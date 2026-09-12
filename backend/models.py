from sqlalchemy import Boolean, Column, Integer, String, TIMESTAMP
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255),nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class StoredFile(Base):
    __tablename__ = "stored_files"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    storage_name = Column(String(255), unique=True, nullable=False)
    content_type = Column(String(255))
    sha256 = Column(String(64), nullable=False)
    uploaded_at = Column(TIMESTAMP,server_default=func.now())
    
class Folders(Base):
    __tablename__ = "folders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,ForeignKey("users.id"), nullable=False, index=True)
    parent_folder_id = Column(Integer, ForeignKey("folders.id"), index=True)    
    folder_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class FilePermission(Base):
    __tablename__ = "file_permissions"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("stored_files.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    permission = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
