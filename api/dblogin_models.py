from typing import Optional
from pydantic import BaseModel, Field


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
    refresh_token: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class ShareRequest(BaseModel):
    username: str
    permission: str = Field(default="read", pattern="^(read|write)$")


class FolderRequest(BaseModel):
    folder_name: str
    parent_folder_id: Optional[int] = None


class RenameFileRequest(BaseModel):
    filename: str


