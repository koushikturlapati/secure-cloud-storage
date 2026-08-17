from fastapi import FASTAPI, FastAPI
import pydantic
from pydantic import Basemodel

app = FastAPI()

class LoginModel(pydantic.BaseModel):
    username: str
    password: str
@app.post("/login")
def login(user: LoginRequest):
   print("Username recived:", user.username)   
   return {
       "success": True,
       "message": "Request received"
   }