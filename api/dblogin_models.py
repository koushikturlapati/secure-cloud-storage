from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str

class Createaccount(BaseModel):
    username: str
    password: str
    confirmpassword:str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


