"""
FastAPI endpoints for Care-Sync Application
"""
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import os
import json
from pydantic import BaseModel

from database import get_db, User, HealthRecord, Appointment, RecordAccess, AccessLog, HealthMetric
from utils import (
    verify_password, get_password_hash, create_access_token, verify_token,
    encrypt_file, extract_metadata_from_file, validate_file_upload,
    analyze_health_metrics
)
from config import UPLOAD_DIR, MAX_FILE_SIZE, UserRole, RecordType, AppointmentStatus

app = FastAPI(title="Care-Sync API", version="1.0.0")
security = HTTPBearer()

# Helper functions
def calculate_age(birth_date):
    """Calculate age from birth date, handling timezone issues"""
    try:
        today = datetime.now()
        # Handle timezone-aware dates
        if birth_date.tzinfo is not None:
            birth_date = birth_date.replace(tzinfo=None)
        return (today - birth_date).days // 365
    except:
        return None

# Pydantic models for API
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str
    full_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    duration_minutes: int = 30
    reason: Optional[str] = None

class RecordAccessGrant(BaseModel):
    record_id: int
    doctor_id: int
    expires_at: Optional[datetime] = None

class HealthMetricCreate(BaseModel):
    metric_name: str
    value: float
    unit: Optional[str] = None
    recorded_at: datetime
    notes: Optional[str] = None

# Authentication dependency
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

# Authentication endpoints
@app.post("/auth/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        full_name=user_data.full_name,
        phone=user_data.phone,
        date_of_birth=user_data.date_of_birth,
        gender=user_data.gender,
        address=user_data.address
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"message": "User registered successfully", "user_id": db_user.id}

@app.post("/auth/login")
def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    user = db.query(User).filter(User.username == user_credentials.username).first()

    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
        "full_name": user.full_name
    }

# Health record endpoints
@app.post("/records/upload")
async def upload_health_record(
    file: UploadFile = File(...),
    record_type: str = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    record_date: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a health record"""
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can upload health records"
        )

    # Create upload directory for user
    user_upload_dir = UPLOAD_DIR / str(current_user.id)
    user_upload_dir.mkdir(exist_ok=True)

    # Save uploaded file
    file_path = user_upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # Validate file
    validation_result = validate_file_upload(str(file_path), MAX_FILE_SIZE)
    if not validation_result["valid"]:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: {', '.join(validation_result['errors'])}"
        )

    # Extract metadata
    metadata = extract_metadata_from_file(str(file_path))

    # Encrypt file
    encrypted_path = encrypt_file(str(file_path))

    # Save record to database
    db_record = HealthRecord(
        patient_id=current_user.id,
        record_type=record_type,
        title=title,
        description=description,
        file_path=encrypted_path,
        file_name=file.filename,
        file_size=metadata["file_size"],
        record_metadata=json.dumps(metadata),
        record_date=datetime.fromisoformat(record_date)
    )

    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    # Log access
    log_entry = AccessLog(
        user_id=current_user.id,
        record_id=db_record.id,
        action="upload"
    )
    db.add(log_entry)
    db.commit()

    return {"message": "Health record uploaded successfully", "record_id": db_record.id}

@app.get("/records/my-records")
def get_my_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's health records"""
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can view their own records"
        )

    records = db.query(HealthRecord).filter(HealthRecord.patient_id == current_user.id).all()

    return {
        "records": [
            {
                "id": record.id,
                "record_type": record.record_type,
                "title": record.title,
                "description": record.description,
                "file_name": record.file_name,
                "record_date": record.record_date,
                "date_created": record.date_created
            }
            for record in records
        ]
    }

@app.post("/records/grant-access")
def grant_record_access(
    access_data: RecordAccessGrant,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Grant access to a health record to a doctor"""
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can grant access to their records"
        )

    # Verify record belongs to current user
    record = db.query(HealthRecord).filter(
        HealthRecord.id == access_data.record_id,
        HealthRecord.patient_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health record not found"
        )

    # Verify doctor exists
    doctor = db.query(User).filter(
        User.id == access_data.doctor_id,
        User.role == UserRole.DOCTOR
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    # Create access permission
    access_permission = RecordAccess(
        record_id=access_data.record_id,
        doctor_id=access_data.doctor_id,
        granted_by=current_user.id,
        expires_at=access_data.expires_at
    )

    db.add(access_permission)
    db.commit()

    return {"message": "Access granted successfully"}

# Appointment endpoints
@app.post("/appointments/create")
def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new appointment"""
    if current_user.role not in [UserRole.DOCTOR, UserRole.PATIENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors and patients can create appointments"
        )

    # Verify patient and doctor exist
    patient = db.query(User).filter(
        User.id == appointment_data.patient_id,
        User.role == UserRole.PATIENT
    ).first()

    doctor = db.query(User).filter(
        User.id == appointment_data.doctor_id,
        User.role == UserRole.DOCTOR
    ).first()

    if not patient or not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient or doctor not found"
        )

    # Create appointment
    db_appointment = Appointment(
        patient_id=appointment_data.patient_id,
        doctor_id=appointment_data.doctor_id,
        appointment_date=appointment_data.appointment_date,
        duration_minutes=appointment_data.duration_minutes,
        reason=appointment_data.reason,
        status=AppointmentStatus.PENDING
    )

    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)

    return {"message": "Appointment created successfully", "appointment_id": db_appointment.id}

