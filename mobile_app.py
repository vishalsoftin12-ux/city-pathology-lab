import streamlit as st
import pandas as pd
import sqlite3
import datetime
import io
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

# Robust Database Initialization with Auto-Repair
def init_db():
    conn = sqlite3.connect("lab.db")
    c = conn.cursor()
    
    # Check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients'")
    table_exists = c.fetchone()
    
    if not table_exists:
        c.execute('''CREATE TABLE patients (
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
    else:
        # Auto-add any missing columns
        c.execute("PRAGMA table_info(patients)")
        cols = [col[1] for col in c.fetchall()]
        needed_cols = {
            "designation": "TEXT",
            "age_type": "TEXT",
            "rate_list": "TEXT",
            "dispatch_methods": "TEXT",
            "aadhaar": "TEXT",
            "email": "TEXT",
            "address": "TEXT",
            "sample_status": "TEXT DEFAULT 'Sample Collected'"
        }
        for col_name, col_type in needed_cols.items():
            if col_name not in cols:
                try:
                    c.execute(f"ALTER TABLE patients ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass

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
                
    # Test Results Table
    c.execute('''CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT UNIQUE,
                    hb REAL,
                    wbc REAL,
                    platelets REAL,
                    neutrophils REAL,
                    lymphocytes REAL,
                    status TEXT DEFAULT 'Verified',
                    verified_by TEXT DEFAULT 'Dr. Pathologist (MD)'
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
    
    c.execute("INSERT OR IGNORE INTO inventory (id, item_name, category, stock, unit, expiry_date) VALUES (1, 'EDTA Tubes (Purple, 2ml)', 'Consumables', 250, 'Pcs', '2027-12-31')")
    c.execute("INSERT OR IGNORE INTO inventory (id, item_name, category, stock, unit, expiry_date) VALUES (2, 'CBC Diluent 20L', 'Reagents', 4, 'Bottles', '2027-06-30')")
    c.execute("INSERT OR IGNORE INTO inventory (id, item_name, category, stock, unit, expiry_date) VALUES (3, 'Plain Serum Vials (Red, 5ml)', 'Consumables', 180, 'Pcs', '2027-08-15')")
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect("lab.db")

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

# BHARAT Red Corporate Styling
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
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
    }
    .stButton > button[kind="primary"] {
        background-color: #DC2626 !important;
        border-color: #DC2626 !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #B91C1C !important;
        border-color: #B91C1C !important;
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

# Sidebar Menu
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
            st.success(f"Patient {new_pid} ({first_name}) successfully registered!")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 2: CREDENT (ACCESSION & BARCODE) -----------------
elif menu == "Credent (Accession & Barcode)":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Credent: Sample Accession & Barcode Tracking</h4>', unsafe_allow_html=True)
    conn = get_db()
    pts = pd.read_sql_query("SELECT id, name, gender, age, sample_status FROM patients ORDER BY rowid DESC", conn)
    conn.close()
    
    if pts.empty:
        st.info("Koi patient data uplabdh nahi hai.")
    else:
        c1, c2 = st.columns([1.6, 1])
        with c1:
            st.dataframe(pts, use_container_width=True)
        with c2:
            sel_pid = st.selectbox("Select Patient ID", pts['id'].tolist())
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
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 3: ANALYSIS -----------------
elif menu == "Analysis (Dashboard)":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Laboratory Dashboard & Metrics</h4>', unsafe_allow_html=True)
    conn = get_db()
    total_p = pd.read_sql_query("SELECT COUNT(*) FROM patients", conn).iloc[0,0]
    total_rev = pd.read_sql_query("SELECT SUM(paid_amount) FROM tests_billing", conn).iloc[0,0] or 0.0
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
    if q:
        query = f"SELECT id, name, age, gender, phone, doctor, sample_status FROM patients WHERE name LIKE '%{q}%' OR phone LIKE '%{q}%' OR id LIKE '%{q}%'"
    else:
        query = "SELECT id, name, age, gender, phone, doctor, sample_status FROM patients ORDER BY rowid DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 5: ENTER & VERIFY -----------------
elif menu == "Enter & Verify":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Enter Clinical Parameters & Verify Results</h4>', unsafe_allow_html=True)
    conn = get_db()
    pts = pd.read_sql_query("SELECT id, name FROM patients ORDER BY rowid DESC", conn)
    conn.close()
    
    if pts.empty:
        st.info("Pehle patient register karein.")
    else:
        selected_pid = st.selectbox("Select Patient", pts['id'].tolist(), format_func=lambda x: f"{x} - {pts[pts['id']==x]['name'].values[0]}")
        col1, col2, col3 = st.columns(3)
        with col1:
            hb = st.number_input("Haemoglobin (g/dL) [13.0 - 17.0]", value=14.2)
            wbc = st.number_input("Total WBC (/cumm) [4000 - 11000]", value=6800)
        with col2:
            platelets = st.number_input("Platelets (Lakhs/cumm) [1.5 - 4.5]", value=2.4)
            neutro = st.number_input("Neutrophils (%) [40 - 75]", value=62)
        with col3:
            lympho = st.number_input("Lymphocytes (%) [20 - 45]", value=30)
            verified_by = st.selectbox("Verified By", ["Dr. Pathologist (MD)", "Dr. Senior Resident"])
        if st.button("Save & Verify Findings", type="primary"):
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO test_results (patient_id, hb, wbc, platelets, neutrophils, lymphocytes, status, verified_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (selected_pid, hb, wbc, platelets, neutro, lympho, 'Approved', verified_by))
            conn.commit()
            conn.close()
            st.success("Test report approve ho gayi!")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 6: BILLING & INVOICING -----------------
elif menu == "Billing & Invoicing":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Billing & UPI Invoicing</h4>', unsafe_allow_html=True)
    conn = get_db()
    pts = pd.read_sql_query("SELECT id, name, phone FROM patients ORDER BY rowid DESC", conn)
    conn.close()
    
    if pts.empty:
        st.info("Pehle patient register karein.")
    else:
        pid = st.selectbox("Select Patient", pts['id'].tolist(), format_func=lambda x: f"{x} - {pts[pts['id']==x]['name'].values[0]}")
        test_prices = {
            "Complete Blood Count (CBC)": 350, "Liver Function Test (LFT)": 650, "Kidney Function Test (KFT)": 600,
            "Lipid Profile": 700, "Thyroid Profile (T3, T4, TSH)": 500, "Blood Sugar Fasting": 80,
            "HbA1c": 450, "Widal Test": 180, "Dengue NS1 Antigen": 750, "Urine Routine": 150
        }
        selected = st.multiselect("Select Tests", list(test_prices.keys()), default=["Complete Blood Count (CBC)"])
        total = sum(test_prices[t] for t in selected)
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Total Amount", f"₹ {total}")
            discount = st.number_input("Discount (₹)", value=0, min_value=0)
            final_p = max(0, total - discount)
            st.metric("Final Payable", f"₹ {final_p}")
        with c2:
            st.subheader("UPI QR Code")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=upi://pay?pa=bharatlab@upi&pn=BHARATLab&am={final_p}&cu=INR", caption=f"Scan to Pay ₹{final_p}")
        if st.button("Confirm Payment & Save Bill", type="primary"):
            conn = get_db()
            c = conn.cursor()
            for t in selected:
                c.execute("INSERT INTO tests_billing (patient_id, test_name, test_price, paid_amount, status) VALUES (?, ?, ?, ?, ?)", (pid, t, test_prices[t], final_p, "Paid"))
            conn.commit()
            conn.close()
            st.success("Bill successfully save ho gaya!")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 7: FINANCIAL ANALYSIS -----------------
elif menu == "Financial Analysis":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Financial & Referral Analytics</h4>', unsafe_allow_html=True)
    conn = get_db()
    bills = pd.read_sql_query("SELECT bill_id, patient_id, test_name, test_price, paid_amount, status, created_at FROM tests_billing ORDER BY bill_id DESC", conn)
    conn.close()
    if bills.empty:
        st.info("Koi billing record nahi mila.")
    else:
        st.dataframe(bills, use_container_width=True)
        st.metric("Total Collection", f"₹ {bills['paid_amount'].sum():,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 8: TESTS & RATE LIST -----------------
elif menu == "Tests & Rate List":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">BHARAT Pathology - All Diagnostic Tests & Packages</h4>', unsafe_allow_html=True)
    test_data = {
        "Code": [
            "HEM01", "HEM02", "HEM03", "HEM04", "HEM05", "HEM06", "HEM07", "HEM08",
            "BIO01", "BIO02", "BIO03", "BIO04", "BIO05", "BIO06", "BIO07", "BIO08", "BIO09", "BIO10", "BIO11", "BIO12",
            "THY01", "THY02", "THY03",
            "SER01", "SER02", "SER03", "SER04", "SER05", "SER06", "SER07",
            "URI01", "URI02", "URI03",
            "VIT01", "VIT02", "VIT03",
            "CARD01", "CARD02",
            "PKG01", "PKG02"
        ],
        "Test Name": [
            "Complete Blood Count (CBC)", "Hemoglobin (Hb Only)", "ESR", "Platelet Count", "Blood Group & Rh", "Peripheral Smear (PBS)", "PT-INR", "BT & CT",
            "Blood Glucose - Fasting", "Blood Glucose - PP", "Blood Glucose - Random", "HbA1c (Glycated Hemoglobin)", "Liver Function Test (LFT)", "Kidney Function Test (KFT)", "Serum Creatinine", "Serum Uric Acid", "Lipid Profile (Full Panel)", "Serum Bilirubin Total", "SGOT / AST", "SGPT / ALT",
            "Thyroid Profile Total (T3, T4, TSH)", "Thyroid Profile Free (FT3, FT4, TSH)", "TSH Ultrasensitive",
            "Widal Slide/Tube Test", "TyphiDot IgM/IgG", "Dengue NS1 Antigen + IgM/IgG", "Malaria Antigen Rapid", "Chikungunya IgM", "HBsAg Rapid", "HIV 1 & 2 Antibody",
            "Urine Routine & Microscopic", "Urine Pregnancy Test (UPT)", "Urine Microalbumin",
            "Vitamin D (25-OH)", "Vitamin B12", "Serum Calcium",
            "CRP (Quantitative)", "Troponin-I Rapid",
            "BHARAT Basic Health Package (CBC, Sugar, Lipid, LFT)", "BHARAT Executive Full Body Package (60+ Parameters)"
        ],
        "Department": [
            "Hematology", "Hematology", "Hematology", "Hematology", "Hematology", "Hematology", "Hematology", "Hematology",
            "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry",
            "Endocrinology", "Endocrinology", "Endocrinology",
            "Serology", "Serology", "Serology", "Serology", "Serology", "Serology", "Serology",
            "Clinical Pathology", "Clinical Pathology", "Clinical Pathology",
            "Immunology", "Immunology", "Biochemistry",
            "Biochemistry", "Cardiology",
            "Preventive Package", "Preventive Package"
        ],
        "Standard Rate (₹)": [
            350, 80, 100, 120, 100, 200, 300, 100,
            80, 80, 70, 450, 650, 600, 150, 180, 700, 220, 150, 150,
            500, 750, 250,
            180, 350, 750, 250, 600, 300, 350,
            150, 100, 400,
            1200, 900, 200,
            350, 800,
            1299, 2499
        ],
        "B2B Rate (₹)": [
            180, 40, 50, 60, 50, 100, 160, 50,
            40, 40, 35, 250, 350, 320, 80, 90, 380, 110, 80, 80,
            280, 420, 140,
            90, 180, 450, 120, 320, 150, 180,
            80, 50, 220,
            750, 550, 100,
            180, 450,
            800, 1600
        ],
        "Sample": [
            "EDTA Blood", "EDTA Blood", "Sodium Citrate", "EDTA Blood", "EDTA Blood", "EDTA Blood", "Sodium Citrate", "Capillary Blood",
            "Fluoride Plasma", "Fluoride Plasma", "Fluoride Plasma", "EDTA Blood", "Serum", "Serum", "Serum", "Serum", "Serum", "Serum", "Serum", "Serum",
            "Serum", "Serum", "Serum",
            "Serum", "Serum", "Serum", "Whole Blood", "Serum", "Serum", "Serum",
            "Urine", "Urine", "Urine",
            "Serum", "Serum", "Serum",
            "Serum", "Serum",
            "Blood + Urine", "Blood + Urine"
        ],
        "TAT": [
            "2 Hours", "1 Hour", "1 Hour", "2 Hours", "30 Mins", "4 Hours", "3 Hours", "30 Mins",
            "1 Hour", "1 Hour", "30 Mins", "2 Hours", "4 Hours", "4 Hours", "2 Hours", "2 Hours", "4 Hours", "3 Hours", "2 Hours", "2 Hours",
            "Same Day", "Same Day", "4 Hours",
            "1 Hour", "2 Hours", "2 Hours", "1 Hour", "3 Hours", "2 Hours", "2 Hours",
            "1 Hour", "15 Mins", "3 Hours",
            "Next Day", "Next Day", "2 Hours",
            "2 Hours", "1 Hour",
            "Same Day", "Next Day"
        ]
    }
    df_tests = pd.DataFrame(test_data)
    q = st.text_input("🔍 Search Test Name or Code", "")
    if q:
        df_tests = df_tests[df_tests["Test Name"].str.contains(q, case=False) | df_tests["Code"].str.contains(q, case=False)]
    st.dataframe(df_tests, use_container_width=True, height=540)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 9: SMART REPORT -----------------
elif menu == "Smart Report":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Smart Report & WhatsApp</h4>', unsafe_allow_html=True)
    conn = get_db()
    ready_pts = pd.read_sql_query("""
        SELECT p.id, p.name, p.phone, r.hb, r.wbc, r.platelets, r.neutrophils, r.lymphocytes, r.verified_by
        FROM patients p JOIN test_results r ON p.id = r.patient_id
    """, conn)
    conn.close()
    
    if ready_pts.empty:
        st.warning("Pehle 'Enter & Verify' module mein test values save karein.")
    else:
        pid = st.selectbox("Select Patient for Report", ready_pts['id'].tolist(), format_func=lambda x: f"{x} - {ready_pts[ready_pts['id']==x]['name'].values[0]}")
        p_row = ready_pts[ready_pts['id']==pid].iloc[0]
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor("#991B1B"))
        c.drawString(50, 750, "BHARAT PATHOLOGY & DIAGNOSTIC CENTRE")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        c.drawString(50, 735, "ISO 9001:2015 Certified | Powered by BHARAT LIS")
        c.setLineWidth(1)
        c.setStrokeColor(colors.HexColor("#DC2626"))
        c.line(50, 725, 560, 725)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 705, f"Patient ID: {p_row['id']}")
        c.drawString(50, 690, f"Patient Name: {p_row['name']}")
        c.drawString(350, 705, f"Date: {datetime.date.today().strftime('%d-%b-%Y')}")
        c.drawString(350, 690, f"Contact: {p_row['phone']}")
        c.line(50, 675, 560, 675)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 655, "Investigation")
        c.drawString(240, 655, "Result")
        c.drawString(360, 655, "Reference Range")
        c.drawString(480, 655, "Unit")
        c.line(50, 647, 560, 647)
        
        c.setFont("Helvetica", 10)
        tests = [
            ("Haemoglobin (Hb)", str(p_row['hb']), "13.0 - 17.0", "g/dL"),
            ("Total WBC Count", str(p_row['wbc']), "4000 - 11000", "/cumm"),
            ("Platelet Count", str(p_row['platelets']), "1.50 - 4.50", "Lakhs/cumm"),
            ("Neutrophils", str(p_row['neutrophils']), "40 - 75", "%"),
            ("Lymphocytes", str(p_row['lymphocytes']), "20 - 45", "%")
        ]
        y = 625
        for name, val, rng, unit in tests:
            c.drawString(50, y, name)
            c.drawString(240, y, val)
            c.drawString(360, y, rng)
            c.drawString(480, y, unit)
            y -= 22
            
        c.line(50, 200, 560, 200)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(400, 160, f"Verified: {p_row['verified_by']}")
        c.save()
        buffer.seek(0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Download Report PDF", data=buffer, file_name=f"Report_{pid}.pdf", mime="application/pdf", type="primary", use_container_width=True)
        with col2:
            msg = f"Namaste {p_row['name']}, aapki BHARAT Pathology Lab diagnostic report (ID: {pid}) taiyar hai."
            st.link_button("📲 Send via WhatsApp", f"https://wa.me/91{p_row['phone']}?text={urllib.parse.quote(msg)}", use_container_width=True)
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
    st.dataframe(pd.read_sql_query("SELECT name as 'Doctor', commission as 'Commission %' FROM doctors", conn), use_container_width=True)
    conn.close()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 11: INVENTORY -----------------
elif menu == "Inventory":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Reagents & Consumables</h4>', unsafe_allow_html=True)
    conn = get_db()
    st.dataframe(pd.read_sql_query("SELECT item_name as 'Item', category as 'Category', stock as 'Quantity', unit as 'Unit', expiry_date as 'Expiry' FROM inventory", conn), use_container_width=True)
    conn.close()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 12: LAB PROFILE -----------------
elif menu == "Lab Profile":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Lab Profile</h4>', unsafe_allow_html=True)
    st.text_input("Lab Name", "BHARAT Pathology & Diagnostic Centre")
    st.text_input("Accreditation", "ISO 9001:2015 / NABL Compliant")
    st.text_input("Email", "contact@bharatpathology.com")
    st.button("Save Profile", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)
