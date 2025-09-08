from fastapi import *

app = FastAPI()
items = []

class Item():
	item:str

@app.get("/")
def root():
	return {"Hello":"World"}

@app.get("/names")
def root():
	return ["C.S club","AICUF"]

@app.post("/items")
def create_item(item:str = Body(..., embed=False)):
	print(item)
	return item

@app.post("/json")
def print_json(content:dict = Body(..., embed=False)):
	print(content)
	return content