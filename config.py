"""
Configuration settings for Care-Sync Application
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database configuration
DATABASE_URL = "sqlite:///./care_sync.db"

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# File upload settings
UPLOAD_DIR = BASE_DIR / "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.txt', '.doc', '.docx'}

# Encryption settings
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "your-encryption-key-change-in-production")

# Application settings
APP_NAME = "Care-Sync"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Create upload directory if it doesn't exist
UPLOAD_DIR.mkdir(exist_ok=True)

# Role definitions
class UserRole:
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

# Health record types
class RecordType:
    LAB_REPORT = "Lab Report"
    PRESCRIPTION = "Prescription"
    DIAGNOSIS = "Diagnosis"
    IMAGING = "Imaging"
    VACCINATION = "Vaccination"
    OTHER = "Other"

# Appointment status
class AppointmentStatus:
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Critical health value thresholds
CRITICAL_VALUES = {
    "blood_pressure_systolic": {"min": 90, "max": 140},
    "blood_pressure_diastolic": {"min": 60, "max": 90},
    "heart_rate": {"min": 60, "max": 100},
    "temperature": {"min": 36.1, "max": 37.2},
    "blood_sugar": {"min": 70, "max": 140}
}
