from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel

app = FastAPI()
items = ["apple","orange","porridge"]

class Item(BaseModel):
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

@app.get("/items/{item_index}")
def get_item_by_id(item_index:int)->str:
	if item_index < len(items):
		item = items[item_index]
	else:
		raise HTTPException(status_code=404,detail="Item not found")

@app.post("/json")
def print_json(content:Item = Body(..., embed=False)):
	print(content)
	return content