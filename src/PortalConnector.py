import firebase_admin
from firebase_admin import credentials , firestore
from pydantic import BaseModel
import uuid

cred = credentials.Certificate("src\secrets\equinox-2025-firebase-adminsdk-fbsvc-512587e6eb.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

class Event(BaseModel):
	club_name :str
	event_id:str
	event_name :str
	description :str
	rules :list[str]
	num_teams:int
	num_participants:int
	timings:str
	contact_no:str
	fees:int

class RegistrationRequest(BaseModel):
	club_name:str
	event_name:str
	type:str
class participant(BaseModel):
	name:str
	phone_no:str
	email_id:str
class Team(BaseModel):
	participants:list[participant]
class InstitutionDelegate(BaseModel):
	institution_name:str
	delegate_head:str
	delegate_phone_no:str
	delegate_email_id:str
	teams:list[Team]

class IndividualDelegate(BaseModel):
	team_name:str
	participants:list[participant]

def get_user(user_id:str)->bool:
	doc_ref = db.collection("users").document(user_id)
	doc = doc_ref.get()
	return doc.exists

def try_login(user_id:str,password:str)->bool:
	if not get_user(user_id=user_id):
		return False
	doc_ref = db.collection("users").document(user_id)
	doc = doc_ref.get()
	data = doc.to_dict()
	if user_id == data["login_id"] and password == data["password"]:
		return True
	return False

def get_club_from_user_id(user_id:str)->str:
	if not get_user(user_id=user_id):
		return ""
	doc_ref = db.collection("users").document(user_id)
	doc = doc_ref.get()
	data = doc.to_dict()
	return data["club_name"]

def create_user(user_id:str,email_id:str,password:str,club_name:str)->None:
	doc_ref = db.collection("users").document(user_id)
	doc_ref.set({
		"login_id":user_id,
		"email_id":email_id,
		"password":password,
		"club_name":club_name
	})

def get_user_details(user_id:str)->dict:
	if not get_user(user_id=user_id):
		return {}
	doc_ref = db.collection("users").document(user_id)
	doc = doc_ref.get()
	data = doc.to_dict()
	return data

def get_all_host_ids()->list[str]:
	doc_ref = db.collection("users")
	docs = doc_ref.stream()
	return [doc.id for doc in docs]

def event_exsists(club_name:str,event_name:str)->bool:
	doc_ref = db.collection("club_events").document(club_name).collection("events").document(event_name)
	doc = doc_ref.get()
	return doc.exists

def create_event(event:Event)->None:
	doc_ref = db.collection("club_events").document(event.club_name).collection("events").document(event.event_id)
	db.collection("club_events").document(event.club_name).set({
		"club_name":event.club_name
	})
	doc_ref.set({
		"event_name":event.event_name,
		"description":event.description,
		"rules":event.rules,
		"num_teams":event.num_teams,
		"num_participants":event.num_participants,
		"timings":event.timings,
		"contact_no":event.contact_no,
		"fees":event.fees,
	})

def get_event(club_name:str,event_name:str)->dict:
	if not event_exsists(club_name=club_name,event_name=event_name):
		return {}
	doc_ref = db.collection("club_events").document(club_name).collection("events").document(event_name)
	doc = doc_ref.get()
	data = doc.to_dict()
	return data

def get_club_events_size(club_name:str)->int:
	doc_ref = db.collection("club_events").document(club_name).collection("events")
	count_query = doc_ref.count()
	count_result = count_query.get()
	return int(count_result[0][0].value)

def get_all_event_by_club(club_name:str)->dict:
	doc_ref = db.collection("club_events").document(club_name).collection("events")
	docs = doc_ref.stream()
	return {doc.id:doc.to_dict()["event_name"] for doc in docs}

def get_all_clubs()->list[str]:
	doc_ref = db.collection("club_events")
	docs = doc_ref.stream()
	return [doc.id for doc in docs]

def create_individual_registration(request:RegistrationRequest,registration_list:IndividualDelegate)->None:
	registration_id = str(uuid.uuid4())
	doc_ref = (
		db.collection("registrations")
		.document("individual")
		.collection("clubs")
		.document(request.club_name)
		.collection("events")
		.document(request.event_name)
		.collection("registrations")
		.document(registration_id)
	)

	participants_data = [p.model_dump() for p in registration_list.participants]

	doc_ref.set({
		"team_name":registration_list.team_name,
		"participants":participants_data,
	})

def create_institution_registration(request:RegistrationRequest,registration_list:InstitutionDelegate)->None:
	registration_id = str(uuid.uuid4())
	doc_ref = (
		db.collection("registrations")
		.document("institution")
		.collection("clubs")
		.document(request.club_name)
		.collection("events")
		.document(request.event_name)
		.collection("registrations")
		.document(registration_id)
	)
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

def create_registration(request:RegistrationRequest,registration_list)->None:
	if request.type == "individual":
		create_individual_registration(request,registration_list)
	elif request.type == "institution":
		create_institution_registration(request,registration_list)

def get_all_registrations(reg_type:str,club_name:str,event_name:str)->list[dict]:
	doc_ref = (
		db.collection("registrations")
		.document(reg_type)
		.collection("clubs")
		.document(club_name)
		.collection("events")
		.document(event_name)
		.collection("registrations")
		.stream()
	)

	registrations = []
	for doc in doc_ref:
		data = doc.to_dict()
		data["registration_id"] = doc.id
		registrations.append(data)
		return(registrations)