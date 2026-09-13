import os
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from backend.database import get_db
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.models import User, StoredFile, Folders, FilePermission, RefreshToken 
from api.dblogin_models import Createaccount, LoginRequest, Token



load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


app = FastAPI()


STORAGE_DIR = Path(__file__).resolve().parents[1] / "storage"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # This API uses Bearer tokens, not cookies.  Credentials cannot safely be
    # combined with a wildcard origin in browsers.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise credentials_exception
    return user


def authenticate_user(username: str, password: str, db: Session) -> User | None:
    user = db.query(User).filter(User.username == username.strip()).first()
    if user is None or not bcrypt.checkpw(
        password.encode("utf-8"), user.password_hash.encode("utf-8")
    ):
        return None
    return user

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
    db_user = authenticate_user(user.username, user.password, db)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "success": True,
        "message": "Login successful",
        "access_token": create_access_token(db_user.username),
        "token_type": "bearer",
    }


@app.post("/token", response_model=Token)
def issue_oauth_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 password-flow endpoint used by the OpenAPI Authorize dialog."""
    user = authenticate_user(form_data.username, form_data.password, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.username))


@app.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}


@app.post("/files/upload")
def upload_file():

@app.get("/files/")
def list_files():

@app.get("/files/{file_id}")
def download_files():



@app.delete("/files/{file_id}")
def delete_files():


@app.post("/folders")
def create_folder():

@app.get("/folders")
def list_folder():

@app.delete("/folders/{folder_id}")
def delete_folder():

@app.post("/files/{file_id}/share")
def share_file():


@app.get("/files/{file_id}/permissions")
def view_permission():


@app.delete("/files/{file_id}/share/{user_id}")
def remove_permisssion():

@app.post("/refresh")
def new_access_token():


@app.post("/logout")
def ():

#shows where my frontend exits
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")