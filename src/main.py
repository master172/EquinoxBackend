from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from . import PortalConnector
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import uuid, shutil, os

app = FastAPI()

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

class RegistrationCheckRequest(BaseModel):
	uid:str

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
	return events

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
async def register(data: PortalConnector.WebsiteIndividualData):
	amount_to_be_paid:int = 0
	PortalConnector.delete_registration(data.registration_uid)
	PortalConnector.create_individual_style_references(data=data)
	found_club_name = data.clubUid
	reg_request :PortalConnector.RegistrationRequest = PortalConnector.RegistrationRequest(
		registration_id=data.registration_uid,
		club_name=found_club_name,
		type="individual",
		event_name=data.selectedEvent)
	name_team = str(uuid.uuid1())
	registered_participants :list[PortalConnector.participant] = []
	seen_emails = set()
	seen_phones = set()
	temp_fees:int = PortalConnector.get_event_fees(club_name=found_club_name,event_id=data.selectedEvent)
	for i in data.participants:
		if i["phone"] in seen_phones:
			raise HTTPException(status_code=400,detail={
				"code":"DUPLICATE_PARTICIPANT",
				"message": f"Duplicate participant phone number: {i["phone"]}"
			})
		if i["email"] in seen_emails:
			raise HTTPException(status_code=400,
					   detail={
						   "code":"DUPLICATE_PARTICIPANT",
						   "message": f"Duplicate participant email: {i["email"]}"
					   })
		
		amount_to_be_paid += temp_fees
		print(f"adding fees {temp_fees}")
		seen_emails.add(i["email"])
		seen_phones.add(i["phone"])
		name = i["name"]
		phone_no = i["phone"]
		email_id = i["email"]
		new_participant = PortalConnector.participant(name=name,phone_no=phone_no,email_id=email_id)
			
		registered_participants.append(new_participant)
	registering_delegate = PortalConnector.IndividualDelegate(team_name=name_team,participants=registered_participants)
	returned_uid = PortalConnector.create_individual_registration(reg_request,registering_delegate)
	print(amount_to_be_paid)
	PortalConnector.create_fees_databse_by_uid(uid=returned_uid,amount=amount_to_be_paid)
	return {"uid":returned_uid,"fees":amount_to_be_paid}

@app.post("/Web_InR", response_model=dict)
async def register(data: PortalConnector.WebsiteInstitutionData):
	amount_to_be_paid:int = 0

	PortalConnector.delete_registration(data.registration_uid)
	PortalConnector.create_institution_style_references(data=data)
	institute_name = data.schoolName
	head_name = data.headDelegate["name"]
	head_phone = data.headDelegate["phone"]
	head_email = data.headDelegate["email"]
	seen_reg_no = set()
	for i in data.registrationForms:
		for j in i["teams"]:
			for participant in j["participants"]:
				if participant["reg_no"] in seen_reg_no:
					raise HTTPException(
						status_code=400,
						detail={
							"code":"DUPLICATE_PARTICIPANT",
							"message": f"Duplicate registration number found: {participant["reg_no"]}"
						}
					)
				seen_reg_no.add(participant["reg_no"])

	for registering_events in data.registrationForms:
		club_name = registering_events["club_uid"]
		event_name = registering_events["event_uid"]
		reg_request :PortalConnector.RegistrationRequest = PortalConnector.RegistrationRequest(
			registration_id=data.registration_uid,
			club_name=club_name,
			event_name=event_name,
			type="institution")
		
		registering_teams:list[PortalConnector.Team_institution] = []
		current_team_fees:int = 0
		temp_fees = PortalConnector.get_event_fees(club_name=club_name,event_id=event_name)
		for team in registering_events["teams"]:
			participant_list:list[PortalConnector.participant_institution] = []
			for participant in team["participants"]:
				current_team_fees += temp_fees
				print(f"adding fees {temp_fees}")
				name = participant["name"]
				phone = participant["phone"]
				reg_no = participant["reg_no"]
				email = ""
				new_participant :PortalConnector.participant_institution = PortalConnector.participant_institution(
					name=name,
					reg_no=reg_no,
					phone_no=phone,
					email_id=email)
				participant_list.append(new_participant)
			new_team :PortalConnector.Team_institution = PortalConnector.Team_institution(participants=participant_list)
			registering_teams.append(new_team)
		
		new_institution_delegate :PortalConnector.InstitutionDelegate = PortalConnector.InstitutionDelegate(
			institution_name=institute_name,
			delegate_head=head_name,
			delegate_phone_no=head_phone,
			delegate_email_id=head_email,
			teams=registering_teams)
		
		register_uid = PortalConnector.create_institution_registration(request=reg_request,registration_list=new_institution_delegate)
		amount_to_be_paid += current_team_fees
	print(amount_to_be_paid)
	PortalConnector.create_fees_databse_by_uid(uid=register_uid,amount=amount_to_be_paid)
	return {"uid":register_uid,"fees":amount_to_be_paid}

@app.get("/lookup/{uid}")
def lookup_registration(uid:str)->dict:
	print(uid)
	lookup_results = PortalConnector.get_registration_exists(uid)
	print(lookup_results)
	return lookup_results

@app.get("/export")
def export_registrations():
	PortalConnector.export_all_registrations()

@app.get("/scrutinize")
def export_registrations():
	PortalConnector.scrutinize_registrations()

@app.get("/download")
def export_and_send():
	PortalConnector.export_all_registrations()
	PortalConnector.scrutinize_registrations()
	shutil.make_archive("registrations", 'zip', "exports")
	if not os.path.exists("registrations.zip"):
		raise HTTPException(status_code=404, detail="Export zip not found")
	
	return FileResponse(
		path="registrations.zip",
		filename="registrations.zip",
		media_type='application/zip'
	)