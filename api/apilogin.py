import bcrypt
from fastapi import Depends, FastAPI
from backend.database import get_db
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
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

# JWT



@app.post("/createacc")
def createacc(
    user: Createaccount,
    db: Session = Depends(get_db)
):
    username = user.username.strip()

    if not username:
        return {
            "success": False,
            "message": "Username is required"
        }

    if user.password != user.confirmpassword:
        return {
            "success": False,
            "message": "Passwords do not match"
        }

    existing_user = db.query(User).filter(User.username == username).first()

    if existing_user:
        return {
            "success": False,
            "message": "Username already exists"
        }

    password_bytes = user.password.encode("utf-8")
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

    new_user = User(
        username=username,
        password_hash=password_hash
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        return {
            "success": False,
            "message": "Username already exists"
        }

    return {
        "success": True,
        "message": "Account created"
    }

@app.post("/login")
def login(
    user: LoginRequest,
    db: Session = Depends(get_db)
):
    username = user.username.strip()
    db_user = db.query(User).filter(User.username == username).first()

    if db_user and bcrypt.checkpw(
        user.password.encode("utf-8"), db_user.password_hash.encode("utf-8")
    ):
        return {
            "success": True,
            "message": "Login successful"
        }
    return {
        "success": False,
        "message": "Invalid username or password"
    }

