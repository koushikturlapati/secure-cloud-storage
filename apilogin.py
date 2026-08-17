from fastapi import FASTAPI, FastAPI
import pydantic
from pydantic import Basemodel

 app = FastAPI()

class LoginModel(pydantic.BaseModel):
    username: str
    password: str