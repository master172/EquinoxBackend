from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from . import PortalConnector

app = FastAPI()

class ClubRequest(BaseModel):
	user_id:str
class LoginRequest(BaseModel):
	login_id:str
	password:str

class CreateUserRequest(BaseModel):
	login_id:str
	password:str
	club_name:str
	email_id:str

@app.get("/user")
def get_user(login_creds:LoginRequest)->bool:
	user_exists = PortalConnector.try_login(login_creds.login_id,login_creds.password)
	return user_exists

@app.post("/create")
def create_user(login_creds:CreateUserRequest):
	PortalConnector.create_user(login_creds.login_id,login_creds.email_id,login_creds.password,login_creds.club_name)

@app.get("/club")
def get_club_from_user(request:ClubRequest)->str:
	club = PortalConnector.get_club_from_user_id(request.user_id)
	return club if club else ""

@app.get("/hosts")
def get_club_from_user()->list[str]:
	return PortalConnector.get_all_host_ids()

@app.get("/host")
def get_club_from_user(request:ClubRequest)->dict:
	return PortalConnector.get_user_details(request.user_id)