import streamlit as st
import pandas as pd
import sqlite3
import datetime
import io
import json
import urllib.parse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Page Configuration
st.set_page_config(
    page_title="BHARAT LIS - Pathology Management System",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# New Fresh Database File
DB_NAME = "bharat_lab_v2.db"

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Patients Table
    c.execute('''CREATE TABLE IF NOT EXISTS patients (
                    id TEXT PRIMARY KEY,
                    designation TEXT,
                    name TEXT,
                    age INTEGER,
                    age_type TEXT,
                    gender TEXT,
                    doctor TEXT,
                    rate_list TEXT,
                    dispatch_methods TEXT,
                    aadhaar TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    sample_status TEXT DEFAULT 'Sample Collected',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # Billing Table
    c.execute('''CREATE TABLE IF NOT EXISTS tests_billing (
                    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT,
                    test_name TEXT,
                    test_price REAL,
                    paid_amount REAL,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # All-Parameter Flexible Clinical Results Table (Stores dynamic JSON metrics)
    c.execute('''CREATE TABLE IF NOT EXISTS test_results_all (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT UNIQUE,
                    parameters_json TEXT,
                    status TEXT DEFAULT 'Verified',
                    verified_by TEXT DEFAULT 'Dr. Pathologist (MD, Pathology)',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # Doctors Table
    c.execute('''CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    commission REAL DEFAULT 15.0
                )''')

    # Inventory Table
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT,
                    category TEXT,
                    stock INTEGER,
                    unit TEXT,
                    expiry_date TEXT
                )''')
    
    c.execute("INSERT OR IGNORE INTO doctors (name, commission) VALUES ('Self / Direct', 0)")
    c.execute("INSERT OR IGNORE INTO doctors (name, commission) VALUES ('Dr. Sharma (MBBS, MD)', 15)")
    c.execute("INSERT OR IGNORE INTO doctors (name, commission) VALUES ('Dr. Rajesh Verma (Consultant)', 20)")
    
    c.execute("INSERT OR IGNORE INTO inventory (item_name, category, stock, unit, expiry_date) VALUES ('EDTA Tubes (Purple, 2ml)', 'Consumables', 250, 'Pcs', '2027-12-31')")
    c.execute("INSERT OR IGNORE INTO inventory (item_name, category, stock, unit, expiry_date) VALUES ('CBC Diluent 20L', 'Reagents', 4, 'Bottles', '2027-06-30')")
    c.execute("INSERT OR IGNORE INTO inventory (item_name, category, stock, unit, expiry_date) VALUES ('Plain Serum Vials (Red, 5ml)', 'Consumables', 180, 'Pcs', '2027-08-15')")
    
    conn.commit()
    conn.close()

init_db()

def generate_patient_id():
    date_part = datetime.datetime.now().strftime("%y%m%d")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM patients WHERE id LIKE ?", (f"{date_part}%",))
    cnt = c.fetchone()[0] + 1
    conn.close()
    return f"{date_part}{str(cnt).zfill(3)}"

def get_doctors():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM doctors")
    docs = [r[0] for r in c.fetchall()]
    conn.close()
    return docs

# BHARAT Red Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    .top-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff;
        padding: 12px 22px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 18px;
    }
    .bharat-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 4px;
        font-size: 24px;
        font-weight: 800;
        color: #DC2626;
        border-bottom: 1px solid #f1f5f9;
        margin-bottom: 12px;
    }
    .patient-id-badge {
        font-size: 18px;
        font-weight: 700;
        color: #0f172a;
        padding-top: 4px;
    }
    .dept-header {
        background-color: #FEF2F2;
        color: #991B1B;
        padding: 8px 14px;
        font-weight: 700;
        border-left: 4px solid #DC2626;
        border-radius: 4px;
        margin: 18px 0 12px 0;
    }
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
    }
    .stButton > button[kind="primary"] {
        background-color: #DC2626 !important;
        border-color: #DC2626 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Top Bar
st.markdown("""
<div class="top-header">
    <div style="display: flex; align-items: center; gap: 15px;">
        <span style="font-size: 22px; font-weight: 800; color: #DC2626;">// BHARAT</span>
        <span style="background: #FEF2F2; color: #DC2626; border: 1px solid #FCA5A5; padding: 2px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;">PREMIERE</span>
    </div>
    <div style="display: flex; align-items: center; gap: 20px; font-size: 13px; color: #475569;">
        <span>Branch: <b>BHARAT Diagnostic Centre</b></span>
        <span>Operator: <b>Admin</b></span>
        <span style="color: #16a34a; font-weight: 600;">● Cloud Connected</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-brand">// BHARAT</div>', unsafe_allow_html=True)
    menu = st.radio(
        "BHARAT Modules",
        [
            "New Registration",
            "Credent (Accession & Barcode)",
            "Analysis (Dashboard)",
            "Patient List",
            "Enter & Verify",
            "Billing & Invoicing",
            "Financial Analysis",
            "Tests & Rate List",
            "Smart Report",
            "Lab Management",
            "Inventory",
            "Lab Profile"
        ],
        label_visibility="collapsed"
    )

# ----------------- MODULE 1: NEW REGISTRATION -----------------
if menu == "New Registration":
    new_pid = generate_patient_id()
    
    st.markdown('<div class="bharat-card">', unsafe_allow_html=True)
    st.markdown("<h4 style='margin-top:0; color:#1e293b;'>Patient Registration</h4>", unsafe_allow_html=True)
    
    c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.2, 3, 1.2, 1.2, 2.5])
    with c1:
        st.markdown("<p style='font-size: 12px; color: #64748b; margin-bottom: 2px;'>Patient ID</p>", unsafe_allow_html=True)
        st.markdown(f"<div class='patient-id-badge'>{new_pid}</div>", unsafe_allow_html=True)
    with c2:
        designation = st.selectbox("Designation *", ["MR.", "MRS.", "MS.", "DR.", "BABY", "MASTER"])
    with c3:
        first_name = st.text_input("First Name *", placeholder="Patient Name")
    with c4:
        age = st.number_input("Age *", min_value=0, max_value=120, value=28)
    with c5:
        age_type = st.selectbox("Age Type *", ["Year", "Month", "Days"])
    with c6:
        gender = st.radio("Gender *", ["Male", "Female", "Other"], horizontal=True)

    st.markdown("<hr style='margin: 12px 0; border: none; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)

    r2_1, r2_2, r2_3, r2_4 = st.columns([2.5, 2, 3, 3])
    with r2_1:
        doc_list = get_doctors()
        doctor = st.selectbox("Referring Doctor", doc_list)
    with r2_2:
        rate_list = st.selectbox("Rate List Type", ["Main", "Corporate", "B2B Discount"])
    with r2_3:
        dispatch_methods = st.multiselect("Dispatch Methods", ["Email", "Hardcopy", "SMS", "WhatsApp"], default=["WhatsApp", "Hardcopy"])
    with r2_4:
        address = st.text_area("Address", placeholder="Patient Address", height=68)

    st.markdown("<hr style='margin: 12px 0; border: none; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)

    r3_1, r3_2, r3_3 = st.columns([2.5, 2.5, 3])
    with r3_1:
        aadhaar = st.text_input("Aadhaar number", placeholder="12-digit Aadhaar")
    with r3_2:
        phone = st.text_input("Phone Number (IN +91) *", placeholder="10-digit Phone")
    with r3_3:
        email = st.text_input("Email", placeholder="Email ID")

    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2 = st.columns([8, 2])
    with b2:
        btn_reg = st.button("Register Patient ➔", type="primary", use_container_width=True)

    if btn_reg:
        if not first_name or not phone:
            st.error("First Name aur Phone Number bharna zaroori hai.")
        else:
            conn = get_db()
            c = conn.cursor()
            c.execute('''INSERT INTO patients (id, designation, name, age, age_type, gender, doctor,
                            rate_list, dispatch_methods, aadhaar, phone, email, address, sample_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (new_pid, designation, first_name, int(age), age_type, gender, doctor,
                             rate_list, ",".join(dispatch_methods), aadhaar, phone, email, address, 'Sample Collected'))
            conn.commit()
            conn.close()
            st.success(f"Patient {new_pid} ({first_name}) successfully register ho gaya!")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 2: CREDENT (ACCESSION & BARCODE) -----------------
elif menu == "Credent (Accession & Barcode)":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Credent: Sample Accession & Barcode Tracking</h4>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, gender, age, sample_status FROM patients ORDER BY rowid DESC")
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        st.info("Koi patient data uplabdh nahi hai.")
    else:
        df_pts = pd.DataFrame(rows, columns=["ID", "Name", "Gender", "Age", "Status"])
        c1, c2 = st.columns([1.6, 1])
        with c1:
            st.dataframe(df_pts, use_container_width=True)
        with c2:
            sel_pid = st.selectbox("Select Patient ID", df_pts['ID'].tolist())
            barcode_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=BHARAT-{sel_pid}"
            st.image(barcode_url, caption=f"Sample Barcode: BHARAT-{sel_pid}")
            new_status = st.selectbox("Accession Status", ["Sample Collected", "Received at Lab", "In Processing", "Sample Rejected"])
            if st.button("Update Sample Status", type="primary"):
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE patients SET sample_status = ? WHERE id = ?", (new_status, sel_pid))
                conn.commit()
                conn.close()
                st.success("Status update ho gaya!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 3: ANALYSIS -----------------
elif menu == "Analysis (Dashboard)":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Laboratory Dashboard & Metrics</h4>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM patients")
    total_p = c.fetchone()[0]
    c.execute("SELECT SUM(paid_amount) FROM tests_billing")
    total_rev = c.fetchone()[0] or 0.0
    conn.close()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Patients", total_p)
    m2.metric("Average TAT", "1 Hour 15 Mins")
    m3.metric("Total Revenue", f"₹ {total_rev:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 4: PATIENT LIST -----------------
elif menu == "Patient List":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Patient Directory</h4>', unsafe_allow_html=True)
    q = st.text_input("🔍 Search Directory by Name / Phone / ID", "")
    conn = get_db()
    c = conn.cursor()
    if q:
        c.execute("SELECT id, name, age, gender, phone, doctor, sample_status FROM patients WHERE name LIKE ? OR phone LIKE ? OR id LIKE ?", (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        c.execute("SELECT id, name, age, gender, phone, doctor, sample_status FROM patients ORDER BY rowid DESC")
    data = c.fetchall()
    conn.close()
    
    if data:
        df = pd.DataFrame(data, columns=["ID", "Name", "Age", "Gender", "Phone", "Doctor", "Sample Status"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Koi patient nahi mila.")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 5: ENTER & VERIFY (ALL PARAMETERS INCLUDED) -----------------
elif menu == "Enter & Verify":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Clinical Results Entry - All Department Parameters</h4>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name FROM patients ORDER BY rowid DESC")
    pts_data = c.fetchall()
    conn.close()
    
    if not pts_data:
        st.info("Pehle 'New Registration' se patient register karein.")
    else:
        pt_dict = {row[0]: row[1] for row in pts_data}
        selected_pid = st.selectbox("Select Patient for Clinical Entry", list(pt_dict.keys()), format_func=lambda x: f"{x} - {pt_dict[x]}")
        
        # Pull existing results if previously saved
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT parameters_json, verified_by FROM test_results_all WHERE patient_id = ?", (selected_pid,))
        saved_row = c.fetchone()
        conn.close()
        
        saved_params = {}
        if saved_row and saved_row[0]:
            try:
                saved_params = json.loads(saved_row[0])
            except Exception:
                saved_params = {}

        tabs = st.tabs([
            "🩸 Hematology (CBC & ESR)",
            "🧪 Biochemistry & Sugar",
            "🫘 KFT / Kidney Panel",
            "🩺 LFT / Liver Panel",
            "🫀 Lipid & Cardiac",
            "🦋 Thyroid & Serology",
            "🔬 Urine Routine"
        ])
        
        results = {}

        # TAB 1: HEMATOLOGY
        with tabs[0]:
            st.markdown('<div class="dept-header">Complete Blood Count (CBC) with Differential & ESR</div>', unsafe_allow_html=True)
            h1, h2, h3 = st.columns(3)
            with h1:
                results["Hemoglobin (Hb)"] = st.text_input("Hemoglobin (Hb) [g/dL | 13.0 - 17.0]", value=str(saved_params.get("Hemoglobin (Hb)", "13.8")))
                results["Total Leucocyte Count (TLC/WBC)"] = st.text_input("Total WBC [cumm | 4000 - 11000]", value=str(saved_params.get("Total Leucocyte Count (TLC/WBC)", "6800")))
                results["Platelet Count"] = st.text_input("Platelets [Lakh/cumm | 1.5 - 4.5]", value=str(saved_params.get("Platelet Count", "2.40")))
                results["RBC Count"] = st.text_input("RBC Count [mil/cumm | 4.5 - 5.5]", value=str(saved_params.get("RBC Count", "4.8")))
                results["Packed Cell Volume (PCV/HCT)"] = st.text_input("PCV / Hematocrit [% | 40 - 50]", value=str(saved_params.get("Packed Cell Volume (PCV/HCT)", "42.5")))
            with h2:
                results["MCV"] = st.text_input("MCV [fL | 80 - 100]", value=str(saved_params.get("MCV", "88.0")))
                results["MCH"] = st.text_input("MCH [pg | 27 - 32]", value=str(saved_params.get("MCH", "29.2")))
                results["MCHC"] = st.text_input("MCHC [g/dL | 32 - 36]", value=str(saved_params.get("MCHC", "33.5")))
                results["RDW-CV"] = st.text_input("RDW-CV [% | 11.5 - 14.5]", value=str(saved_params.get("RDW-CV", "12.8")))
                results["ESR (Westergren)"] = st.text_input("ESR 1st Hour [mm/hr | 0 - 15]", value=str(saved_params.get("ESR (Westergren)", "10")))
            with h3:
                results["Neutrophils"] = st.text_input("Neutrophils [% | 40 - 75]", value=str(saved_params.get("Neutrophils", "64")))
                results["Lymphocytes"] = st.text_input("Lymphocytes [% | 20 - 45]", value=str(saved_params.get("Lymphocytes", "28")))
                results["Eosinophils"] = st.text_input("Eosinophils [% | 01 - 06]", value=str(saved_params.get("Eosinophils", "03")))
                results["Monocytes"] = st.text_input("Monocytes [% | 02 - 10]", value=str(saved_params.get("Monocytes", "05")))
                results["Basophils"] = st.text_input("Basophils [% | 00 - 01]", value=str(saved_params.get("Basophils", "00")))

        # TAB 2: BIOCHEMISTRY & SUGAR
        with tabs[1]:
            st.markdown('<div class="dept-header">Blood Glucose & Glycated Hemoglobin</div>', unsafe_allow_html=True)
            b1, b2 = st.columns(2)
            with b1:
                results["Blood Glucose (Fasting)"] = st.text_input("Blood Glucose - Fasting [mg/dL | 70 - 100]", value=str(saved_params.get("Blood Glucose (Fasting)", "92")))
                results["Blood Glucose (PP)"] = st.text_input("Blood Glucose - Post Prandial [mg/dL | < 140]", value=str(saved_params.get("Blood Glucose (PP)", "128")))
                results["Blood Glucose (Random)"] = st.text_input("Blood Glucose - Random [mg/dL | 70 - 140]", value=str(saved_params.get("Blood Glucose (Random)", "105")))
            with b2:
                results["HbA1c (Glycated Hb)"] = st.text_input("HbA1c [% | Non-diabetic: < 5.7]", value=str(saved_params.get("HbA1c (Glycated Hb)", "5.4")))
                results["Estimated Avg Glucose (eAG)"] = st.text_input("Estimated Avg Glucose [mg/dL | 90 - 120]", value=str(saved_params.get("Estimated Avg Glucose (eAG)", "108")))

        # TAB 3: KFT / RENAL
        with tabs[2]:
            st.markdown('<div class="dept-header">Kidney Function Test (KFT / RFT)</div>', unsafe_allow_html=True)
            k1, k2 = st.columns(2)
            with k1:
                results["Serum Urea"] = st.text_input("Blood Urea [mg/dL | 15 - 40]", value=str(saved_params.get("Serum Urea", "26.5")))
                results["Blood Urea Nitrogen (BUN)"] = st.text_input("BUN [mg/dL | 7 - 20]", value=str(saved_params.get("Blood Urea Nitrogen (BUN)", "12.4")))
                results["Serum Creatinine"] = st.text_input("Serum Creatinine [mg/dL | 0.6 - 1.2]", value=str(saved_params.get("Serum Creatinine", "0.95")))
            with k2:
                results["Serum Uric Acid"] = st.text_input("Serum Uric Acid [mg/dL | 3.5 - 7.2]", value=str(saved_params.get("Serum Uric Acid", "4.8")))
                results["Serum Calcium (Total)"] = st.text_input("Serum Calcium [mg/dL | 8.8 - 10.2]", value=str(saved_params.get("Serum Calcium (Total)", "9.4")))
                results["Serum Sodium (Na+)"] = st.text_input("Serum Sodium [mEq/L | 136 - 145]", value=str(saved_params.get("Serum Sodium (Na+)", "140")))

        # TAB 4: LFT / LIVER
        with tabs[3]:
            st.markdown('<div class="dept-header">Liver Function Test (LFT)</div>', unsafe_allow_html=True)
            l1, l2 = st.columns(2)
            with l1:
                results["Bilirubin Total"] = st.text_input("Serum Bilirubin Total [mg/dL | 0.2 - 1.2]", value=str(saved_params.get("Bilirubin Total", "0.8")))
                results["Bilirubin Direct"] = st.text_input("Serum Bilirubin Direct [mg/dL | 0.0 - 0.3]", value=str(saved_params.get("Bilirubin Direct", "0.2")))
                results["SGOT / AST"] = st.text_input("SGOT / AST [U/L | 5 - 40]", value=str(saved_params.get("SGOT / AST", "28")))
                results["SGPT / ALT"] = st.text_input("SGPT / ALT [U/L | 5 - 45]", value=str(saved_params.get("SGPT / ALT", "32")))
            with l2:
                results["Alkaline Phosphatase (ALP)"] = st.text_input("Alkaline Phosphatase [U/L | 30 - 120]", value=str(saved_params.get("Alkaline Phosphatase (ALP)", "75")))
                results["Total Protein"] = st.text_input("Total Protein [g/dL | 6.0 - 8.3]", value=str(saved_params.get("Total Protein", "7.2")))
                results["Serum Albumin"] = st.text_input("Serum Albumin [g/dL | 3.5 - 5.0]", value=str(saved_params.get("Serum Albumin", "4.2")))
                results["A/G Ratio"] = st.text_input("A/G Ratio [1.2 - 2.0]", value=str(saved_params.get("A/G Ratio", "1.4")))

        # TAB 5: LIPID & CARDIAC
        with tabs[4]:
            st.markdown('<div class="dept-header">Lipid Profile & Inflammatory Markers</div>', unsafe_allow_html=True)
            lp1, lp2 = st.columns(2)
            with lp1:
                results["Total Cholesterol"] = st.text_input("Total Cholesterol [mg/dL | < 200]", value=str(saved_params.get("Total Cholesterol", "172")))
                results["Triglycerides"] = st.text_input("Serum Triglycerides [mg/dL | < 150]", value=str(saved_params.get("Triglycerides", "135")))
                results["HDL Cholesterol (Good)"] = st.text_input("HDL Cholesterol [mg/dL | > 40]", value=str(saved_params.get("HDL Cholesterol (Good)", "46")))
            with lp2:
                results["LDL Cholesterol (Bad)"] = st.text_input("LDL Cholesterol [mg/dL | < 100]", value=str(saved_params.get("LDL Cholesterol (Bad)", "99")))
                results["VLDL Cholesterol"] = st.text_input("VLDL Cholesterol [mg/dL | 10 - 30]", value=str(saved_params.get("VLDL Cholesterol", "27")))
                results["CRP (Quantitative)"] = st.text_input("C-Reactive Protein (CRP) [mg/L | < 6.0]", value=str(saved_params.get("CRP (Quantitative)", "2.1")))

        # TAB 6: THYROID & SEROLOGY
        with tabs[5]:
            st.markdown('<div class="dept-header">Thyroid Profile & Serology / Infections</div>', unsafe_allow_html=True)
            th1, th2 = st.columns(2)
            with th1:
                results["Total T3 (Triiodothyronine)"] = st.text_input("Total T3 [ng/dL | 60 - 200]", value=str(saved_params.get("Total T3 (Triiodothyronine)", "120")))
                results["Total T4 (Thyroxine)"] = st.text_input("Total T4 [µg/dL | 4.5 - 12.0]", value=str(saved_params.get("Total T4 (Thyroxine)", "8.2")))
                results["TSH (Ultrasensitive)"] = st.text_input("TSH 3rd Gen [µIU/mL | 0.35 - 5.50]", value=str(saved_params.get("TSH (Ultrasensitive)", "2.45")))
            with th2:
                results["Widal Test (Typhoid)"] = st.selectbox("Widal Slide/Tube Test", ["Negative (< 1:80)", "Positive (O: 1:160, H: 1:160)", "Positive (O: 1:320, H: 1:320)"], index=0)
                results["Dengue NS1 Antigen"] = st.selectbox("Dengue NS1 Antigen", ["Negative", "Positive"], index=0)
                results["Malaria Antigen (Pv/Pf)"] = st.selectbox("Malaria Antigen Rapid", ["Negative", "Plasmodium Vivax Positive", "Plasmodium Falciparum Positive"], index=0)

        # TAB 7: URINE ROUTINE
        with tabs[6]:
            st.markdown('<div class="dept-header">Urine Routine & Microscopic Examination</div>', unsafe_allow_html=True)
            u1, u2 = st.columns(2)
            with u1:
                results["Urine Color & Appearance"] = st.text_input("Color / Appearance", value=str(saved_params.get("Urine Color & Appearance", "Pale Yellow, Clear")))
                results["Urine Reaction (pH)"] = st.text_input("Reaction (pH) [4.5 - 8.0]", value=str(saved_params.get("Urine Reaction (pH)", "6.0")))
                results["Urine Specific Gravity"] = st.text_input("Specific Gravity [1.005 - 1.030]", value=str(saved_params.get("Urine Specific Gravity", "1.015")))
                results["Urine Protein / Albumin"] = st.selectbox("Urine Protein / Albumin", ["Nil / Negative", "Trace", "+ (30 mg/dL)", "++ (100 mg/dL)", "+++ (300 mg/dL)"], index=0)
            with u2:
                results["Urine Sugar / Glucose"] = st.selectbox("Urine Sugar", ["Nil / Negative", "Trace", "+ (0.5%)", "++ (1.0%)"], index=0)
                results["Urine Pus Cells"] = st.text_input("Pus Cells [/HPF | 2 - 4]", value=str(saved_params.get("Urine Pus Cells", "2 - 3 / HPF")))
                results["Urine Epithelial Cells"] = st.text_input("Epithelial Cells [/HPF | 1 - 3]", value=str(saved_params.get("Urine Epithelial Cells", "1 - 2 / HPF")))
                results["Urine RBCs"] = st.text_input("R.B.C [/HPF | Nil]", value=str(saved_params.get("Urine RBCs", "Nil")))

        st.markdown("<br>", unsafe_allow_html=True)
        v1, v2 = st.columns([2, 1])
        with v1:
            approver = st.selectbox("Verifying Pathologist", [
                "Dr. Pathologist (MD, DNB Pathology)",
                "Dr. Rajesh Verma (MBBS, DCP, Consultant)",
                "Dr. Senior Resident (Pathology)"
            ])
        with v2:
            st.write("")
            st.write("")
            btn_save_all = st.button("Save & Lock All Parameters ➔", type="primary", use_container_width=True)

        if btn_save_all:
            conn = get_db()
            c = conn.cursor()
            json_blob = json.dumps(results)
            c.execute('''INSERT OR REPLACE INTO test_results_all (patient_id, parameters_json, status, verified_by)
                         VALUES (?, ?, ?, ?)''', (selected_pid, json_blob, "Approved", approver))
            conn.commit()
            conn.close()
            st.success(f"Saare clinical parameters Patient ID {selected_pid} ke liye verify hokar save ho gaye!")

    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 6: BILLING & INVOICING -----------------
elif menu == "Billing & Invoicing":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Billing & UPI Invoicing</h4>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, phone FROM patients ORDER BY rowid DESC")
    b_pts = c.fetchall()
    conn.close()
    
    if not b_pts:
        st.info("Pehle 'New Registration' module se patient register karein.")
    else:
        b_dict = {r[0]: f"{r[0]} - {r[1]} ({r[2]})" for r in b_pts}
        pid = st.selectbox("Select Patient", list(b_dict.keys()), format_func=lambda x: b_dict[x])
        
        test_prices = {
            "Complete Blood Count (CBC)": 350, "Hemoglobin (Hb Only)": 80, "ESR": 100, "Platelet Count": 120, "Blood Group & Rh": 100,
            "Blood Glucose - Fasting": 80, "Blood Glucose - PP": 80, "HbA1c (Glycated Hemoglobin)": 450,
            "Liver Function Test (LFT)": 650, "Kidney Function Test (KFT / RFT)": 600, "Serum Creatinine": 150, "Serum Uric Acid": 180,
            "Lipid Profile (Full Panel)": 700, "Thyroid Profile Total (T3, T4, TSH)": 500, "TSH Ultrasensitive": 250,
            "Widal Slide/Tube Test": 180, "Dengue NS1 Antigen + IgM/IgG": 750, "Malaria Antigen Rapid": 250,
            "Urine Routine & Microscopic": 150, "Vitamin D (25-OH)": 1200, "Vitamin B12": 900, "Serum Calcium": 200,
            "BHARAT Basic Health Package (CBC, Sugar, Lipid, LFT)": 1299, "BHARAT Executive Full Body Package": 2499
        }
        
        selected = st.multiselect("Select Tests / Packages", list(test_prices.keys()), default=["Complete Blood Count (CBC)"])
        total = sum(test_prices[t] for t in selected)
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Total Test Price", f"₹ {total}")
            discount = st.number_input("Discount (₹)", value=0, min_value=0)
            final_p = max(0, total - discount)
            st.metric("Final Payable Amount", f"₹ {final_p}")
            
        with c2:
            st.subheader("UPI QR Code Payment")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=upi://pay?pa=bharatlab@upi&pn=BHARATLab&am={final_p}&cu=INR", caption=f"Scan to Pay ₹{final_p} via Any UPI App")
            
        if st.button("Confirm Payment & Save Bill", type="primary", use_container_width=True):
            if not selected:
                st.error("Kripya kam se kam ek test select karein.")
            else:
                conn = get_db()
                c = conn.cursor()
                for t in selected:
                    c.execute("INSERT INTO tests_billing (patient_id, test_name, test_price, paid_amount, status) VALUES (?, ?, ?, ?, ?)", 
                              (pid, t, test_prices[t], final_p, "Paid"))
                conn.commit()
                conn.close()
                st.success(f"Bill ₹{final_p} successfully save ho gaya for Patient: {pid}!")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 7: FINANCIAL ANALYSIS -----------------
elif menu == "Financial Analysis":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Financial & Referral Analytics</h4>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT bill_id, patient_id, test_name, test_price, paid_amount, status, created_at FROM tests_billing ORDER BY bill_id DESC")
    bills_data = c.fetchall()
    conn.close()
    if not bills_data:
        st.info("Koi billing record nahi mila.")
    else:
        df_bills = pd.DataFrame(bills_data, columns=["Bill ID", "Patient ID", "Test", "Price", "Paid", "Status", "Date"])
        st.dataframe(df_bills, use_container_width=True)
        st.metric("Total Collection", f"₹ {df_bills['Paid'].sum():,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 8: TESTS & RATE LIST -----------------
elif menu == "Tests & Rate List":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">BHARAT Pathology - Diagnostic Directory</h4>', unsafe_allow_html=True)
    test_data = {
        "Code": ["HEM01", "HEM02", "HEM03", "BIO01", "BIO02", "BIO03", "BIO04", "BIO05", "BIO06", "THY01", "SER01", "SER02", "URI01", "VIT01", "PKG01", "PKG02"],
        "Test Name": [
            "Complete Blood Count (CBC)", "Hemoglobin (Hb Only)", "ESR",
            "Blood Glucose - Fasting", "Blood Glucose - PP", "HbA1c",
            "Liver Function Test (LFT)", "Kidney Function Test (KFT)", "Lipid Profile",
            "Thyroid Profile (T3, T4, TSH)", "Widal Test", "Dengue NS1 Antigen",
            "Urine Routine & Microscopic", "Vitamin D (25-OH)",
            "BHARAT Basic Health Package", "BHARAT Executive Full Body Package"
        ],
        "Department": ["Hematology", "Hematology", "Hematology", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Endocrinology", "Serology", "Serology", "Clinical Pathology", "Immunology", "Package", "Package"],
        "Standard Rate (₹)": [350, 80, 100, 80, 80, 450, 650, 600, 700, 500, 180, 750, 150, 1200, 1299, 2499],
        "B2B Rate (₹)": [180, 40, 50, 40, 40, 250, 350, 320, 380, 280, 90, 450, 80, 750, 800, 1600]
    }
    st.dataframe(pd.DataFrame(test_data), use_container_width=True, height=480)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 9: SMART REPORT (DYNAMIC ALL PARAMETERS PDF) -----------------
elif menu == "Smart Report":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Smart Report & WhatsApp</h4>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT p.id, p.designation, p.name, p.age, p.age_type, p.gender, p.phone, p.doctor, r.parameters_json, r.verified_by
        FROM patients p JOIN test_results_all r ON p.id = r.patient_id
    """)
    rep_data = c.fetchall()
    conn.close()
    
    if not rep_data:
        st.warning("Pehle 'Enter & Verify' module mein test values fill karke save karein.")
    else:
        rep_dict = {row[0]: row for row in rep_data}
        pid = st.selectbox("Select Patient for Report", list(rep_dict.keys()), format_func=lambda x: f"{x} - {rep_dict[x][2]}")
        p_row = rep_dict[pid]
        
        parsed_params = {}
        try:
            parsed_params = json.loads(p_row[8])
        except Exception:
            parsed_params = {}

        # Master parameter reference table (Units & Bio Reference Ranges)
        reference_standards = {
            "Hemoglobin (Hb)": ("g/dL", "13.0 - 17.0"),
            "Total Leucocyte Count (TLC/WBC)": ("/cumm", "4000 - 11000"),
            "Platelet Count": ("Lakhs/cumm", "1.50 - 4.50"),
            "RBC Count": ("mil/cumm", "4.50 - 5.50"),
            "Packed Cell Volume (PCV/HCT)": ("%", "40.0 - 50.0"),
            "MCV": ("fL", "80.0 - 100.0"),
            "MCH": ("pg", "27.0 - 32.0"),
            "MCHC": ("g/dL", "32.0 - 36.0"),
            "RDW-CV": ("%", "11.5 - 14.5"),
            "ESR (Westergren)": ("mm/1st hr", "0 - 15"),
            "Neutrophils": ("%", "40 - 75"),
            "Lymphocytes": ("%", "20 - 45"),
            "Eosinophils": ("%", "01 - 06"),
            "Monocytes": ("%", "02 - 10"),
            "Basophils": ("%", "00 - 01"),
            "Blood Glucose (Fasting)": ("mg/dL", "70 - 100"),
            "Blood Glucose (PP)": ("mg/dL", "< 140"),
            "Blood Glucose (Random)": ("mg/dL", "70 - 140"),
            "HbA1c (Glycated Hb)": ("%", "< 5.7 (Normal)"),
            "Estimated Avg Glucose (eAG)": ("mg/dL", "90 - 120"),
            "Serum Urea": ("mg/dL", "15 - 40"),
            "Blood Urea Nitrogen (BUN)": ("mg/dL", "7 - 20"),
            "Serum Creatinine": ("mg/dL", "0.60 - 1.20"),
            "Serum Uric Acid": ("mg/dL", "3.5 - 7.2"),
            "Serum Calcium (Total)": ("mg/dL", "8.8 - 10.2"),
            "Serum Sodium (Na+)": ("mEq/L", "136 - 145"),
            "Bilirubin Total": ("mg/dL", "0.2 - 1.2"),
            "Bilirubin Direct": ("mg/dL", "0.0 - 0.3"),
            "SGOT / AST": ("U/L", "5 - 40"),
            "SGPT / ALT": ("U/L", "5 - 45"),
            "Alkaline Phosphatase (ALP)": ("U/L", "30 - 120"),
            "Total Protein": ("g/dL", "6.0 - 8.3"),
            "Serum Albumin": ("g/dL", "3.5 - 5.0"),
            "A/G Ratio": ("Ratio", "1.2 - 2.0"),
            "Total Cholesterol": ("mg/dL", "< 200"),
            "Triglycerides": ("mg/dL", "< 150"),
            "HDL Cholesterol (Good)": ("mg/dL", "> 40"),
            "LDL Cholesterol (Bad)": ("mg/dL", "< 100"),
            "VLDL Cholesterol": ("mg/dL", "10 - 30"),
            "CRP (Quantitative)": ("mg/L", "< 6.0"),
            "Total T3 (Triiodothyronine)": ("ng/dL", "60 - 200"),
            "Total T4 (Thyroxine)": ("µg/dL", "4.5 - 12.0"),
            "TSH (Ultrasensitive)": ("µIU/mL", "0.35 - 5.50"),
            "Widal Test (Typhoid)": ("Titre", "Negative (< 1:80)"),
            "Dengue NS1 Antigen": ("Result", "Negative"),
            "Malaria Antigen (Pv/Pf)": ("Result", "Negative"),
            "Urine Color & Appearance": ("Physical", "Pale Yellow, Clear"),
            "Urine Reaction (pH)": ("pH", "4.5 - 8.0"),
            "Urine Specific Gravity": ("Sp. Gr.", "1.005 - 1.030"),
            "Urine Protein / Albumin": ("Chemical", "Nil / Negative"),
            "Urine Sugar / Glucose": ("Chemical", "Nil / Negative"),
            "Urine Pus Cells": ("/HPF", "2 - 4 / HPF"),
            "Urine Epithelial Cells": ("/HPF", "1 - 3 / HPF"),
            "Urine RBCs": ("/HPF", "Nil")
        }

        # Multi-page ReportLab PDF Generator
        buffer = io.BytesIO()
        c_pdf = canvas.Canvas(buffer, pagesize=letter)
        
        def draw_report_header(canv):
            canv.setFont("Helvetica-Bold", 16)
            canv.setFillColor(colors.HexColor("#991B1B"))
            canv.drawString(50, 755, "BHARAT PATHOLOGY & DIAGNOSTIC CENTRE")
            canv.setFont("Helvetica", 9)
            canv.setFillColor(colors.black)
            canv.drawString(50, 740, "ISO 9001:2015 Certified | NABL Guidelines Compliant LIS")
            canv.drawString(50, 727, "Address: Main Medical Road, City Centre | Contact: +91 98765 43210")
            canv.setLineWidth(1.2)
            canv.setStrokeColor(colors.HexColor("#DC2626"))
            canv.line(50, 720, 560, 720)
            
            # Patient Details
            canv.setFont("Helvetica-Bold", 9)
            canv.drawString(50, 703, f"Patient ID: {p_row[0]}")
            canv.drawString(50, 688, f"Patient: {p_row[1]} {p_row[2]} ({p_row[3]} {p_row[4]} / {p_row[5]})")
            canv.drawString(330, 703, f"Date & Time: {datetime.date.today().strftime('%d-%b-%Y')}")
            canv.drawString(330, 688, f"Ref By: {p_row[7]}")
            canv.setLineWidth(0.6)
            canv.line(50, 678, 560, 678)
            
            # Table Header
            canv.setFont("Helvetica-Bold", 9)
            canv.drawString(50, 663, "Test Investigation")
            canv.drawString(250, 663, "Observed Value")
            canv.drawString(365, 663, "Biological Ref. Range")
            canv.drawString(490, 663, "Unit")
            canv.line(50, 656, 560, 656)

        draw_report_header(c_pdf)
        y_pos = 640
        
        c_pdf.setFont("Helvetica", 8.5)
        for param, val in parsed_params.items():
            if not val or str(val).strip() == "":
                continue
            unit, ref = reference_standards.get(param, ("-", "-"))
            
            # Page overflow handling
            if y_pos < 100:
                c_pdf.line(50, 95, 560, 95)
                c_pdf.setFont("Helvetica-Oblique", 8)
                c_pdf.drawString(460, 80, "Continued on Next Page...")
                c_pdf.showPage()
                draw_report_header(c_pdf)
                y_pos = 640
                c_pdf.setFont("Helvetica", 8.5)

            c_pdf.drawString(50, y_pos, str(param)[:38])
            c_pdf.setFont("Helvetica-Bold", 8.5)
            c_pdf.drawString(250, y_pos, str(val))
            c_pdf.setFont("Helvetica", 8.5)
            c_pdf.drawString(365, y_pos, str(ref))
            c_pdf.drawString(490, y_pos, str(unit))
            y_pos -= 18

        # Footer Signature
        c_pdf.line(50, 95, 560, 95)
        c_pdf.setFont("Helvetica-Bold", 9)
        c_pdf.drawString(50, 75, "*** END OF DETAILED CLINICAL REPORT ***")
        c_pdf.drawString(360, 75, f"Verified: {p_row[9]}")
        c_pdf.save()
        buffer.seek(0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Download Official Multi-Parameter PDF", data=buffer, file_name=f"BHARAT_Report_{pid}.pdf", mime="application/pdf", type="primary", use_container_width=True)
        with col2:
            msg = f"Namaste {p_row[2]}, aapki BHARAT Pathology Lab diagnostic report (ID: {pid}) taiyar hai."
            st.link_button("📲 Send via WhatsApp", f"https://wa.me/91{p_row[6]}?text={urllib.parse.quote(msg)}", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 10: LAB MANAGEMENT -----------------
elif menu == "Lab Management":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Referral Doctor Management</h4>', unsafe_allow_html=True)
    with st.form("doc"):
        dn = st.text_input("Doctor Name")
        dc = st.number_input("Commission (%)", value=15.0)
        if st.form_submit_button("Add Doctor"):
            if dn:
                conn = get_db()
                c = conn.cursor()
                c.execute("INSERT OR IGNORE INTO doctors (name, commission) VALUES (?, ?)", (dn, dc))
                conn.commit()
                conn.close()
                st.success("Doctor added!")
                st.rerun()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, commission FROM doctors")
    d_rows = c.fetchall()
    conn.close()
    if d_rows:
        st.dataframe(pd.DataFrame(d_rows, columns=["Doctor", "Commission %"]), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 11: INVENTORY -----------------
elif menu == "Inventory":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Reagents & Consumables</h4>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT item_name, category, stock, unit, expiry_date FROM inventory")
    inv_data = c.fetchall()
    conn.close()
    if inv_data:
        st.dataframe(pd.DataFrame(inv_data, columns=["Item", "Category", "Quantity", "Unit", "Expiry"]), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 12: LAB PROFILE -----------------
elif menu == "Lab Profile":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Lab Profile</h4>', unsafe_allow_html=True)
    st.text_input("Lab Name", "BHARAT Pathology & Diagnostic Centre")
    st.text_input("Accreditation", "ISO 9001:2015 / NABL Compliant")
    st.text_input("Email", "contact@bharatpathology.com")
    st.button("Save Profile", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)
