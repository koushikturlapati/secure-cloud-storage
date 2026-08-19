from fastapi import FastAPI, Depends
from backend.database import get_db
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.models import User
from api.dblogin_models import LoginRequest, Createaccount


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/createacc")
def createacc(
    user: Createaccount,
    db: Session = Depends(get_db)
):
    if user.password != user.confirmpassword:
        return {
        "success": False,
        "message": "Passwords do not match"
    }

    new_user = User(
    username=user.username,
    password_hash=user.password
    )


    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created"
    }

@app.post("/login")
def login(
    user: LoginRequest,
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.username == user.username).first()


    if db_user:
        print("User found:", db_user.username) 
        return {
            "success": True,
            "message": "Login successfull"
        
        }
    return{
        "succes": False,
        "message": "User not found"
    }

