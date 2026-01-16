
import os
import uuid
from datetime import datetime
from typing import Optional


from dotenv import load_dotenv
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


load_dotenv()


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "smart_city_db")
DB_DRIVER = os.getenv("DB_DRIVER", "pymysql")


DATABASE_URL = f"mysql+{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


def generate_uuid() -> str:

    return str(uuid.uuid4())


class Users(Base):
   
    __tablename__ = "users"
    

    id = Column(String(36), primary_key=True, default=generate_uuid)
    

    email = Column(String(255), nullable=True, unique=True, index=True)
    name = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    designation = Column(String(255), nullable=True)
    mpin = Column(String(10), nullable=True)
    
   
    otp = Column(String(6), nullable=True)
    otp_created_at = Column(DateTime, nullable=True)
    
  
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExcelUploads(Base):
   
    __tablename__ = "excel_uploads"
    
  
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
   
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    
 
    filename = Column(String(500), nullable=False)
    table_name = Column(String(100), nullable=False, unique=True, index=True)
    columns = Column(JSON, nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


