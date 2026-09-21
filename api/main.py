import os
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from backend.database import get_db
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.models import User, StoredFile, Folders, FilePermission, RefreshToken 
from api.dblogin_models import (
    Createaccount,
    FolderRequest,
    LoginRequest,
    RefreshRequest,
    RenameFileRequest,
    ShareRequest,
    Token,
)
from crypto.aes_crypto import decrypt_data, encrypt_data

load_dotenv()
secret_key_file = Path(__file__).resolve().parents[1] / "secret.key"
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY and secret_key_file.is_file():
    SECRET_KEY = secret_key_file.read_text(encoding="utf-8").strip()
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


app = FastAPI()


STORAGE_DIR = Path(__file__).resolve().parents[1] / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

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


def create_refresh_token(user_id: int, db: Session) -> str:
    if not hasattr(db, "add") or not hasattr(db, "commit"):
        return None
    raw_token = secrets.token_urlsafe(32)
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_token)
    db.commit()
    return raw_token


def refresh_token_record(raw_token: str, db: Session) -> RefreshToken | None:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked.is_(False),
    ).first()
    if record is None or record.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        return None
    return record


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


def get_accessible_file(file_id: int, current_user: User, db: Session) -> StoredFile:
    file = db.query(StoredFile).filter(StoredFile.id == file_id).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    if file.user_id == current_user.id:
        return file
    permission = db.query(FilePermission).filter(
        FilePermission.file_id == file.id,
        FilePermission.user_id == current_user.id,
    ).first()
    if permission is None:
        raise HTTPException(status_code=403, detail="You do not have access to this file")
    return file

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
        "refresh_token": create_refresh_token(db_user.id, db),
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
    return Token(
        access_token=create_access_token(user.username),
        refresh_token=create_refresh_token(user.id, db),
    )


@app.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}


@app.post("/files/upload")
async def upload_file(
    file: UploadFile =File(...), # uploading the file 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename: #if file not found
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is requried"
        )
    # genearting unique file name and giving the  file a path to stay
    file_extension = Path(file.filename).suffix
    storage_name = f"{uuid.uuid4()}{file_extension}"
    file_path = STORAGE_DIR / storage_name

    # reading the file
    file_data = await file.read()

    with open(file_path, "wb") as buffer:
        buffer.write(encrypt_data(file_data))


    #calcutaing the SHA 256 of the file
    sha256_hash = hashlib.sha256(file_data).hexdigest()

    #adding the file to database record
    new_file = StoredFile(
        user_id=current_user.id,
        filename=file.filename,
        storage_name =storage_name,
        content_type =file.content_type,
        sha256=sha256_hash 
    )


    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return{
    "success": True,
    "message": "File uploaded successfully", 
    "file_id": new_file.id, 
    "filename": new_file.filename,
    "size": len(file_data),
    "content_type": new_file.content_type,
    }

