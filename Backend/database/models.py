"""
Database models and connection setup for FastAPI application.

This module contains:
- Database connection configuration using environment variables
- SQLAlchemy Base and SessionLocal setup
- Database models (Users, etc.)
"""

# Standard library imports
import os
import uuid
from datetime import datetime
from typing import Optional

# Third-party imports
from dotenv import load_dotenv
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Load environment variables
load_dotenv()

# Database configuration from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "smart_city_db")
DB_DRIVER = os.getenv("DB_DRIVER", "pymysql")

# Construct database URL
DATABASE_URL = f"mysql+{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


def generate_uuid() -> str:
    """Generate UUID string for primary keys."""
    return str(uuid.uuid4())


class Users(Base):
    """
    Users table model.
    
    Contains user information including email, OTP, name, department,
    designation, mpin, and timestamps.
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # User information columns
    email = Column(String(255), nullable=True, unique=True, index=True)
    name = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    designation = Column(String(255), nullable=True)
    mpin = Column(String(10), nullable=True)
    
    # OTP columns
    otp = Column(String(6), nullable=True)
    otp_created_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExcelUploads(Base):
    """
    Excel uploads table model.
    
    Tracks metadata about uploaded Excel files including filename,
    table name, columns, row count, and user association.
    """
    __tablename__ = "excel_uploads"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # User association
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    
    # File information
    filename = Column(String(500), nullable=False)
    table_name = Column(String(100), nullable=False, unique=True, index=True)
    columns = Column(JSON, nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


