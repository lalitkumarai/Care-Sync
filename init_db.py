"""
Database initialization script for Care-Sync Application
"""
from database import create_tables, SessionLocal, User
from utils import get_password_hash
from config import UserRole
from datetime import datetime

def create_sample_users():
    """Create sample users for testing"""
    db = SessionLocal()
    
    try:
        # Check if users already exist
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("Users already exist in database. Skipping user creation.")
            return
        
        # Create sample patient
        patient = User(
            username="patient1",
            email="patient1@example.com",
            hashed_password=get_password_hash("password123"),
            role=UserRole.PATIENT,
            full_name="John Doe",
            phone="+1234567890",
            date_of_birth=datetime(1990, 5, 15),
            gender="Male",
            address="123 Main St, City, State 12345"
        )
        
        # Create sample doctor
        doctor = User(
            username="doctor1",
            email="doctor1@example.com",
            hashed_password=get_password_hash("password123"),
            role=UserRole.DOCTOR,
            full_name="Dr. Jane Smith",
            phone="+1234567891",
            date_of_birth=datetime(1980, 8, 20),
            gender="Female",
            address="456 Medical Center Dr, City, State 12345"
        )
        
        # Create sample admin
        admin = User(
            username="admin1",
            email="admin1@example.com",
            hashed_password=get_password_hash("password123"),
            role=UserRole.ADMIN,
            full_name="Admin User",
            phone="+1234567892",
            date_of_birth=datetime(1985, 3, 10),
            gender="Other",
            address="789 Admin Blvd, City, State 12345"
        )
        
        # Add users to database
        db.add(patient)
        db.add(doctor)
        db.add(admin)
        db.commit()
        
        print("Sample users created successfully!")
        print("\nLogin credentials:")
        print("Patient: username='patient1', password='password123'")
        print("Doctor: username='doctor1', password='password123'")
        print("Admin: username='admin1', password='password123'")
        
    except Exception as e:
        print(f"Error creating sample users: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Initialize database"""
    print("Initializing Care-Sync database...")
    
    # Create tables
    create_tables()
    print("Database tables created successfully!")
    
    # Create sample users
    create_sample_users()
    
    print("\nDatabase initialization complete!")
    print("You can now start the application with: streamlit run app.py")

if __name__ == "__main__":
    main()