@app.get("/files/")
def list_files(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    owned_files = db.query(StoredFile).filter(StoredFile.user_id == current_user.id).all()
    shared_files = db.query(StoredFile).join(
        FilePermission, FilePermission.file_id == StoredFile.id
    ).filter(FilePermission.user_id == current_user.id).all()
    files = {file.id: file for file in owned_files + shared_files}
    result = []
    for file in files.values():
        file_path = STORAGE_DIR / file.storage_name
        size = 0
        if file_path.is_file():
            size = len(decrypt_data(file_path.read_bytes()))
        result.append({
            "id": file.id,
            "name": file.filename,
            "filename": file.filename,
            "size": size,
            "content_type": file.content_type,
            "security": "Encrypted",
            "owner_id": file.user_id,
        })
    return result

@app.get("/files/{file_id}")
def download_files(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file = get_accessible_file(file_id, current_user, db)
    file_path = STORAGE_DIR / file.storage_name
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File data not found")
    return Response(
        content=decrypt_data(file_path.read_bytes()),
        media_type=file.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
    )

@app.delete("/files/{file_id}")
def delete_files(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file = db.query(StoredFile).filter(
        StoredFile.id == file_id,
        StoredFile.user_id == current_user.id,
    ).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    file_path = STORAGE_DIR / file.storage_name
    if file_path.is_file():
        file_path.unlink()
    db.query(FilePermission).filter(FilePermission.file_id == file.id).delete()
    db.delete(file)
    db.commit()
    return {"success": True}


@app.patch("/files/{file_id}")
def rename_file(file_id: int, request: RenameFileRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    filename = request.filename.strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    file = db.query(StoredFile).filter(
        StoredFile.id == file_id,
        StoredFile.user_id == current_user.id,
    ).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    file.filename = filename
    db.commit()
    return {"success": True, "filename": filename}

@app.post("/folders")
def create_folder(request: FolderRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    folder_name = request.folder_name.strip()
    if not folder_name:
        raise HTTPException(status_code=400, detail="Folder name is required")
    if request.parent_folder_id is not None:
        parent = db.query(Folders).filter(
            Folders.id == request.parent_folder_id,
            Folders.user_id == current_user.id,
        ).first()
        if parent is None:
            raise HTTPException(status_code=404, detail="Parent folder not found")
    folder = Folders(
        user_id=current_user.id,
        parent_folder_id=request.parent_folder_id,
        folder_name=folder_name,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return {"id": folder.id, "folder_name": folder.folder_name, "parent_folder_id": folder.parent_folder_id}

@app.get("/folders")
def list_folder(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    folders = db.query(Folders).filter(Folders.user_id == current_user.id).all()
    return [{"id": folder.id, "folder_name": folder.folder_name, "parent_folder_id": folder.parent_folder_id} for folder in folders]

@app.delete("/folders/{folder_id}")
def delete_folder(folder_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    folder = db.query(Folders).filter(Folders.id == folder_id, Folders.user_id == current_user.id).first()
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    if db.query(Folders).filter(Folders.parent_folder_id == folder.id).first():
        raise HTTPException(status_code=409, detail="Folder contains subfolders")
    db.delete(folder)
    db.commit()
    return {"success": True}

@app.post("/files/{file_id}/share")
def share_file(file_id: int, request: ShareRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file = db.query(StoredFile).filter(StoredFile.id == file_id, StoredFile.user_id == current_user.id).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    target_user = db.query(User).filter(User.username == request.username.strip()).first()
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You already own this file")
    permission = db.query(FilePermission).filter(
        FilePermission.file_id == file.id,
        FilePermission.user_id == target_user.id,
    ).first()
    if permission is None:
        permission = FilePermission(file_id=file.id, user_id=target_user.id, permission=request.permission)
        db.add(permission)
    else:
        permission.permission = request.permission
    db.commit()
    return {"success": True, "username": target_user.username, "permission": request.permission}

@app.get("/files/{file_id}/permissions")
def view_permission(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file = db.query(StoredFile).filter(StoredFile.id == file_id, StoredFile.user_id == current_user.id).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    permissions = db.query(FilePermission, User).join(User, User.id == FilePermission.user_id).filter(FilePermission.file_id == file.id).all()
    return [{"user_id": user.id, "username": user.username, "permission": permission.permission} for permission, user in permissions]

@app.delete("/files/{file_id}/share/{user_id}")
def remove_permisssion(file_id: int, user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file = db.query(StoredFile).filter(StoredFile.id == file_id, StoredFile.user_id == current_user.id).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    permission = db.query(FilePermission).filter(FilePermission.file_id == file.id, FilePermission.user_id == user_id).first()
    if permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    db.delete(permission)
    db.commit()
    return {"success": True}

@app.post("/refresh")
def new_access_token(request: RefreshRequest, db: Session = Depends(get_db)):
    record = refresh_token_record(request.refresh_token, db)
    if record is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = db.query(User).filter(User.id == record.user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return Token(access_token=create_access_token(user.username))

@app.post("/logout")
def logout(request: RefreshRequest, db: Session = Depends(get_db)):
    record = refresh_token_record(request.refresh_token, db)
    if record is not None:
        record.revoked = True
        db.commit()
    return {"success": True}



#shows where my frontend exits
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
