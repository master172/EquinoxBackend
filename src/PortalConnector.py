import firebase_admin
from firebase_admin import credentials , firestore

cred = credentials.Certificate("src\secrets\equinox-2025-firebase-adminsdk-fbsvc-512587e6eb.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

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
		return False
	doc_ref = db.collection("users").document(user_id)
	doc = doc_ref.get()
	data = doc.to_dict()
	return data

def get_all_host_ids()->list[str]:
	doc_ref = db.collection("users")
	docs = doc_ref.stream()
	return [doc.id for doc in docs]