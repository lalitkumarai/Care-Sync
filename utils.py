"""
Utility functions for Care-Sync Application
"""
import os
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from jose import JWTError, jwt
# import magic  # Optional dependency
import PyPDF2
from PIL import Image
import pandas as pd
from config import SECRET_KEY, ALGORITHM, ENCRYPTION_KEY, CRITICAL_VALUES

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryption setup
def get_encryption_key():
    """Get or generate encryption key"""
    if ENCRYPTION_KEY and ENCRYPTION_KEY != "your-encryption-key-change-in-production":
        return ENCRYPTION_KEY.encode()
    else:
        # Generate a new key for development
        return Fernet.generate_key()

fernet = Fernet(get_encryption_key())

# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

# JWT token utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Encryption utilities
def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    return fernet.decrypt(encrypted_data.encode()).decode()

def encrypt_file(file_path: str) -> str:
    """Encrypt a file and return encrypted file path"""
    with open(file_path, 'rb') as file:
        file_data = file.read()

    encrypted_data = fernet.encrypt(file_data)
    encrypted_path = f"{file_path}.encrypted"

    with open(encrypted_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)

    # Remove original file
    os.remove(file_path)
    return encrypted_path

def decrypt_file(encrypted_path: str, output_path: str) -> str:
    """Decrypt a file and save to output path"""
    with open(encrypted_path, 'rb') as encrypted_file:
        encrypted_data = encrypted_file.read()

    decrypted_data = fernet.decrypt(encrypted_data)

    with open(output_path, 'wb') as output_file:
        output_file.write(decrypted_data)

    return output_path

# File processing utilities
def get_file_type(file_path: str) -> str:
    """Get file MIME type"""
    # Extension-based detection (fallback when python-magic is not available)
    ext = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.txt': 'text/plain',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    return mime_types.get(ext, 'application/octet-stream')

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_metadata_from_file(file_path: str) -> Dict[str, Any]:
    """Extract metadata from uploaded file"""
    metadata = {
        "file_size": os.path.getsize(file_path),
        "file_type": get_file_type(file_path),
        "upload_time": datetime.now(timezone.utc).isoformat(),
        "checksum": calculate_file_checksum(file_path)
    }

    # Extract additional metadata based on file type
    file_type = metadata["file_type"]

    if file_type == "application/pdf":
        metadata["extracted_text"] = extract_text_from_pdf(file_path)
    elif file_type.startswith("image/"):
        try:
            with Image.open(file_path) as img:
                metadata["image_dimensions"] = img.size
                metadata["image_format"] = img.format
        except Exception:
            pass

    return metadata

def calculate_file_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# Health data analysis utilities
def analyze_health_metrics(metrics_data: list) -> Dict[str, Any]:
    """Analyze health metrics and detect trends"""
    if not metrics_data:
        return {}

    df = pd.DataFrame(metrics_data)
    analysis = {}

    for metric_name in df['metric_name'].unique():
        metric_df = df[df['metric_name'] == metric_name].sort_values('recorded_at')

        analysis[metric_name] = {
            "latest_value": metric_df.iloc[-1]['value'] if not metric_df.empty else None,
            "average": metric_df['value'].mean(),
            "min": metric_df['value'].min(),
            "max": metric_df['value'].max(),
            "trend": calculate_trend(metric_df['value'].tolist()),
            "critical_alerts": check_critical_values(metric_name, metric_df['value'].tolist())
        }

    return analysis

def calculate_trend(values: list) -> str:
    """Calculate trend direction for a series of values"""
    if len(values) < 2:
        return "insufficient_data"

    # Simple trend calculation using first and last values
    if values[-1] > values[0]:
        return "increasing"
    elif values[-1] < values[0]:
        return "decreasing"
    else:
        return "stable"

def check_critical_values(metric_name: str, values: list) -> list:
    """Check for critical health values"""
    alerts = []

    if metric_name in CRITICAL_VALUES:
        thresholds = CRITICAL_VALUES[metric_name]
        for value in values:
            if value < thresholds["min"] or value > thresholds["max"]:
                alerts.append({
                    "value": value,
                    "threshold": thresholds,
                    "severity": "critical" if value < thresholds["min"] * 0.8 or value > thresholds["max"] * 1.2 else "warning"
                })

    return alerts

# Validation utilities
def validate_file_upload(file_path: str, max_size: int) -> Dict[str, Any]:
    """Validate uploaded file"""
    result = {"valid": True, "errors": []}

    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size > max_size:
        result["valid"] = False
        result["errors"].append(f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)")

    # Check file type
    file_type = get_file_type(file_path)
    allowed_types = [
        'application/pdf', 'image/jpeg', 'image/png', 'text/plain',
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]

    if file_type not in allowed_types:
        result["valid"] = False
        result["errors"].append(f"File type ({file_type}) is not allowed")

    return result