@app.get("/appointments/my-appointments")
def get_my_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's appointments"""
    if current_user.role == UserRole.PATIENT:
        appointments = db.query(Appointment).filter(Appointment.patient_id == current_user.id).all()
    elif current_user.role == UserRole.DOCTOR:
        appointments = db.query(Appointment).filter(Appointment.doctor_id == current_user.id).all()
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients and doctors can view appointments"
        )

    return {
        "appointments": [
            {
                "id": apt.id,
                "patient_id": apt.patient_id,
                "doctor_id": apt.doctor_id,
                "appointment_date": apt.appointment_date,
                "duration_minutes": apt.duration_minutes,
                "status": apt.status,
                "reason": apt.reason,
                "notes": apt.notes
            }
            for apt in appointments
        ]
    }

# Doctor search and patient management endpoints
@app.get("/doctors/search-patients")
def search_patients(
    condition: Optional[str] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    gender: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search patients based on criteria (for doctors)"""
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can search patients"
        )

    query = db.query(User).filter(User.role == UserRole.PATIENT)

    if gender:
        query = query.filter(User.gender == gender)

    if age_min or age_max:
        today = datetime.now()
        if age_max:
            min_birth_date = today - timedelta(days=age_max * 365)
            query = query.filter(User.date_of_birth >= min_birth_date)
        if age_min:
            max_birth_date = today - timedelta(days=age_min * 365)
            query = query.filter(User.date_of_birth <= max_birth_date)

    patients = query.all()

    return {
        "patients": [
            {
                "id": patient.id,
                "full_name": patient.full_name,
                "age": calculate_age(patient.date_of_birth) if patient.date_of_birth else None,
                "gender": patient.gender,
                "phone": patient.phone
            }
            for patient in patients
        ]
    }

@app.get("/doctors/patient-records/{patient_id}")
def get_patient_records(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get patient records that doctor has access to"""
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can view patient records"
        )

    # Get records that doctor has access to
    accessible_records = db.query(HealthRecord).join(RecordAccess).filter(
        RecordAccess.doctor_id == current_user.id,
        RecordAccess.is_active == True,
        HealthRecord.patient_id == patient_id
    ).all()

    # Log access
    for record in accessible_records:
        log_entry = AccessLog(
            user_id=current_user.id,
            record_id=record.id,
            action="view"
        )
        db.add(log_entry)

    db.commit()

    return {
        "records": [
            {
                "id": record.id,
                "record_type": record.record_type,
                "title": record.title,
                "description": record.description,
                "record_date": record.record_date,
                "metadata": json.loads(record.record_metadata) if record.record_metadata else {}
            }
            for record in accessible_records
        ]
    }

# Health metrics endpoints
@app.post("/health-metrics/add")
def add_health_metric(
    metric_data: HealthMetricCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a health metric"""
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can add health metrics"
        )

    db_metric = HealthMetric(
        patient_id=current_user.id,
        metric_name=metric_data.metric_name,
        value=metric_data.value,
        unit=metric_data.unit,
        recorded_at=metric_data.recorded_at,
        notes=metric_data.notes
    )

    db.add(db_metric)
    db.commit()

    return {"message": "Health metric added successfully"}

@app.get("/health-metrics/analysis")
def get_health_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health metrics analysis"""
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can view their health analysis"
        )

    metrics = db.query(HealthMetric).filter(HealthMetric.patient_id == current_user.id).all()

    metrics_data = [
        {
            "metric_name": metric.metric_name,
            "value": metric.value,
            "unit": metric.unit,
            "recorded_at": metric.recorded_at
        }
        for metric in metrics
    ]

    analysis = analyze_health_metrics(metrics_data)

    return {"analysis": analysis}

# Appointment management endpoints
@app.put("/appointments/{appointment_id}/update")
def update_appointment_status(
    appointment_id: int,
    update_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update appointment status"""
    if current_user.role not in [UserRole.DOCTOR, UserRole.PATIENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors and patients can update appointments"
        )

    # Get appointment
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Check permissions
    if current_user.role == UserRole.DOCTOR and appointment.doctor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own appointments"
        )
    elif current_user.role == UserRole.PATIENT and appointment.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own appointments"
        )

    # Update appointment
    if "status" in update_data:
        appointment.status = update_data["status"]
    if "notes" in update_data:
        appointment.notes = update_data["notes"]

    appointment.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Appointment updated successfully"}

# Admin endpoints
@app.get("/admin/users")
def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    users = db.query(User).all()
    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_at": user.created_at
            }
            for user in users
        ]
    }

@app.get("/admin/statistics")
def get_system_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system statistics (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Count statistics
    total_users = db.query(User).count()
    total_patients = db.query(User).filter(User.role == UserRole.PATIENT).count()
    total_doctors = db.query(User).filter(User.role == UserRole.DOCTOR).count()
    total_records = db.query(HealthRecord).count()
    total_appointments = db.query(Appointment).count()
    total_metrics = db.query(HealthMetric).count()

    return {
        "statistics": {
            "total_users": total_users,
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "total_records": total_records,
            "total_appointments": total_appointments,
            "total_metrics": total_metrics
        }
    }

@app.get("/admin/audit-logs")
def get_audit_logs(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    logs = db.query(AccessLog).order_by(AccessLog.timestamp.desc()).limit(limit).all()

    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "record_id": log.record_id,
                "action": log.action,
                "timestamp": log.timestamp,
                "ip_address": log.ip_address
            }
            for log in logs
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
