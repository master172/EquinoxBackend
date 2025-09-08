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
	print(request.user_id)
	club = PortalConnector.get_club_from_user_id(request.user_id)
	print(club)
	return club if club else ""