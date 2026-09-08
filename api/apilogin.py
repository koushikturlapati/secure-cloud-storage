import os
from datetime import datetime, timedelata, timezone
import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI,HTTPException, status
from backend.database import get_db
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.models import User
from api.dblogin_models import LoginRequest, Createaccount



load_dotenv()
SECRECT_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")    


def  create_access_token(username:str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": username,
        "exp": expire
    }

    token = jwt.encode(payload,SECRET_KEY, algorithm=ALGORITHM)
    

 
def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    credentails_exception = HTTPException
    (
        status_code=status.HTTP_401UNAUTHORIZED,
     detail="Could not validate credentials",
     headers={"WWW-Authenticate", "Bearer"}

    )
    try:
        payload = jwt.decode(
            token,
            SECERET_KEY,
            algorithms=[ALGORITHM]
        )
        username =payload.get("sub")
        if username is None:
            raise credential_exeception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )   
    except jwt.InvalidTokenError:
        raise credntials_exception
    user = (
        db.query(User.filter(User.username == username).first())
    )

    if user is None:
        raise credtenials_exception
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

