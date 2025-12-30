import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# ================= CONFIG =================
st.set_page_config(page_title="Hospital System", page_icon="🏥", layout="wide")
DB = "hospital.db"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS Users(
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    );

    CREATE TABLE IF NOT EXISTS Patients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        cnic TEXT UNIQUE,
        phone TEXT
    );

    CREATE TABLE IF NOT EXISTS Doctors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        cnic TEXT UNIQUE,
        specialty TEXT
    );

    CREATE TABLE IF NOT EXISTS Appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient TEXT,
        doctor TEXT,
        date TEXT,
        time TEXT,
        status TEXT
    );
    """)
    c.execute("INSERT OR IGNORE INTO Users VALUES ('admin','admin123','Admin')")
    conn.commit()
    conn.close()

init_db()

# ================= HELPERS =================
def query(sql, params=()):
    conn = sqlite3.connect(DB)
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df

def execute(sql, params=()):
    conn = sqlite3.connect(DB)
    conn.execute(sql, params)
    conn.commit()
    conn.close()

def valid_cnic(cnic):
    return re.match(r"^\d{5}-\d{7}-\d$", cnic)

# ================= LOGIN =================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        user = query("SELECT * FROM Users WHERE username=? AND password=?", (u, p))
        if not user.empty:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ================= SIDEBAR =================
menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Patients", "Doctors", "Appointments"]
)

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.title("📊 Analytics")

    df = query("SELECT * FROM Appointments")
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        year = st.selectbox("Year", sorted(df["date"].dt.year.unique()))
        df = df[df["date"].dt.year == year]

        monthly = df.groupby(df["date"].dt.month).size().reset_index(name="Count")
        fig = px.line(monthly, x="date", y="Count", markers=True,
                      title="Monthly Appointment Trend")
        st.plotly_chart(fig, use_container_width=True)

        doc_fig = px.bar(df["doctor"].value_counts().reset_index(),
                         x="index", y="doctor",
                         title="Doctor-wise Appointments")
        st.plotly_chart(doc_fig, use_container_width=True)
    else:
        st.info("No data yet")

# ================= PATIENTS =================
elif menu == "Patients":
    st.title("👥 Patients")

    search = st.text_input("Search by CNIC or Name")
    if search:
        st.dataframe(query(
            "SELECT * FROM Patients WHERE cnic LIKE ? OR name LIKE ?",
            (f"%{search}%", f"%{search}%")
        ))
    else:
        st.dataframe(query("SELECT * FROM Patients"))

    with st.form("add_patient"):
        name = st.text_input("Name")
        cnic = st.text_input("CNIC (xxxxx-xxxxxxx-x)")
        phone = st.text_input("Phone")
        if st.form_submit_button("Add"):
            if not valid_cnic(cnic):
                st.error("Invalid CNIC")
            else:
                execute("INSERT INTO Patients VALUES(NULL,?,?,?)",
                        (name, cnic, phone))
                st.success("Patient added")
                st.rerun()

# ================= DOCTORS =================
elif menu == "Doctors":
    st.title("👨‍⚕️ Doctors")

    search = st.text_input("Search by CNIC or Name")
    if search:
        st.dataframe(query(
            "SELECT * FROM Doctors WHERE cnic LIKE ? OR name LIKE ?",
            (f"%{search}%", f"%{search}%")
        ))
    else:
        st.dataframe(query("SELECT * FROM Doctors"))

    with st.form("add_doctor"):
        name = st.text_input("Name")
        cnic = st.text_input("CNIC")
        spec = st.text_input("Specialty")
        if st.form_submit_button("Add"):
            if not valid_cnic(cnic):
                st.error("Invalid CNIC")
            else:
                execute("INSERT INTO Doctors VALUES(NULL,?,?,?)",
                        (name, cnic, spec))
                st.success("Doctor added")
                st.rerun()

# ================= APPOINTMENTS =================
elif menu == "Appointments":
    st.title("🗓️ Appointments")

    patients = query("SELECT name, cnic FROM Patients")
    doctors = query("SELECT name, cnic FROM Doctors")

    p = st.selectbox("Patient",
                     (patients["name"] + " | " + patients["cnic"]).tolist())
    d = st.selectbox("Doctor",
                     (doctors["name"] + " | " + doctors["cnic"]).tolist())
    date = st.date_input("Date")
    time = st.time_input("Time")
    status = st.selectbox("Status", ["Scheduled", "Completed", "Cancelled"])

    if st.button("Book Appointment"):
        execute("INSERT INTO Appointments VALUES(NULL,?,?,?,?,?)",
                (p, d, str(date), str(time), status))
        st.success("Appointment booked")
        st.rerun()

    st.dataframe(query("SELECT * FROM Appointments"))

    st.subheader("🧾 PDF Slip")
    aid = st.number_input("Appointment ID", min_value=1)

    if st.button("Generate PDF"):
        row = query("SELECT * FROM Appointments WHERE id=?", (aid,))
        if row.empty:
            st.error("Invalid ID")
        else:
            file = f"appointment_{aid}.pdf"
            pdf = SimpleDocTemplate(file)
            styles = getSampleStyleSheet()
            pdf.build([
                Paragraph("<b>Appointment Slip</b>", styles["Title"]),
                Paragraph(f"Patient: {row.iloc[0]['patient']}", styles["Normal"]),
                Paragraph(f"Doctor: {row.iloc[0]['doctor']}", styles["Normal"]),
                Paragraph(f"Date: {row.iloc[0]['date']}", styles["Normal"]),
                Paragraph(f"Time: {row.iloc[0]['time']}", styles["Normal"]),
                Paragraph(f"Status: {row.iloc[0]['status']}", styles["Normal"])
            ])
            with open(file, "rb") as f:
                st.download_button("Download PDF", f, file)
