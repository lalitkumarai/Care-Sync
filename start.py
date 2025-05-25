"""
Startup script for Care-Sync Application
"""
import subprocess
import sys
import time
import threading
import os
from pathlib import Path

def check_dependencies():
    """Check if all dependencies are installed"""
    try:
        import streamlit
        import fastapi
        import sqlalchemy
        print("✓ Dependencies check passed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def initialize_database():
    """Initialize the database"""
    print("Initializing database...")
    try:
        from database import create_tables
        from init_db import create_sample_users
        
        create_tables()
        create_sample_users()
        print("✓ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def start_api_server():
    """Start the FastAPI server"""
    try:
        print("Starting API server on http://localhost:8000...")
        subprocess.run([
            sys.executable, "-m", "uvicorn", "api:app",
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ])
    except KeyboardInterrupt:
        print("\nAPI server stopped")
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")

def start_streamlit_app():
    """Start the Streamlit application"""
    try:
        print("Starting Streamlit app on http://localhost:8501...")
        time.sleep(3)  # Wait for API server to start
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501"
        ])
    except KeyboardInterrupt:
        print("\nStreamlit app stopped")
    except Exception as e:
        print(f"❌ Failed to start Streamlit app: {e}")

def main():
    """Main startup function"""
    print("=" * 60)
    print("🏥 Care-Sync: Patient Health Records Management System")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Initialize database
    if not initialize_database():
        return 1
    
    print("\n🚀 Starting Care-Sync Application...")
    print("\nServices will be available at:")
    print("- Streamlit App: http://localhost:8501")
    print("- API Server: http://localhost:8000")
    print("- API Docs: http://localhost:8000/docs")
    
    print("\n📝 Sample Login Credentials:")
    print("- Patient: username='patient1', password='password123'")
    print("- Doctor: username='doctor1', password='password123'")
    print("- Admin: username='admin1', password='password123'")
    
    print("\n⚠️  Press Ctrl+C to stop all services")
    print("-" * 60)
    
    try:
        # Start API server in a separate thread
        api_thread = threading.Thread(target=start_api_server, daemon=True)
        api_thread.start()
        
        # Start Streamlit app in main thread
        start_streamlit_app()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down Care-Sync...")
        print("Thank you for using Care-Sync!")
        return 0
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
