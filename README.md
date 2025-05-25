# Care-Sync: Patient Health Records Management System

A secure web-based application for managing patient health records, enabling seamless interaction between patients and healthcare providers with role-based access control and comprehensive security measures.

## 🏥 Features

### Patient Features
- **Health Record Upload**: Upload medical documents (PDFs, images, text files)
- **Record Management**: View and organize personal health records
- **Access Control**: Grant/revoke access to specific doctors
- **Appointment Management**: View scheduled appointments
- **Health Metrics**: Track vital signs and health indicators
- **Health Analysis**: View trends and receive critical value alerts

### Doctor Features
- **Patient Search**: Find patients by demographics and conditions
- **Record Access**: View patient records (with permission)
- **Appointment Scheduling**: Book consultations with patients
- **Health Monitoring**: Analyze patient health trends
- **Access Logging**: All record access is logged for audit trails

### Security Features
- **Role-Based Access Control**: Patient, Doctor, and Admin roles
- **Data Encryption**: All sensitive data and files are encrypted
- **JWT Authentication**: Secure token-based authentication
- **Access Permissions**: Patients control who can access their records
- **Audit Trails**: Complete logging of all system access

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd care-sync
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python init_db.py
   ```

4. **Start the API server**
   ```bash
   python api.py
   ```

5. **Start the Streamlit application** (in a new terminal)
   ```bash
   streamlit run app.py
   ```

6. **Access the application**
   - Open your browser and go to `http://localhost:8501`
   - Use the sample credentials provided during database initialization

## 📁 Project Structure

```
care-sync/
├── app.py              # Main Streamlit application
├── api.py              # FastAPI backend endpoints
├── database.py         # Database models and setup
├── utils.py            # Utility functions (encryption, validation)
├── config.py           # Configuration settings
├── init_db.py          # Database initialization script
├── requirements.txt    # Python dependencies
├── uploads/            # Directory for uploaded files (created automatically)
└── README.md          # This file
```

## 🔐 Security Measures

### Data Protection
- **File Encryption**: All uploaded files are encrypted using Fernet encryption
- **Password Hashing**: User passwords are hashed using bcrypt
- **JWT Tokens**: Secure authentication with expiring tokens
- **Input Validation**: All user inputs are validated and sanitized

### Access Control
- **Role-Based Permissions**: Different access levels for patients, doctors, and admins
- **Record Permissions**: Patients explicitly grant access to their records
- **Session Management**: Secure session handling with automatic logout
- **API Security**: All API endpoints require authentication

### Compliance
- **HIPAA Considerations**: Designed with healthcare privacy standards in mind
- **Audit Logging**: Complete audit trail of all data access
- **Data Minimization**: Only necessary data is collected and stored
- **Secure Communication**: HTTPS recommended for production deployment

## 🔧 Configuration

### Environment Variables
Create a `.env` file for production deployment:

```env
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
DATABASE_URL=sqlite:///./care_sync.db
DEBUG=False
```

### File Upload Settings
- **Maximum file size**: 10MB (configurable in `config.py`)
- **Supported formats**: PDF, JPG, PNG, TXT, DOC, DOCX
- **Storage**: Local filesystem with encryption

## 📊 API Documentation

### Authentication Endpoints
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login

### Health Records Endpoints
- `POST /records/upload` - Upload health record
- `GET /records/my-records` - Get user's records
- `POST /records/grant-access` - Grant record access to doctor

### Appointment Endpoints
- `POST /appointments/create` - Create appointment
- `GET /appointments/my-appointments` - Get user's appointments

### Health Metrics Endpoints
- `POST /health-metrics/add` - Add health metric
- `GET /health-metrics/analysis` - Get health analysis

### Doctor Endpoints
- `GET /doctors/search-patients` - Search patients
- `GET /doctors/patient-records/{patient_id}` - Get patient records

## 🧪 Testing

### Sample Users
The database initialization creates sample users for testing:

- **Patient**: username=`patient1`, password=`password123`
- **Doctor**: username=`doctor1`, password=`password123`
- **Admin**: username=`admin1`, password=`password123`

### Testing Workflow
1. Login as a patient and upload health records
2. Grant access to a doctor
3. Login as a doctor and search for patients
4. View patient records and schedule appointments
5. Add health metrics and view analysis

## 🚀 Deployment

### Local Development
Follow the Quick Start guide above.

### Production Deployment
1. Set up a production database (PostgreSQL recommended)
2. Configure environment variables
3. Use a production WSGI server (e.g., Gunicorn)
4. Set up HTTPS with SSL certificates
5. Configure file storage (cloud storage recommended)

### Hugging Face Spaces Deployment
1. Create a new Space on Hugging Face
2. Upload all project files
3. Add a `app.py` file as the main Streamlit app
4. Configure secrets for environment variables

## 🔍 Troubleshooting

### Common Issues

1. **Database connection errors**
   - Ensure the database is initialized: `python init_db.py`
   - Check file permissions in the project directory

2. **File upload failures**
   - Verify the `uploads/` directory exists and is writable
   - Check file size limits in `config.py`

3. **Authentication issues**
   - Ensure the API server is running on port 8000
   - Check that JWT tokens are not expired

4. **Import errors**
   - Install all dependencies: `pip install -r requirements.txt`
   - Ensure Python version compatibility (3.8+)
