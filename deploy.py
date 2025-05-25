"""
Deployment script for Care-Sync Application
"""
import os
import subprocess
import sys
from pathlib import Path

def create_huggingface_files():
    """Create files needed for Hugging Face Spaces deployment"""
    
    # Create app.py for Hugging Face (entry point)
    hf_app_content = '''"""
Hugging Face Spaces entry point for Care-Sync
"""
import subprocess
import threading
import time
import streamlit as st
from database import create_tables

def start_api_server():
    """Start the FastAPI server in background"""
    try:
        subprocess.run([
            "python", "-m", "uvicorn", "api:app", 
            "--host", "0.0.0.0", "--port", "8000"
        ], check=True)
    except Exception as e:
        print(f"Failed to start API server: {e}")

def main():
    """Main function for Hugging Face deployment"""
    # Initialize database
    create_tables()
    
    # Start API server in background thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Give API server time to start
    time.sleep(3)
    
    # Import and run the main Streamlit app
    from app import main as app_main
    app_main()

if __name__ == "__main__":
    main()
'''
    
    with open("hf_app.py", "w") as f:
        f.write(hf_app_content)
    
    # Create requirements.txt for Hugging Face
    hf_requirements = """streamlit==1.28.1
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pandas==2.1.3
numpy==1.24.3
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
cryptography==41.0.7
Pillow==10.1.0
PyPDF2==3.0.1
plotly==5.17.0
bcrypt==4.1.1
pydantic==2.5.0
email-validator==2.1.0
python-dateutil==2.8.2
requests==2.31.0
aiofiles==23.2.1
jinja2==3.1.2"""
    
    with open("hf_requirements.txt", "w") as f:
        f.write(hf_requirements)
    
    # Create README for Hugging Face
    hf_readme = """---
title: Care-Sync
emoji: 🏥
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.28.1
app_file: hf_app.py
pinned: false
license: mit
---

# Care-Sync: Patient Health Records Management System

A secure web-based application for managing patient health records with role-based access control.

## Features
- Patient health record upload and management
- Doctor-patient appointment system
- Health metrics tracking and analysis
- Secure role-based access control
- Data encryption and audit trails

## Usage
1. Register as a patient, doctor, or admin
2. Upload health records (patients)
3. Grant access to doctors
4. Schedule appointments
5. Track health metrics

## Sample Credentials
- Patient: username=`patient1`, password=`password123`
- Doctor: username=`doctor1`, password=`password123`
- Admin: username=`admin1`, password=`password123`

## Security
- All data is encrypted
- Role-based access control
- Audit logging
- HIPAA-compliant design
"""
    
    with open("HF_README.md", "w") as f:
        f.write(hf_readme)
    
    print("✓ Hugging Face deployment files created")

def create_docker_files():
    """Create Docker files for containerized deployment"""
    
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Initialize database
RUN python init_db.py

# Expose ports
EXPOSE 8000 8501

# Start both API and Streamlit
CMD ["sh", "-c", "python api.py & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    # Docker compose file
    docker_compose_content = """version: '3.8'

services:
  care-sync:
    build: .
    ports:
      - "8501:8501"
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./care_sync.db:/app/care_sync.db
    environment:
      - SECRET_KEY=your-secret-key-here
      - ENCRYPTION_KEY=your-encryption-key-here
      - DEBUG=False
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose_content)
    
    print("✓ Docker deployment files created")

def create_deployment_guide():
    """Create deployment guide"""
    
    guide_content = """# Care-Sync Deployment Guide

## Local Development

1. **Setup**
   ```bash
   pip install -r requirements.txt
   python init_db.py
   ```

2. **Run Application**
   ```bash
   # Terminal 1: Start API server
   python api.py
   
   # Terminal 2: Start Streamlit app
   streamlit run app.py
   ```

## Hugging Face Spaces Deployment

1. **Create a new Space**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Choose "Streamlit" as SDK

2. **Upload Files**
   - Upload all project files
   - Use `hf_app.py` as the main app file
   - Use `hf_requirements.txt` for dependencies

3. **Configure**
   - Set app_file to `hf_app.py` in README.md
   - Add secrets for sensitive configuration

## Docker Deployment

1. **Build and Run**
   ```bash
   docker-compose up --build
   ```

2. **Access Application**
   - Streamlit: http://localhost:8501
   - API: http://localhost:8000

## Production Considerations

### Security
- Use strong SECRET_KEY and ENCRYPTION_KEY
- Enable HTTPS
- Configure proper firewall rules
- Regular security audits

### Database
- Use PostgreSQL for production
- Regular backups
- Database encryption at rest

### File Storage
- Use cloud storage (AWS S3, Google Cloud Storage)
- Implement proper access controls
- Regular backups

### Monitoring
- Application logging
- Performance monitoring
- Health checks
- Error tracking

### Compliance
- HIPAA compliance review
- Data retention policies
- Access audit procedures
- Incident response plan
"""
    
    with open("DEPLOYMENT.md", "w") as f:
        f.write(guide_content)
    
    print("✓ Deployment guide created")

def main():
    """Main deployment preparation function"""
    print("=" * 50)
    print("Care-Sync Deployment Preparation")
    print("=" * 50)
    
    print("\nCreating deployment files...")
    
    try:
        create_huggingface_files()
        create_docker_files()
        create_deployment_guide()
        
        print("\n✅ Deployment preparation complete!")
        print("\nFiles created:")
        print("- hf_app.py (Hugging Face entry point)")
        print("- hf_requirements.txt (Hugging Face dependencies)")
        print("- HF_README.md (Hugging Face README)")
        print("- Dockerfile (Docker configuration)")
        print("- docker-compose.yml (Docker Compose)")
        print("- DEPLOYMENT.md (Deployment guide)")
        
        print("\nNext steps:")
        print("1. Test locally: python test_setup.py")
        print("2. Initialize database: python init_db.py")
        print("3. Deploy to your preferred platform")
        
    except Exception as e:
        print(f"❌ Error during deployment preparation: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
