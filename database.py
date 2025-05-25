"""
Database models and setup for Care-Sync Application
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
from config import DATABASE_URL

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # patient, doctor, admin
    full_name = Column(String, nullable=False)
    phone = Column(String)
    date_of_birth = Column(DateTime)
    gender = Column(String)
    address = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient_records = relationship("HealthRecord", back_populates="patient", foreign_keys="HealthRecord.patient_id")
    doctor_appointments = relationship("Appointment", back_populates="doctor", foreign_keys="Appointment.doctor_id")
    patient_appointments = relationship("Appointment", back_populates="patient", foreign_keys="Appointment.patient_id")

class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    record_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    file_path = Column(String)
    file_name = Column(String)
    file_size = Column(Integer)
    record_metadata = Column(Text)  # JSON string for additional metadata
    date_created = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    record_date = Column(DateTime, nullable=False)
    is_encrypted = Column(Boolean, default=True)

    # Relationships
    patient = relationship("User", back_populates="patient_records", foreign_keys=[patient_id])
    access_permissions = relationship("RecordAccess", back_populates="record")

class RecordAccess(Base):
    __tablename__ = "record_access"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("health_records.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    record = relationship("HealthRecord", back_populates="access_permissions")
    doctor = relationship("User", foreign_keys=[doctor_id])
    granter = relationship("User", foreign_keys=[granted_by])

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(String, default="pending")
    reason = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("User", back_populates="patient_appointments", foreign_keys=[patient_id])
    doctor = relationship("User", back_populates="doctor_appointments", foreign_keys=[doctor_id])

class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    record_id = Column(Integer, ForeignKey("health_records.id"))
    action = Column(String, nullable=False)  # view, download, upload, etc.
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = Column(String)
    user_agent = Column(String)

    # Relationships
    user = relationship("User")
    record = relationship("HealthRecord")

class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    metric_name = Column(String, nullable=False)  # blood_pressure, heart_rate, etc.
    value = Column(Float, nullable=False)
    unit = Column(String)
    recorded_at = Column(DateTime, nullable=False)
    is_critical = Column(Boolean, default=False)
    notes = Column(Text)

    # Relationships
    patient = relationship("User")

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
