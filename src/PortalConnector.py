import firebase_admin
from firebase_admin import credentials , firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from pydantic import BaseModel
import uuid
from fastapi import HTTPException
from passlib.hash import bcrypt

cred = credentials.Certificate("src\secrets\equinox-2025-firebase-adminsdk-fbsvc-512587e6eb.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

class Event(BaseModel):
	event_id:str = ""
	club_name :str
	event_name :str
	description :str
	rules :list[str]
	num_teams:int
	num_participants:int
	timings:str
	venue:str
	event_type:str
	contact_no:str
	fees:int

class RegistrationRequest(BaseModel):
	registration_id:str = ""
	club_name:str
	event_name:str
	type:str

class participant(BaseModel):
	name:str
	phone_no:str
	email_id:str

class participant_institution(BaseModel):
	name:str
	reg_no:str
	phone_no:str
	email_id:str
class Team(BaseModel):
	participants:list[participant]

class Team_institution(BaseModel):
	participants:list[participant_institution]
class InstitutionDelegate(BaseModel):
	institution_name:str
	delegate_head:str
	delegate_phone_no:str
	delegate_email_id:str
	teams:list[Team_institution]

class IndividualDelegate(BaseModel):
	team_name:str
	participants:list[participant]

def get_all_events():
	events_dict = {}
	events_ref = db.collection_group("events").stream()
	for event in events_ref:
		path_parts = event.reference.path.split("/")
		club_name = path_parts[1]
		event_id = path_parts[3]

		if club_name not in events_dict:
			events_dict[club_name] = {}
		
		events_dict[club_name][event_id] = event.to_dict()
	
	print(events_dict)
	return events_dict

def get_user_id_by_name(user_name:str)->str:
	events_ref = db.collection("users")
	query = events_ref.where(filter=FieldFilter("login_id", "==",user_name)).limit(1).stream()

	for doc in query:
		return doc.id
	return ""

def get_user(user_id:str)->bool:
	user_uid = get_user_id_by_name(user_name=user_id)
	if user_uid == "":
		return False
	doc_ref = db.collection("users").document(user_uid)
	doc = doc_ref.get()
	return doc.exists

def try_login(user_id:str,password:str)->bool:
	user_uid = get_user_id_by_name(user_name=user_id)
	if user_uid == "":
		return False
	check_ref = db.collection("users").document(user_uid)
	check = check_ref.get()
	if check.exists == False:
		return False
	data = check.to_dict()
	return bcrypt.verify(password, data["password"])

def get_club_from_user_id(user_id:str)->str:
	user_uid = get_user_id_by_name(user_name=user_id)
	if user_uid == "":
		return ""
	check_ref = db.collection("users").document(user_uid)
	check = check_ref.get()
	if check.exists == False:
		return False
	data = check.to_dict()
	return data["club_name"]

def create_user(user_id:str,email_id:str,password:str,club_name:str,login_uid:str="")->None:
	hashed_pw = bcrypt.hash(password)
	user_uid :str= str(uuid.uuid4()) if login_uid == "" else login_uid
	doc_ref = db.collection("users").document(user_uid)
	doc_ref.set({
		"login_id":user_id,
		"email_id":email_id,
		"password":hashed_pw,
		"club_name":club_name,
		"role":"Bearer"
	})

def update_user(user_id:str,email_id:str,club_name:str,login_uid:str,password:str="")->None:
	user_uid :str= str(uuid.uuid4()) if login_uid == "" else login_uid
	doc_ref = db.collection("users").document(user_uid)
	doc_ref.update({
		"login_id":user_id,
		"email_id":email_id,
		"club_name":club_name,
		"role":"Bearer"
	})
	if password != "":
		hashed_pw = bcrypt.hash(password)
		doc_ref.update({
		"password":hashed_pw,
	})


def get_user_details(user_id:str)->dict:
	check_ref = db.collection("users").document(user_id)
	check = check_ref.get()
	if check.exists == False:
		return {}
	data = check.to_dict()
	data["password"] = data["password"]
	return data

def get_all_host_ids()->dict:
	doc_ref = db.collection("users")
	docs = doc_ref.stream()
	return {doc.id:doc.to_dict()["login_id"] for doc in docs}

def event_exsists(club_name:str,event_name:str)->bool:
	doc_ref = db.collection("club_events").document(club_name).collection("events").document(event_name)
	doc = doc_ref.get()
	return doc.exists

def get_event_id_by_name(club_id:str,event_name:str)->str:
	events_ref = db.collection("club_events").document(club_id).collection("events")
	query = events_ref.where(filter=FieldFilter("event_name", "==",event_name)).limit(1).stream()

	for doc in query:
		return doc.id
	return ""

def create_event(event:Event)->None:
	
	event_id:str = str(uuid.uuid4()) if event.event_id == "" else event.event_id
	doc_ref = db.collection("club_events").document(event.club_name).collection("events").document(event_id)
	doc_ref.set({
		"event_name":event.event_name,
		"description":event.description,
		"rules":event.rules,
		"num_teams":event.num_teams,
		"num_participants":event.num_participants,
		"timings":event.timings,
		"venue":event.venue,
		"event_type":event.event_type,
		"contact_no":event.contact_no,
		"fees":event.fees,
	})

def get_event(club_name:str,event_id:str)->dict:
	if not event_exsists(club_name=club_name,event_name=event_id):
		return {}
	doc_ref = db.collection("club_events").document(club_name).collection("events").document(event_id)
	doc = doc_ref.get()
	data = doc.to_dict()
	data["event_id"] = doc.id
	return data

def get_club_events_size(club_name:str)->int:
	doc_ref = db.collection("club_events").document(club_name).collection("events")
	count_query = doc_ref.count()
	count_result = count_query.get()
	print("something is calling this event")
	return int(count_result[0][0].value)

def get_all_event_by_club(club_name:str)->dict:
	doc_ref = db.collection("club_events").document(club_name).collection("events")
	docs = doc_ref.stream()
	return {doc.id:doc.to_dict()["event_name"] for doc in docs}

def get_all_clubs()->list[str]:
	doc_ref = db.collection("club_events")
	docs = doc_ref.stream()
	return [doc.id for doc in docs]

def create_individual_registration(request:RegistrationRequest,registration_list:IndividualDelegate)->str:
	registration_id = str(uuid.uuid4()) if request.registration_id == "" else request.registration_id
	event_id = get_event_id_by_name(request.club_name,request.event_name)
	if event_id == "":
		raise HTTPException(
			status_code=404,
			detail=f"Event not found {request.event_name}"
		)
	data_ref = doc_ref = (
		db.collection("registrations")
		.document("individual")
		.collection("clubs")
		.document(request.club_name)
		.collection("events")
		.document(event_id)
	)
	data_ref.set({
		"event_name":request.event_name
	})
	doc_ref = data_ref.collection("registrations").document(registration_id)
	participants_data = [p.model_dump() for p in registration_list.participants]

	doc_ref.set({
		"team_name":registration_list.team_name,
		"participants":participants_data,
	})

	return registration_id

def create_institution_registration(request:RegistrationRequest,registration_list:InstitutionDelegate)->str:
	registration_id = str(uuid.uuid4()) if request.registration_id == "" else request.registration_id
	event_id = get_event_id_by_name(request.club_name,request.event_name)
	if event_id == "":
		raise HTTPException(
			status_code=404,
			detail=f"Event not found {request.event_name}"
		)
	
	all_reg_no = []
	for team in registration_list.teams:
		for participant in team.participants:
			if isinstance(participant, participant_institution):
				if participant.reg_no in all_reg_no:
					raise HTTPException(
						status_code=400,
						detail=f"Duplicate reg_no {participant.reg_no} found within the registration for {request.event_name}"
					)
				all_reg_no.append(participant.reg_no)

	data_ref = doc_ref = (
		db.collection("registrations")
		.document("institution")
		.collection("clubs")
		.document(request.club_name)
		.collection("events")
		.document(event_id)
	)
	data_ref.set({
		"event_name":request.event_name
	})
	doc_ref = data_ref.collection("registrations").document(registration_id)
	teams_data = []
	for team in registration_list.teams:
		team_dict = {
			"participants":[p.model_dump() for p in team.participants]
		}
		teams_data.append(team_dict)

	doc_ref.set({
		"institution_name":registration_list.institution_name,
		"delegate_head":registration_list.delegate_head,
		"delegate_phone_no":registration_list.delegate_phone_no,
		"delegate_email_id":registration_list.delegate_email_id,
		"teams":teams_data
	})

	return registration_id

def create_registration(request:RegistrationRequest,registration_list)->str:
	if request.type == "individual":
		reg_id = create_individual_registration(request,registration_list)
	elif request.type == "institution":
		reg_id = create_institution_registration(request,registration_list)
	return reg_id

def get_all_registrations(reg_type:str,club_name:str,event_name:str)->list[dict]:
	event_id = get_event_id_by_name(club_name,event_name)
	if event_id == "":
		return
	doc_ref = (
		db.collection("registrations")
		.document(reg_type)
		.collection("clubs")
		.document(club_name)
		.collection("events")
		.document(event_id)
		.collection("registrations")
		.stream()
	)

	registrations = []
	for doc in doc_ref:
		data = doc.to_dict()
		data["registration_id"] = doc.id
		data["event_name"] = event_name
		registrations.append(data)
		return(registrations)


get_all_events()
