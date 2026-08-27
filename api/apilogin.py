import bcrypt
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
    existing_user = db.query(User).flilter(User.username == user.user).first()

    if existing_user: # checking if the user already exists
        return {
            "success" : False,
            "message" : "User name already exists" 
        }
     # password hashing by bcrypt
    password_bytes = user.password.encode("utf-8")
    password_hash = bcrypt.hashpw(password_bytes,bcrypt.gensalt())

    new_user = User(
    username=user.username,
    password_hash=password_hash.decode("uf-8)")
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
        "success": False,
        "message": "User not found"
    }

