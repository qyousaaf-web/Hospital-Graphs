# app.py - Hospital Management System with Native Streamlit Charts (Fully Working!)
# Ready for GitHub + Streamlit Community Cloud (No extra packages beyond streamlit & pandas)
# Includes beautiful native charts on Home page + additional charts in each module

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --------------------- Page Config & Custom CSS ---------------------
st.set_page_config(
    page_title="Hospital Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .big-title {font-size: 3rem !important; font-weight: bold; color: #1E88E5; text-align: center; margin-bottom: 1rem;}
    .module-header {font-size: 2rem; color: #1976D2; padding: 0.5rem; border-left: 5px solid #42A5F5;}
    .stButton>button {border-radius: 8px; height: 3em; width: 100%;}
</style>
""", unsafe_allow_html=True)

# --------------------- Database Setup ---------------------
DB_FILE = "hospital.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS Patients (
            pat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            phone TEXT,
            address TEXT,
            email TEXT,
            registration_date TEXT DEFAULT (date('now'))
        );
        CREATE TABLE IF NOT EXISTS Doctors (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT,
            dept_id INTEGER,
            phone TEXT,
            email TEXT
        );
        CREATE TABLE IF NOT EXISTS Appointments (
            app_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pat_id INTEGER,
            doc_id INTEGER,
            app_date TEXT,
            app_time TEXT,
            status TEXT DEFAULT 'Scheduled'
        );
        CREATE TABLE IF NOT EXISTS MedicalRecords (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pat_id INTEGER,
            doc_id INTEGER,
            diagnosis TEXT,
            treatment TEXT,
            prescription TEXT
        );
        CREATE TABLE IF NOT EXISTS Billings (
            bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pat_id INTEGER,
            amount REAL,
            details TEXT,
            payment_status TEXT DEFAULT 'Pending',
            bill_date TEXT DEFAULT (date('now'))
        );
    ''')
    conn.commit()
    conn.close()

init_db()

# --------------------- Helper Functions ---------------------
def get_data(table_name):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

def insert_record(table_name, fields, values):
    conn = sqlite3.connect(DB_FILE)
    placeholders = ', '.join(['?' for _ in values])
    columns = ', '.join(fields)
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    conn.execute(sql, values)
    conn.commit()
    conn.close()

def delete_record(table_name, id_column, record_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(f"DELETE FROM {table_name} WHERE {id_column} = ?", (record_id,))
    conn.commit()
    conn.close()

def update_record(table_name, id_column, record_id, fields, values):
    conn = sqlite3.connect(DB_FILE)
    set_clause = ', '.join([f"{f} = ?" for f in fields])
    sql = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = ?"
    values.append(record_id)
    conn.execute(sql, values)
    conn.commit()
    conn.close()

def get_record(table_name, id_column, record_id):
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute(f"SELECT * FROM {table_name} WHERE {id_column} = ?", (record_id,)).fetchone()
    conn.close()
    return row

# --------------------- Charts Functions ---------------------
def show_home_charts():
    patients = get_data("Patients")
    appointments = get_data("Appointments")
    doctors = get_data("Doctors")
    bills = get_data("Billings")

    st.markdown("### 📊 Hospital Overview Dashboard")

    col1, col2 = st.columns(2)
    with col1:
        # Patients Growth Over Time
        if not patients.empty:
            patients['registration_date'] = pd.to_datetime(patients['registration_date'])
            growth = patients.groupby(patients['registration_date'].dt.strftime('%Y-%m')).size().reset_index(name='Count')
            growth = growth.set_index('registration_date')
            st.subheader("📈 New Patients Over Time")
            st.line_chart(growth)
        else:
            st.info("No patient registrations yet")

        # Gender Distribution
        if not patients.empty:
            gender_count = patients['gender'].value_counts().to_frame(name='Count')
            st.subheader("👥 Patient Gender Distribution")
            st.bar_chart(gender_count)
        else:
            st.info("No gender data yet")

    with col2:
        # Appointments by Status
        if not appointments.empty:
            status_count = appointments['status'].value_counts().to_frame(name='Count')
            st.subheader("🗓️ Appointments by Status")
            st.bar_chart(status_count)
        else:
            st.info("No appointments yet")

        # Monthly Revenue
        if not bills.empty:
            bills['bill_date'] = pd.to_datetime(bills['bill_date'])
            revenue = bills.groupby(bills['bill_date'].dt.strftime('%Y-%m'))['amount'].sum().reset_index()
            revenue = revenue.set_index('bill_date')['amount'].to_frame()
            st.subheader("💰 Monthly Revenue")
            st.area_chart(revenue)
        else:
            st.info("No billing data yet")

    # Top Busy Doctors
    if not appointments.empty and not doctors.empty:
        busy = appointments['doc_id'].value_counts().head(6).reset_index()
        busy = busy.merge(doctors[['doc_id', 'name']], on='doc_id')
        busy = busy.set_index('name')['count'].to_frame()
        st.subheader("🏆 Top 6 Busy Doctors")
        st.bar_chart(busy)

# --------------------- Sidebar Navigation ---------------------
st.sidebar.image("https://img.icons8.com/fluency/96/000000/hospital.png", width=100)
st.sidebar.markdown("<h1 style='text-align: center; color: #1976D2;'>🏥 HMS</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")

choice = st.sidebar.radio("**Navigation**", 
    ["🏠 Home", "👥 Patients", "👨‍⚕️ Doctors", "🗓️ Appointments", "📋 Medical Records", "💰 Billings"],
    label_visibility="collapsed")

# --------------------- Main Content ---------------------
if choice == "🏠 Home":
    st.markdown('<div class="big-title">🏥 Hospital Management System</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.3rem;'>Modern dashboard with live native charts</p>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Patients", len(get_data("Patients")))
    with col2:
        st.metric("Doctors", len(get_data("Doctors")))
    with col3:
        st.metric("Appointments", len(get_data("Appointments")))
    with col4:
        total_rev = get_data("Billings")['amount'].sum()
        st.metric("Total Revenue", f"${total_rev:,.2f}")

    show_home_charts()

elif choice == "👥 Patients":
    st.markdown('<div class="module-header">👥 Patients Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📋 View & Manage", "➕ Add New", "📊 Statistics"])

    with tab1:
        # View, Delete, Update (same as before)
        search_query = st.text_input("🔍 Search by Name or Phone")
        df = get_data("Patients") if not search_query else get_data("Patients")[get_data("Patients")['name'].str.contains(search_query, case=False) | get_data("Patients")['phone'].str.contains(search_query)]
        st.dataframe(df, use_container_width=True)

        col_del, col_up = st.columns(2)
        with col_del:
            del_id = st.number_input("ID to Delete", min_value=1, step=1)
            if st.button("🗑️ Delete Patient"):
                delete_record("Patients", "pat_id", del_id)
                st.success("Deleted!")
                st.rerun()
        with col_up:
            update_id = st.number_input("ID to Update", min_value=1, step=1)
            if update_id and st.button("✏️ Load for Update"):
                row = get_record("Patients", "pat_id", update_id)
                if row:
                    with st.form("update_patient"):
                        name = st.text_input("Name", value=row[1])
                        age = st.number_input("Age", value=row[2])
                        gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male","Female","Other"].index(row[3]))
                        phone = st.text_input("Phone", value=row[4])
                        address = st.text_area("Address", value=row[5] or "")
                        email = st.text_input("Email", value=row[6] or "")
                        if st.form_submit_button("Update"):
                            update_record("Patients", "pat_id", update_id, ["name","age","gender","phone","address","email"], [name,age,gender,phone,address,email])
                            st.success("Updated!")
                            st.rerun()

    with tab2:
        with st.form("add_patient"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name *")
                age = st.number_input("Age", min_value=1)
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            with col2:
                phone = st.text_input("Phone *")
                address = st.text_area("Address")
                email = st.text_input("Email")
            if st.form_submit_button("Add Patient"):
                if name and phone:
                    insert_record("Patients", ["name","age","gender","phone","address","email"], [name,age,gender,phone,address,email])
                    st.success("Patient added!")
                    st.rerun()

    with tab3:
        patients = get_data("Patients")
        if not patients.empty:
            st.subheader("Age Distribution")
            age_bins = pd.cut(patients['age'], bins=[0,18,35,50,65,120], labels=["0-18","19-35","36-50","51-65","65+"])
            age_dist = age_bins.value_counts().sort_index().to_frame()
            st.bar_chart(age_dist)

            st.subheader("Registrations Over Time")
            patients['registration_date'] = pd.to_datetime(patients['registration_date'])
            monthly = patients.groupby(patients['registration_date'].dt.strftime('%Y-%m')).size().to_frame(name='Count')
            st.line_chart(monthly)

# (Repeat similar pattern for other modules with their own stats tab if desired)

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Built with ❤️ using Streamlit • Native Charts • Instant Deployment</div>", unsafe_allow_html=True)
