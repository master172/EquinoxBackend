from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from . import PortalConnector
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
import json, uuid

FIXED_DATETIME = datetime(2025, 9, 10, 18, 0, 0)

origins = [
    "http://localhost:5173",  # your React dev server
    "http://127.0.0.1:5173",
    # add production domain later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ClubRequest(BaseModel):
	user_id:str

class EventsRequest(BaseModel):
	club_name:str
class LoginRequest(BaseModel):
	login_id:str
	password:str

class CreateUserRequest(BaseModel):
	user_uid:str=""
	login_id:str
	password:str
	club_name:str
	email_id:str

class EventRequest(BaseModel):
	club_name:str
	event_name:str

class UserUpdateRequest(BaseModel):
	user_uid:str=""
	login_id:str
	password:str=""
	club_name:str
	email_id:str

class WebsiteIndividualData(BaseModel):
    type: str
    selectedEvent: str
    participants: list


@app.get("/check_time")
def check_time():
    now = datetime.now()
    return now > FIXED_DATETIME

@app.get("/user")
def get_user(login_creds:LoginRequest)->bool:
	user_exists = PortalConnector.try_login(login_creds.login_id,login_creds.password)
	return user_exists

@app.post("/create")	
def create_user(login_creds:CreateUserRequest):
	PortalConnector.create_user(login_creds.login_id,login_creds.email_id,login_creds.password,login_creds.club_name,login_creds.user_uid)

@app.post("/update_host")	
def create_user(login_creds:CreateUserRequest):
	PortalConnector.update_user(login_creds.login_id,login_creds.email_id,login_creds.club_name,login_creds.user_uid,login_creds.password)


@app.post("/create_event")	
def create_user(event:PortalConnector.Event):
	PortalConnector.create_event(event)

@app.get("/event")
def get_event(request:EventRequest)->dict:
	event = PortalConnector.get_event(request.club_name,request.event_name)
	return event

@app.get("/event_size")
def get_event(request:EventsRequest)->int:
	event = PortalConnector.get_club_events_size(request.club_name)
	return event

@app.get("/events")
def get_events(request:EventsRequest)->dict:
	return PortalConnector.get_all_event_by_club(request.club_name)

@app.get("/all_events")
def get_all_events():
	events = PortalConnector.get_all_events()
	return Response(content=json.dumps(events),media_type="application/json")

@app.get("/club")
def get_club_from_user(request:ClubRequest)->str:
	club = PortalConnector.get_club_from_user_id(request.user_id)
	return club if club else ""

@app.get("/clubs")
def get_clubs()->list[str]:
	clubs = PortalConnector.get_all_clubs()
	return clubs

@app.get("/hosts")
def get_club_from_user()->dict:
	return PortalConnector.get_all_host_ids()

@app.get("/host")
def get_club_from_user(request:ClubRequest)->dict:
	return PortalConnector.get_user_details(request.user_id)

@app.post("/registrations/individual/{club_name}/{event_name}")
def api_create_individual_registration(club_name: str, event_name: str, registration: PortalConnector.IndividualDelegate,reg_id:str=""):
    req = PortalConnector.RegistrationRequest(club_name=club_name, event_name=event_name, type="individual",registration_id=reg_id)
    reg_id = PortalConnector.create_individual_registration(req, registration)
    return {"message": "Individual registration created", "registration_id": reg_id}


@app.post("/registrations/institution/{club_name}/{event_name}")
def api_create_institution_registration(club_name: str, event_name: str, registration: PortalConnector.InstitutionDelegate,reg_id:str=""):
    req = PortalConnector.RegistrationRequest(club_name=club_name, event_name=event_name, type="institution",registration_id=reg_id)
    reg_id = PortalConnector.create_institution_registration(req, registration)
    return {"message": "Institution registration created", "registration_id": reg_id}

@app.get("/registrations/{reg_type}/{club_name}/{event_name}")
def api_get_registrations(reg_type: str, club_name: str, event_name: str):
    if reg_type not in ["individual", "institution"]:
        raise HTTPException(status_code=400, detail="Invalid registration type")

    registrations = PortalConnector.get_all_registrations(reg_type, club_name, event_name)

    if not registrations:
        raise HTTPException(status_code=404, detail="No registrations found")

    return {"count": len(registrations), "registrations": registrations}

@app.post("/Web_IdR", response_model=dict)
async def register(data: WebsiteIndividualData):
	found_club_name = PortalConnector.get_club_name_by_event(data.selectedEvent)
	reg_request = PortalConnector.RegistrationRequest(registration_id="",club_name=found_club_name,type="individual",event_name=data.selectedEvent)
	name_team = str(uuid.uuid1())
	registered_participants :list[PortalConnector.participant] = []
	for i in data.participants:
		name = i["name"]
		phone_no = i["phone"]
		email_id = i["reg_no"]
		new_participant = PortalConnector.participant(name=name,phone_no=phone_no,email_id=email_id)
			
		registered_participants.append(new_participant)
	registering_delegate = PortalConnector.IndividualDelegate(team_name=name_team,participants=registered_participants)
	returned_uid = PortalConnector.create_individual_registration(reg_request,registering_delegate)
	return {"uid":returned_uid}
	