from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from . import PortalConnector
from datetime import datetime
app = FastAPI()

FIXED_DATETIME = datetime(2025, 9, 10, 18, 0, 0)

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