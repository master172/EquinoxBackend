import firebase_admin
from firebase_admin import credentials , firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from pydantic import BaseModel
import uuid
from fastapi import HTTPException
from passlib.hash import bcrypt
from . import ExcelExporter
import os
import json
from dotenv import load_dotenv

load_dotenv()

service_account_json_string = os.environ.get("FIREBASE_CRED").replace("\\n","\n")

if service_account_json_string:
    # Load the JSON string into a Python dictionary
    service_account_info = json.loads(service_account_json_string) 

    # Create credentials from the dictionary content
    cred = credentials.Certificate(service_account_info) 

    # Initialize the app
    firebase_admin.initialize_app(cred)
else:
    print("Error: FIREBASE_CRED environment variable not set.")

db = firestore.client()
exporter = ExcelExporter.FirestoreExcelExporter(db)

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
	email_id:str = ""
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

class WebsiteIndividualData(BaseModel):
	registration_uid:str
	type: str
	selectedEvent: str
	participants: list
	clubUid:str

class WebsiteInstitutionData(BaseModel):
	registration_uid:str
	type:str
	schoolName:str
	headDelegate:dict
	registrationForms:list

class WinnersData(BaseModel):
	first_place:dict
	second_place:dict
	third_place:dict

def get_all_events():
	events_dict = {}
	events_ref = db.collection_group("events").stream()

	for event in events_ref:
		path_parts = event.reference.path.split("/")  
		# path looks like: club_events/{club_name}/events/{event_id}

		if path_parts[0] == "club_events":  # only keep from club_events root
			club_name = path_parts[1]
			event_id = path_parts[3]

			if club_name not in events_dict:
				events_dict[club_name] = {}

			events_dict[club_name][event_id] = event.to_dict()

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

def get_event_fees(club_name:str,event_id:str):
	event_ref = db.collection("club_events").document(club_name).collection("events").document(event_id)
	event = event_ref.get()
	if event.exists:
		fees :int = int(event.get("fees"))
		print(f"fees of the event {event_id} under {club_name} is {fees}")
		return fees

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
	club_list:list = []
	events_ref = db.collection_group("events").stream()
	for event in events_ref:
		path_parts = event.reference.path.split("/")
		if path_parts[0] != "club_events":
			continue

		
		club_name = path_parts[1]
		if club_name not in club_list:
			club_list.append(club_name)
	return club_list

"""this is the scary function, it deletes any registration with a given uid
this is done to ensure that when the user updates a registration all previous
reigstrations of that uid are delted"""
def delete_registration(registration_id: str):
	batch = db.batch()
	docs = db.collection_group("registrations").stream()

	found = False
	for doc in docs:
		if doc.id == registration_id:
			batch.delete(doc.reference)
			print(f"Queued delete: {doc.reference.path}")
			found = True
	
	if found:
		batch.commit()
		print(f"Deleted all registrations with id {registration_id}")
	else:
		print("No such registration found.")

def create_individual_registration(request:RegistrationRequest,registration_list:IndividualDelegate)->str:
	registration_id = str(uuid.uuid4()) if request.registration_id == "" else request.registration_id
	event_id = request.event_name
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

	event_ref = db.collection("club_events").document(request.club_name).collection("events").document(request.event_name)
	event = event_ref.get()
	event_name = ""
	if event.exists:
		data = event.to_dict()
		event_name = data["event_name"]

	data_ref.set({
		"event_name":event_name
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
	event_id = request.event_name
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
	event_ref = db.collection("club_events").document(request.club_name).collection("events").document(request.event_name)
	event = event_ref.get()
	event_name = ""
	if event.exists:
		data = event.to_dict()
		event_name = data["event_name"]
		
	data_ref.set({
		"event_name":event_name
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

def get_club_name_by_event(event_name:str)->str:
	club_events_ref = db.collection("club_events")

	clubs = club_events_ref.list_documents()

	for club_ref in clubs:
		club_name = club_ref.id
		
		events_ref = club_ref.collection("events")
		query = events_ref.where(filter=FieldFilter("event_name", "==", event_name)).limit(1)
		events = query.stream()

		for _ in events:
			return club_name
		
	return None

def create_individual_style_references(data:WebsiteIndividualData):
	doc_ref = db.collection("individual_style_reference").document(data.registration_uid)
	doc_ref.set({
		"type":data.type,
		"selectedEvent":data.selectedEvent,
		"participants":data.participants
	})

def create_institution_style_references(data:WebsiteInstitutionData):
	doc_ref = db.collection("institution_style_reference").document(data.registration_uid)
	doc_ref.set({
		"type":data.type,
		"schoolName":data.schoolName,
		"headDelegate":data.headDelegate,
		"registrationForms":data.registrationForms
	})

def get_registration_exists(registration_uid:str)->dict:
	doc_ref = db.collection("individual_style_reference").document(registration_uid)
	doc = doc_ref.get()
	if doc.exists:
		return doc.to_dict()
	doc_ref = db.collection("institution_style_reference").document(registration_uid)
	doc = doc_ref.get()
	if doc.exists:
		return doc.to_dict()
	return {}

def export_all_registrations():
	exporter.export_all_events()

def scrutinize_registrations():
	exporter.scrutinize_all_events_to_excel()

def create_fees_databse_by_uid(uid:str,amount:int):
	fees_ref = db.collection("fees").document(uid)
	fees_ref.set(
		{
			"fees":amount
		}
	)
	print(f"set registration fees of {uid} to {amount}")

def get_fees_by_registration_uid(uid:str):
	fees_ref = db.collection("fees").document(uid)
	fees = fees_ref.get()
	if fees.exists:
		data = fees.get("fees")
		print(f"fees under uid {uid} is {data}")
		return data

def create_winners_data(club_name:str,event_id:str,data:WinnersData)->bool:
	winners_ref = db.collection("winners").document(club_name).collection("events").document(event_id)
	winners_ref.set(data.model_dump())
	return True

def get_winners_data(club_name:str,event_id:str):
	winners_ref = db.collection("winners").document(club_name).collection("events").document(event_id)
	winners = winners_ref.get()
	if winners.exists:
		return winners.to_dict()
	else:
		raise HTTPException(status_code=404)