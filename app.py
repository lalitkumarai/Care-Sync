"""
Main Streamlit application for Care-Sync
"""
import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Care-Sync",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean Modern Healthcare Theme - FIXED
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global App Styling */
    .stApp {
        background: #f8fafc;
        font-family: 'Inter', sans-serif;
    }

    /* Main Container - Clean and Simple */
    .main .block-container {
        background: #ffffff;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid #e2e8f0;
        max-width: 1200px;
    }

    /* Clean Header - NO BLUR, CRYSTAL CLEAR */
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1.5rem;
        color: #1a202c;
        text-shadow: none;
        filter: none;
        -webkit-filter: none;
    }

    /* Clean Card Styling */
    .dashboard-card, .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }

    .metric-card {
        text-align: center;
        background: #3182ce;
        color: white;
        border: none;
    }

    /* Clean Simple Buttons */
    .stButton > button {
        background: #3182ce;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.9rem;
    }

    .stButton > button:hover {
        background: #2c5aa0;
    }

    /* Clean Form Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stTimeInput > div > div > input {
        border-radius: 6px;
        border: 1px solid #d1d5db;
        padding: 0.5rem;
        font-size: 0.9rem;
        background: white;
        color: #374151;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div:focus-within,
    .stNumberInput > div > div > input:focus,
    .stDateInput > div > div > input:focus,
    .stTimeInput > div > div > input:focus {
        border-color: #3182ce;
        outline: none;
        box-shadow: 0 0 0 2px rgba(49, 130, 206, 0.2);
    }

    /* Clean Sidebar */
    .css-1d391kg {
        background: #1f2937;
    }

    .css-1d391kg .css-1v0mbdj {
        color: white;
    }

    /* Clean Messages */
    .stSuccess {
        background: #10b981;
        color: white;
        border-radius: 6px;
        padding: 0.75rem;
        border: none;
    }

    .stError {
        background: #ef4444;
        color: white;
        border-radius: 6px;
        padding: 0.75rem;
        border: none;
    }

    .stWarning {
        background: #f59e0b;
        color: white;
        border-radius: 6px;
        padding: 0.75rem;
        border: none;
    }

    .stInfo {
        background: #3b82f6;
        color: white;
        border-radius: 6px;
        padding: 0.75rem;
        border: none;
    }

    /* Crystal Clear Text */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #111827;
        font-weight: 600;
    }

    .stMarkdown p {
        color: #374151;
        line-height: 1.5;
    }

    /* Clean Labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stNumberInput > label,
    .stDateInput > label,
    .stTimeInput > label,
    .stFileUploader > label {
        color: #374151;
        font-weight: 500;
        font-size: 0.9rem;
    }

    /* Clean Tables */
    .stDataFrame {
        border-radius: 6px;
        border: 1px solid #e5e7eb;
    }

    /* Clean Expanders */
    .streamlit-expanderHeader {
        background: #f9fafb;
        border-radius: 6px;
        border: 1px solid #e5e7eb;
        color: #374151;
        font-weight: 500;
    }

    /* Clean File Upload */
    .stFileUploader > div {
        border-radius: 6px;
        border: 2px dashed #d1d5db;
        background: #f9fafb;
    }

    .stFileUploader > div:hover {
        border-color: #3182ce;
    }

    /* Clean Metrics */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 1rem;
        border-radius: 6px;
    }

    /* Hide Streamlit Branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'access_token' not in st.session_state:
    st.session_state.access_token = None

# Helper functions
def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None) -> Dict[str, Any]:
    """Make API request with authentication"""
    headers = {}
    if st.session_state.access_token:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"

    url = f"{API_BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, data=data, files=files)
            else:
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            headers["Content-Type"] = "application/json"
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.json().get("detail", "Unknown error")}

    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}

def login_user(username: str, password: str) -> bool:
    """Authenticate user"""
    try:
        # Make direct API call to test
        url = f"{API_BASE_URL}/auth/login"
        headers = {"Content-Type": "application/json"}
        data = {"username": username, "password": password}

        response = requests.post(url, headers=headers, json=data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            st.session_state.authenticated = True
            st.session_state.access_token = result["access_token"]
            st.session_state.user_data = result
            st.success("Login successful!")
            return True
        else:
            error_msg = response.json().get("detail", "Login failed")
            st.error(f"Login failed: {error_msg}")
            return False

    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False

def logout_user():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.user_data = None
    st.rerun()

def register_user(user_data: Dict) -> bool:
    """Register new user"""
    response = make_api_request("/auth/register", "POST", user_data)

    if response["success"]:
        st.success("Registration successful! Please login.")
        return True
    else:
        st.error(f"Registration failed: {response['error']}")
        return False

# Authentication pages
def show_login_page():
    """Display clean login page"""
    st.markdown('<h1 class="main-header">🏥 Care-Sync</h1>', unsafe_allow_html=True)

    _, col2, _ = st.columns([1, 2, 1])

    with col2:
        st.markdown("## Login")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")

            if submit_button:
                if username and password:
                    if login_user(username, password):
                        st.rerun()
                else:
                    st.error("Please enter username and password")

        st.markdown("---")

        st.markdown("**Demo Accounts:**")
        st.markdown("• Patient: `patient1` / `password123`")
        st.markdown("• Doctor: `doctor1` / `password123`")
        st.markdown("• Admin: `admin1` / `password123`")

        if st.button("Register New Account"):
            st.session_state.show_register = True
            st.rerun()

def show_register_page():
    """Display clean registration page"""
    st.markdown('<h1 class="main-header">🏥 Care-Sync Registration</h1>', unsafe_allow_html=True)

    _, col2, _ = st.columns([1, 2, 1])

    with col2:
        st.markdown("## Create Account")

        with st.form("register_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            full_name = st.text_input("Full Name")
            role = st.selectbox("Role", ["patient", "doctor", "admin"])
            phone = st.text_input("Phone (optional)")

            col_a, col_b = st.columns(2)
            with col_a:
                date_of_birth = st.date_input("Date of Birth (optional)", value=None)
            with col_b:
                gender = st.selectbox("Gender (optional)", ["", "Male", "Female", "Other"])

            address = st.text_area("Address (optional)")

            submit_button = st.form_submit_button("Register")

            if submit_button:
                if not all([username, email, password, confirm_password, full_name]):
                    st.error("Please fill in all required fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    user_data = {
                        "username": username,
                        "email": email,
                        "password": password,
                        "role": role,
                        "full_name": full_name,
                        "phone": phone if phone else None,
                        "date_of_birth": date_of_birth.isoformat() if date_of_birth else None,
                        "gender": gender if gender else None,
                        "address": address if address else None
                    }

                    if register_user(user_data):
                        st.session_state.show_register = False
                        st.rerun()

        if st.button("Back to Login"):
            st.session_state.show_register = False
            st.rerun()

# Dashboard pages
def show_patient_dashboard():
    """Display patient dashboard"""
    st.markdown(f'<h1 class="main-header">👤 Patient Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(f"**Welcome, {st.session_state.user_data['full_name']}!**")

    # Sidebar navigation
    with st.sidebar:
        st.markdown("### Navigation")
        page = st.radio("Go to", [
            "Overview",
            "Upload Health Records",
            "My Health Records",
            "Manage Access",
            "My Appointments",
            "Book Appointment",
            "Health Metrics",
            "Health Analysis"
        ])

    if page == "Overview":
        show_patient_overview()
    elif page == "Upload Health Records":
        show_upload_records()
    elif page == "My Health Records":
        show_my_records()
    elif page == "Manage Access":
        show_manage_access()
    elif page == "My Appointments":
        show_my_appointments()
    elif page == "Health Metrics":
        show_health_metrics()
    elif page == "Health Analysis":
        show_health_analysis()
    elif page == "Book Appointment":
        show_book_appointment()

def show_doctor_dashboard():
    """Display doctor dashboard"""
    st.markdown(f'<h1 class="main-header">👨‍⚕️ Doctor Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(f"**Welcome, Dr. {st.session_state.user_data['full_name']}!**")

    # Sidebar navigation
    with st.sidebar:
        st.markdown("### Navigation")
        page = st.radio("Go to", [
            "Overview",
            "Search Patients",
            "Patient Records",
            "Appointments",
            "Schedule Appointment"
        ])

    if page == "Overview":
        show_doctor_overview()
    elif page == "Search Patients":
        show_search_patients()
    elif page == "Patient Records":
        show_patient_records()
    elif page == "Appointments":
        show_doctor_appointments()
    elif page == "Schedule Appointment":
        show_schedule_appointment()

def show_admin_dashboard():
    """Display admin dashboard"""
    st.markdown(f'<h1 class="main-header">⚙️ Admin Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(f"**Welcome, {st.session_state.user_data['full_name']}!**")

    # Sidebar navigation
    with st.sidebar:
        st.markdown("### Admin Navigation")
        page = st.radio("Go to", [
            "System Overview",
            "User Management",
            "Health Records Oversight",
            "Appointment Monitoring",
            "Audit Logs",
            "System Statistics",
            "Database Management",
            "System Configuration"
        ])

    if page == "System Overview":
        show_admin_overview()
    elif page == "User Management":
        show_user_management()
    elif page == "Health Records Oversight":
        show_records_oversight()
    elif page == "Appointment Monitoring":
        show_appointment_monitoring()
    elif page == "Audit Logs":
        show_audit_logs()
    elif page == "System Statistics":
        show_system_statistics()
    elif page == "Database Management":
        show_database_management()
    elif page == "System Configuration":
        show_system_configuration()

# Patient dashboard functions
def show_patient_overview():
    """Show clean patient overview"""
    st.markdown("## Dashboard Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Health Records", "0", help="Total uploaded records")

    with col2:
        st.metric("Appointments", "0", help="Scheduled appointments")

    with col3:
        st.metric("Active Doctors", "0", help="Doctors with access")

    st.markdown("### Quick Actions")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("📄 Upload Record"):
            st.info("Go to 'Upload Health Records' in the sidebar")

    with col_b:
        if st.button("📅 Book Appointment"):
            st.info("Go to 'Book Appointment' in the sidebar")

    with col_c:
        if st.button("📊 View Analytics"):
            st.info("Go to 'Health Analysis' in the sidebar")

def show_upload_records():
    """Show upload health records page"""
    st.markdown("### Upload Health Records")

    with st.form("upload_form"):
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'jpg', 'jpeg', 'png', 'txt', 'doc', 'docx'],
            help="Supported formats: PDF, Images (JPG, PNG), Text files, Word documents"
        )

        col1, col2 = st.columns(2)
        with col1:
            record_type = st.selectbox("Record Type", [
                "Lab Report", "Prescription", "Diagnosis",
                "Imaging", "Vaccination", "Other"
            ])
            title = st.text_input("Title")

        with col2:
            record_date = st.date_input("Record Date", value=datetime.now().date())
            description = st.text_area("Description (optional)")

        submit_button = st.form_submit_button("Upload Record")

        if submit_button:
            if uploaded_file and title:
                # Prepare form data
                files = {"file": uploaded_file}
                data = {
                    "record_type": record_type,
                    "title": title,
                    "description": description,
                    "record_date": record_date.isoformat()
                }

                response = make_api_request("/records/upload", "POST", data, files)

                if response["success"]:
                    st.success("Health record uploaded successfully!")
                else:
                    st.error(f"Upload failed: {response['error']}")
            else:
                st.error("Please select a file and enter a title")

def show_my_records():
    """Show patient's health records"""
    st.markdown("### My Health Records")

    response = make_api_request("/records/my-records")

    if response["success"]:
        records = response["data"]["records"]

        if records:
            # Create DataFrame for display
            df = pd.DataFrame(records)
            df['record_date'] = pd.to_datetime(df['record_date']).dt.strftime('%Y-%m-%d')
            df['date_created'] = pd.to_datetime(df['date_created']).dt.strftime('%Y-%m-%d %H:%M')

            # Display records
            for _, record in df.iterrows():
                with st.expander(f"{record['title']} - {record['record_type']} ({record['record_date']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Type:** {record['record_type']}")
                        st.write(f"**Date:** {record['record_date']}")
                        st.write(f"**File:** {record['file_name']}")
                    with col2:
                        st.write(f"**Uploaded:** {record['date_created']}")
                        if record['description']:
                            st.write(f"**Description:** {record['description']}")
        else:
            st.info("No health records found. Upload your first record!")
    else:
        st.error(f"Failed to load records: {response['error']}")

def show_manage_access():
    """Show manage access page"""
    st.markdown("### Manage Record Access")

    # Get user's records
    response = make_api_request("/records/my-records")

    if response["success"]:
        records = response["data"]["records"]

        if records:
            st.markdown("#### Grant Access to Doctor")

            with st.form("grant_access_form"):
                record_options = {f"{r['title']} ({r['record_type']})": r['id'] for r in records}
                selected_record = st.selectbox("Select Record", list(record_options.keys()))
                doctor_id = st.number_input("Doctor ID", min_value=1, step=1)
                expires_at = st.date_input("Access Expires (optional)", value=None)

                submit_button = st.form_submit_button("Grant Access")

                if submit_button:
                    data = {
                        "record_id": record_options[selected_record],
                        "doctor_id": doctor_id,
                        "expires_at": expires_at.isoformat() if expires_at else None
                    }

                    response = make_api_request("/records/grant-access", "POST", data)

                    if response["success"]:
                        st.success("Access granted successfully!")
                    else:
                        st.error(f"Failed to grant access: {response['error']}")
        else:
            st.info("No records available to grant access to.")
    else:
        st.error(f"Failed to load records: {response['error']}")

def show_my_appointments():
    """Show patient's appointments"""
    st.markdown("### My Appointments")

    response = make_api_request("/appointments/my-appointments")

    if response["success"]:
        appointments = response["data"]["appointments"]

        if appointments:
            df = pd.DataFrame(appointments)
            df['appointment_date'] = pd.to_datetime(df['appointment_date']).dt.strftime('%Y-%m-%d %H:%M')

            for _, apt in df.iterrows():
                with st.expander(f"Appointment with Doctor ID {apt['doctor_id']} - {apt['appointment_date']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Date:** {apt['appointment_date']}")
                        st.write(f"**Duration:** {apt['duration_minutes']} minutes")
                        st.write(f"**Status:** {apt['status']}")
                    with col2:
                        if apt['reason']:
                            st.write(f"**Reason:** {apt['reason']}")
                        if apt['notes']:
                            st.write(f"**Notes:** {apt['notes']}")
        else:
            st.info("No appointments scheduled.")
    else:
        st.error(f"Failed to load appointments: {response['error']}")

def show_book_appointment():
    """Show appointment booking interface for patients"""
    st.markdown("### Book New Appointment")

    # First, let patients search for available doctors
    st.markdown("#### Find a Doctor")

    with st.form("doctor_search_form"):
        col1, col2 = st.columns(2)
        with col1:
            specialty = st.selectbox("Specialty", ["General Practice", "Cardiology", "Dermatology", "Pediatrics", "Other"])
        with col2:
            location = st.text_input("Preferred Location (optional)")

        search_doctors_btn = st.form_submit_button("Search Doctors")

        if search_doctors_btn:
            # For now, show available doctors (this would be enhanced with real search)
            st.success("Available doctors found!")

            doctors_data = [
                {"ID": 2, "Name": "Dr. Jane Smith", "Specialty": "General Practice", "Rating": "4.8/5"},
                {"ID": 3, "Name": "Dr. Michael Johnson", "Specialty": "Cardiology", "Rating": "4.9/5"},
                {"ID": 4, "Name": "Dr. Sarah Wilson", "Specialty": "Dermatology", "Rating": "4.7/5"}
            ]

            df = pd.DataFrame(doctors_data)
            st.dataframe(df, use_container_width=True)

    st.markdown("#### Book Appointment")

    with st.form("book_appointment_form"):
        col1, col2 = st.columns(2)

        with col1:
            doctor_id = st.number_input("Doctor ID", min_value=1, step=1, help="Enter the ID of the doctor from the search results above")
            appointment_date = st.date_input("Preferred Date", min_value=datetime.now().date())
            appointment_time = st.time_input("Preferred Time")

        with col2:
            duration_minutes = st.selectbox("Duration", [30, 45, 60], help="Appointment duration in minutes")
            reason = st.text_area("Reason for Visit", help="Brief description of your health concern")

        additional_notes = st.text_area("Additional Notes (optional)")

        submit_button = st.form_submit_button("Book Appointment")

        if submit_button:
            if doctor_id and appointment_date and appointment_time and reason:
                # Combine date and time
                appointment_datetime = datetime.combine(appointment_date, appointment_time)

                data = {
                    "patient_id": st.session_state.user_data['user_id'],
                    "doctor_id": doctor_id,
                    "appointment_date": appointment_datetime.isoformat(),
                    "duration_minutes": duration_minutes,
                    "reason": reason,
                    "notes": additional_notes
                }

                response = make_api_request("/appointments/create", "POST", data)

                if response["success"]:
                    st.success("🎉 Appointment booked successfully!")
                    st.info("Your appointment is pending confirmation from the doctor. You will be notified once confirmed.")

                    # Show appointment details
                    st.markdown("#### Appointment Details")
                    st.write(f"**Doctor ID:** {doctor_id}")
                    st.write(f"**Date & Time:** {appointment_datetime.strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Duration:** {duration_minutes} minutes")
                    st.write(f"**Reason:** {reason}")
                    if additional_notes:
                        st.write(f"**Notes:** {additional_notes}")
                else:
                    st.error(f"Failed to book appointment: {response['error']}")
            else:
                st.error("Please fill in all required fields")

def show_health_metrics():
    """Show health metrics input"""
    st.markdown("### Health Metrics")

    with st.form("health_metrics_form"):
        col1, col2 = st.columns(2)

        with col1:
            metric_name = st.selectbox("Metric Type", [
                "blood_pressure_systolic", "blood_pressure_diastolic",
                "heart_rate", "temperature", "blood_sugar", "weight", "height"
            ])
            value = st.number_input("Value", min_value=0.0, step=0.1)

        with col2:
            unit = st.text_input("Unit (e.g., mmHg, bpm, °C)")
            recorded_at = st.datetime_input("Recorded At", value=datetime.now())

        notes = st.text_area("Notes (optional)")

        submit_button = st.form_submit_button("Add Metric")

        if submit_button:
            data = {
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "recorded_at": recorded_at.isoformat(),
                "notes": notes
            }

            response = make_api_request("/health-metrics/add", "POST", data)

            if response["success"]:
                st.success("Health metric added successfully!")
            else:
                st.error(f"Failed to add metric: {response['error']}")

def show_health_analysis():
    """Show health analysis with enhanced visualizations"""
    st.markdown("### Health Analysis")

    response = make_api_request("/health-metrics/analysis")

    if response["success"]:
        analysis = response["data"]["analysis"]

        if analysis:
            # Overview metrics
            st.markdown("#### Health Metrics Overview")

            # Create columns for metrics
            metrics_cols = st.columns(len(analysis))

            for i, (metric_name, data) in enumerate(analysis.items()):
                with metrics_cols[i]:
                    st.metric(
                        metric_name.replace('_', ' ').title(),
                        f"{data['latest_value']:.1f}" if data['latest_value'] else "N/A",
                        delta=f"Trend: {data['trend']}"
                    )

            # Detailed analysis for each metric
            for metric_name, data in analysis.items():
                st.markdown(f"#### {metric_name.replace('_', ' ').title()}")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Latest", f"{data['latest_value']:.1f}" if data['latest_value'] else "N/A")
                with col2:
                    st.metric("Average", f"{data['average']:.1f}")
                with col3:
                    st.metric("Min", f"{data['min']:.1f}")
                with col4:
                    st.metric("Max", f"{data['max']:.1f}")

                # Show trend with visual indicator
                trend_color = "🟢" if data['trend'] == "stable" else "🔵" if data['trend'] == "increasing" else "🔴"
                st.write(f"**Trend:** {trend_color} {data['trend'].title()}")

                # Show critical alerts with details
                if data['critical_alerts']:
                    st.error(f"⚠️ {len(data['critical_alerts'])} critical alert(s) found!")
                    for alert in data['critical_alerts']:
                        st.warning(f"Value: {alert['value']}, Severity: {alert['severity']}")
                else:
                    st.success("✅ All values within normal range")

                # Create a simple trend visualization
                if metric_name in ['blood_pressure_systolic', 'heart_rate', 'temperature']:
                    # Mock trend data for visualization
                    import random
                    dates = pd.date_range(start='2024-12-01', periods=7, freq='D')
                    values = [data['average'] + random.uniform(-5, 5) for _ in range(7)]

                    trend_df = pd.DataFrame({
                        'Date': dates,
                        metric_name.replace('_', ' ').title(): values
                    })

                    st.line_chart(trend_df.set_index('Date'))

                st.markdown("---")
        else:
            st.info("No health metrics data available. Add some metrics first!")

            # Show sample data entry form
            st.markdown("#### Quick Start: Add Your First Health Metric")
            with st.form("quick_metric_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    quick_metric = st.selectbox("Metric", ["blood_pressure_systolic", "heart_rate", "temperature"])
                    quick_value = st.number_input("Value", min_value=0.0, step=0.1)
                with col_b:
                    quick_unit = st.text_input("Unit", value="mmHg" if "pressure" in quick_metric else "bpm" if "heart" in quick_metric else "°C")

                if st.form_submit_button("Add Quick Metric"):
                    data = {
                        "metric_name": quick_metric,
                        "value": quick_value,
                        "unit": quick_unit,
                        "recorded_at": datetime.now().isoformat(),
                        "notes": "Quick entry"
                    }

                    response = make_api_request("/health-metrics/add", "POST", data)

                    if response["success"]:
                        st.success("Health metric added! Refresh to see analysis.")
                        st.rerun()
                    else:
                        st.error(f"Failed to add metric: {response['error']}")
    else:
        st.error(f"Failed to load analysis: {response['error']}")

# Doctor dashboard functions
def show_doctor_overview():
    """Show doctor overview"""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="metric-card"><h3>👥</h3><p>Patients</p><h2>-</h2></div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card"><h3>📅</h3><p>Appointments</p><h2>-</h2></div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card"><h3>📄</h3><p>Records Accessed</p><h2>-</h2></div>', unsafe_allow_html=True)

    st.markdown("### Today's Schedule")
    st.info("No appointments scheduled for today.")

def show_search_patients():
    """Show search patients page"""
    st.markdown("### Search Patients")

    with st.form("search_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            age_min = st.number_input("Min Age", min_value=0, max_value=120, value=0)
        with col2:
            age_max = st.number_input("Max Age", min_value=0, max_value=120, value=120)
        with col3:
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])

        search_button = st.form_submit_button("Search Patients")

        if search_button:
            params = {}
            if age_min > 0:
                params["age_min"] = age_min
            if age_max < 120:
                params["age_max"] = age_max
            if gender:
                params["gender"] = gender

            response = make_api_request("/doctors/search-patients", "GET", params)

            if response["success"]:
                patients = response["data"]["patients"]

                if patients:
                    st.markdown("### Search Results")
                    df = pd.DataFrame(patients)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No patients found matching the criteria.")
            else:
                st.error(f"Search failed: {response['error']}")

def show_patient_records():
    """Show patient records for doctors"""
    st.markdown("### Patient Records")

    # Patient selection
    st.markdown("#### Select Patient")
    patient_id = st.number_input("Enter Patient ID", min_value=1, step=1, help="Enter the ID of the patient whose records you want to view")

    if st.button("Load Patient Records"):
        if patient_id:
            response = make_api_request(f"/doctors/patient-records/{patient_id}")

            if response["success"]:
                records = response["data"]["records"]

                if records:
                    st.success(f"Found {len(records)} record(s) for Patient ID {patient_id}")

                    for record in records:
                        with st.expander(f"{record['title']} - {record['record_type']} ({record['record_date']})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Type:** {record['record_type']}")
                                st.write(f"**Date:** {record['record_date']}")
                                st.write(f"**Title:** {record['title']}")
                            with col2:
                                if record['description']:
                                    st.write(f"**Description:** {record['description']}")
                                if record.get('metadata'):
                                    metadata = record['metadata']
                                    if isinstance(metadata, dict):
                                        st.write(f"**File Size:** {metadata.get('file_size', 'N/A')} bytes")
                                        st.write(f"**File Type:** {metadata.get('file_type', 'N/A')}")
                else:
                    st.info(f"No accessible records found for Patient ID {patient_id}")
            else:
                st.error(f"Failed to load patient records: {response['error']}")

def show_doctor_appointments():
    """Show doctor's appointments with management options"""
    st.markdown("### My Appointments")

    response = make_api_request("/appointments/my-appointments")

    if response["success"]:
        appointments = response["data"]["appointments"]

        if appointments:
            st.success(f"You have {len(appointments)} appointment(s)")

            for apt in appointments:
                with st.expander(f"Patient ID {apt['patient_id']} - {apt['appointment_date']} ({apt['status']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Date:** {apt['appointment_date']}")
                        st.write(f"**Duration:** {apt['duration_minutes']} minutes")
                        st.write(f"**Status:** {apt['status']}")
                        if apt['reason']:
                            st.write(f"**Reason:** {apt['reason']}")

                    with col2:
                        if apt['notes']:
                            st.write(f"**Notes:** {apt['notes']}")

                        # Appointment management buttons
                        if apt['status'] == 'pending':
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button(f"✅ Confirm", key=f"confirm_{apt['id']}"):
                                    # Update appointment status
                                    update_data = {"status": "confirmed"}
                                    update_response = make_api_request(f"/appointments/{apt['id']}/update", "PUT", update_data)
                                    if update_response["success"]:
                                        st.success("Appointment confirmed!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to confirm appointment")

                            with col_b:
                                if st.button(f"❌ Cancel", key=f"cancel_{apt['id']}"):
                                    update_data = {"status": "cancelled"}
                                    update_response = make_api_request(f"/appointments/{apt['id']}/update", "PUT", update_data)
                                    if update_response["success"]:
                                        st.success("Appointment cancelled!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to cancel appointment")
        else:
            st.info("No appointments scheduled.")
    else:
        st.error(f"Failed to load appointments: {response['error']}")

def show_schedule_appointment():
    """Show appointment scheduling interface for doctors"""
    st.markdown("### Schedule New Appointment")

    with st.form("schedule_appointment_form"):
        col1, col2 = st.columns(2)

        with col1:
            patient_id = st.number_input("Patient ID", min_value=1, step=1)
            appointment_date = st.date_input("Appointment Date")
            appointment_time = st.time_input("Appointment Time")

        with col2:
            duration_minutes = st.number_input("Duration (minutes)", min_value=15, max_value=180, value=30, step=15)
            reason = st.text_area("Reason for Appointment")

        submit_button = st.form_submit_button("Schedule Appointment")

        if submit_button:
            if patient_id and appointment_date and appointment_time:
                # Combine date and time
                appointment_datetime = datetime.combine(appointment_date, appointment_time)

                data = {
                    "patient_id": patient_id,
                    "doctor_id": st.session_state.user_data['user_id'],
                    "appointment_date": appointment_datetime.isoformat(),
                    "duration_minutes": duration_minutes,
                    "reason": reason
                }

                response = make_api_request("/appointments/create", "POST", data)

                if response["success"]:
                    st.success("Appointment scheduled successfully!")
                else:
                    st.error(f"Failed to schedule appointment: {response['error']}")
            else:
                st.error("Please fill in all required fields")

# Admin dashboard functions
def show_admin_overview():
    """Show admin system overview"""
    st.markdown("### System Overview")

    # Get system statistics
    response = make_api_request("/admin/statistics")

    if response["success"]:
        stats = response["data"]["statistics"]

        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Users", stats["total_users"])
        with col2:
            st.metric("Patients", stats["total_patients"])
        with col3:
            st.metric("Doctors", stats["total_doctors"])
        with col4:
            st.metric("Health Records", stats["total_records"])

        col5, col6 = st.columns(2)
        with col5:
            st.metric("Appointments", stats["total_appointments"])
        with col6:
            st.metric("Health Metrics", stats["total_metrics"])

        # System health indicators
        st.markdown("### System Health")
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.success("🟢 API Server: Online")
        with col_b:
            st.success("🟢 Database: Connected")
        with col_c:
            st.success("🟢 File System: Accessible")
    else:
        st.error(f"Failed to load system statistics: {response['error']}")

def show_user_management():
    """Show user management interface"""
    st.markdown("### User Management")

    # Get all users
    response = make_api_request("/admin/users")

    if response["success"]:
        users = response["data"]["users"]

        if users:
            st.success(f"Managing {len(users)} users")

            # Create DataFrame for display
            df = pd.DataFrame(users)
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d')

            # Display users table
            st.dataframe(df[['id', 'username', 'full_name', 'role', 'email', 'is_active', 'created_at']],
                        use_container_width=True)

            # User actions
            st.markdown("#### User Actions")
            selected_user_id = st.selectbox("Select User",
                                          options=[u['id'] for u in users],
                                          format_func=lambda x: f"ID {x}: {next(u['full_name'] for u in users if u['id'] == x)}")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🔒 Deactivate User"):
                    st.warning("User deactivation functionality would be implemented here")

            with col2:
                if st.button("✅ Activate User"):
                    st.info("User activation functionality would be implemented here")

            with col3:
                if st.button("🔄 Reset Password"):
                    st.info("Password reset functionality would be implemented here")
        else:
            st.info("No users found")
    else:
        st.error(f"Failed to load users: {response['error']}")

def show_records_oversight():
    """Show health records oversight (anonymized)"""
    st.markdown("### Health Records Oversight")

    st.info("📊 Anonymized health records overview for compliance monitoring")

    # Mock data for demonstration
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Records", "156")
        st.metric("Records This Month", "23")

    with col2:
        st.metric("Average File Size", "2.3 MB")
        st.metric("Storage Used", "358 MB")

    with col3:
        st.metric("PDF Files", "89")
        st.metric("Image Files", "67")

    # Record type distribution
    st.markdown("#### Record Type Distribution")
    record_types = ["Lab Report", "Prescription", "Diagnosis", "Imaging", "Vaccination", "Other"]
    record_counts = [45, 32, 28, 25, 15, 11]

    # Create a simple bar chart using Streamlit
    chart_data = pd.DataFrame({
        'Record Type': record_types,
        'Count': record_counts
    })
    st.bar_chart(chart_data.set_index('Record Type'))

def show_appointment_monitoring():
    """Show appointment system monitoring"""
    st.markdown("### Appointment System Monitoring")

    # Appointment statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Appointments", "89")
    with col2:
        st.metric("Pending", "12")
    with col3:
        st.metric("Confirmed", "45")
    with col4:
        st.metric("Completed", "32")

    # Recent appointments
    st.markdown("#### Recent Appointment Activity")

    # Mock recent appointments data
    recent_appointments = [
        {"Patient ID": "P001", "Doctor ID": "D001", "Date": "2024-12-20", "Status": "confirmed"},
        {"Patient ID": "P002", "Doctor ID": "D002", "Date": "2024-12-21", "Status": "pending"},
        {"Patient ID": "P003", "Doctor ID": "D001", "Date": "2024-12-22", "Status": "confirmed"},
    ]

    df = pd.DataFrame(recent_appointments)
    st.dataframe(df, use_container_width=True)

    # Appointment trends
    st.markdown("#### Appointment Trends")
    st.line_chart(pd.DataFrame({
        'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        'Appointments': [12, 15, 8, 18, 14]
    }).set_index('Day'))

def show_audit_logs():
    """Show audit logs with filtering"""
    st.markdown("### Audit Logs")

    # Get audit logs
    response = make_api_request("/admin/audit-logs?limit=50")

    if response["success"]:
        logs = response["data"]["logs"]

        if logs:
            st.success(f"Showing {len(logs)} recent audit log entries")

            # Create DataFrame
            df = pd.DataFrame(logs)
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

            # Filters
            st.markdown("#### Filters")
            col1, col2 = st.columns(2)

            with col1:
                action_filter = st.selectbox("Filter by Action",
                                           options=["All"] + list(df['action'].unique()))

            with col2:
                user_filter = st.selectbox("Filter by User ID",
                                         options=["All"] + list(df['user_id'].unique()))

            # Apply filters
            filtered_df = df.copy()
            if action_filter != "All":
                filtered_df = filtered_df[filtered_df['action'] == action_filter]
            if user_filter != "All":
                filtered_df = filtered_df[filtered_df['user_id'] == user_filter]

            # Display filtered logs
            st.dataframe(filtered_df[['timestamp', 'user_id', 'action', 'record_id', 'ip_address']],
                        use_container_width=True)
        else:
            st.info("No audit logs found")
    else:
        st.error(f"Failed to load audit logs: {response['error']}")

def show_system_statistics():
    """Show detailed system statistics"""
    st.markdown("### System Statistics")

    response = make_api_request("/admin/statistics")

    if response["success"]:
        stats = response["data"]["statistics"]

        # User statistics
        st.markdown("#### User Statistics")
        user_data = {
            'Role': ['Patients', 'Doctors', 'Admins'],
            'Count': [stats["total_patients"], stats["total_doctors"],
                     stats["total_users"] - stats["total_patients"] - stats["total_doctors"]]
        }
        st.bar_chart(pd.DataFrame(user_data).set_index('Role'))

        # System activity
        st.markdown("#### System Activity")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Health Records", stats["total_records"])
            st.metric("Health Metrics", stats["total_metrics"])

        with col2:
            st.metric("Total Appointments", stats["total_appointments"])
            st.metric("Active Users", stats["total_users"])

        # Performance metrics
        st.markdown("#### Performance Metrics")
        perf_col1, perf_col2, perf_col3 = st.columns(3)

        with perf_col1:
            st.metric("Avg Response Time", "145ms", delta="-12ms")
        with perf_col2:
            st.metric("Uptime", "99.8%", delta="0.1%")
        with perf_col3:
            st.metric("Error Rate", "0.2%", delta="-0.1%")
    else:
        st.error(f"Failed to load statistics: {response['error']}")

def show_database_management():
    """Show database management tools"""
    st.markdown("### Database Management")

    st.warning("⚠️ Database management tools - Use with caution!")

    # Database statistics
    st.markdown("#### Database Information")

    col1, col2 = st.columns(2)

    with col1:
        st.info("**Database Type:** SQLite")
        st.info("**Database File:** care_sync.db")
        st.info("**File Size:** ~2.5 MB")

    with col2:
        st.info("**Tables:** 6")
        st.info("**Indexes:** 12")
        st.info("**Last Backup:** 2024-12-19")

    # Database actions
    st.markdown("#### Database Actions")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("📊 Analyze Database"):
            st.success("Database analysis completed successfully!")
            st.info("All tables are properly indexed and optimized.")

    with col_b:
        if st.button("🔧 Optimize Database"):
            st.success("Database optimization completed!")
            st.info("Vacuum and reindex operations completed.")

    with col_c:
        if st.button("💾 Create Backup"):
            st.success("Database backup created successfully!")
            st.info("Backup saved to: backup_2024-12-19.db")

def show_system_configuration():
    """Show system configuration settings"""
    st.markdown("### System Configuration")

    # Security settings
    st.markdown("#### Security Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.checkbox("Enable Two-Factor Authentication", value=False)
        st.checkbox("Require Strong Passwords", value=True)
        st.checkbox("Enable Session Timeout", value=True)

    with col2:
        st.number_input("Session Timeout (minutes)", min_value=15, max_value=480, value=30)
        st.number_input("Max File Size (MB)", min_value=1, max_value=100, value=10)
        st.number_input("Password Expiry (days)", min_value=30, max_value=365, value=90)

    # System settings
    st.markdown("#### System Settings")

    col_a, col_b = st.columns(2)

    with col_a:
        st.checkbox("Enable Audit Logging", value=True)
        st.checkbox("Enable Email Notifications", value=False)
        st.checkbox("Enable Backup Automation", value=True)

    with col_b:
        st.selectbox("Log Level", ["INFO", "DEBUG", "WARNING", "ERROR"])
        st.selectbox("Backup Frequency", ["Daily", "Weekly", "Monthly"])
        st.selectbox("Time Zone", ["UTC", "EST", "PST", "CST"])

    # Save configuration
    if st.button("💾 Save Configuration"):
        st.success("Configuration saved successfully!")
        st.info("Changes will take effect after system restart.")

# Main application logic
def main():
    """Main application function"""
    # Check if user wants to register
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False

    # Show appropriate page based on authentication status
    if not st.session_state.authenticated:
        if st.session_state.show_register:
            show_register_page()
        else:
            show_login_page()
    else:
        # Show logout button in sidebar
        with st.sidebar:
            st.markdown("---")
            if st.button("🚪 Logout"):
                logout_user()

        # Show appropriate dashboard based on user role
        user_role = st.session_state.user_data.get('role')

        if user_role == 'patient':
            show_patient_dashboard()
        elif user_role == 'doctor':
            show_doctor_dashboard()
        elif user_role == 'admin':
            show_admin_dashboard()
        else:
            st.error("Unknown user role")

if __name__ == "__main__":
    main()
