from fastapi import FASTAPI, FastAPI
from pydantic import Basemodel
from api.dblogin_models import loginModel


app = FastAPI()


@app.post("/login")
def login(user: loginRequest):
   print("Username recived:", user.username)   
   return {
       "success": True,
   }
