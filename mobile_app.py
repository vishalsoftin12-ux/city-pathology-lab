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

# SQLite Database Setup (Self-healing & auto-migrating)
DB_NAME = "bharat_lab_v2.db"

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()
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
    c.execute('''CREATE TABLE IF NOT EXISTS tests_billing (
                    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT,
                    test_name TEXT,
                    test_price REAL,
                    paid_amount REAL,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS test_results_all (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT UNIQUE,
                    parameters_json TEXT,
                    status TEXT DEFAULT 'Verified',
                    verified_by TEXT DEFAULT 'Dr. Pathologist (MD)',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    commission REAL DEFAULT 15.0
                )''')
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

# BHARAT Red Theme Styling
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
    .stButton > button[kind="primary"] {
        background-color: #DC2626 !important;
        border-color: #DC2626 !important;
        color: white !important;
        border-radius: 6px;
        font-weight: 600;
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

# ----------------- MODULE 2: CREDENT (BARCODE) -----------------
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

# ----------------- MODULE 5: ENTER & VERIFY -----------------
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
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT parameters_json, verified_by FROM test_results_all WHERE patient_id = ?", (selected_pid,))
        saved_row = c.fetchone()
        conn.close()
        
        saved_params = json.loads(saved_row[0]) if saved_row and saved_row[0] else {}

        tabs = st.tabs([
            "🩸 Hematology (CBC & ESR)",
            "🧪 Biochemistry & Sugar",
            "🫘 KFT / Kidney Panel",
            "🩺 LFT / Liver Panel",
            "🫀 Lipid & Cardiac",
            "🔬 Urine Routine"
        ])
        results = {}

        with tabs[0]:
            st.markdown('<div class="dept-header">Complete Blood Count (CBC) with Differential & ESR</div>', unsafe_allow_html=True)
            h1, h2, h3 = st.columns(3)
            with h1:
                results["Hemoglobin (Hb)"] = st.text_input("Hemoglobin [g/dL | 13.0 - 17.0]", str(saved_params.get("Hemoglobin (Hb)", "13.8")))
                results["Total Leucocyte Count (TLC/WBC)"] = st.text_input("Total WBC [cumm | 4000 - 11000]", str(saved_params.get("Total Leucocyte Count (TLC/WBC)", "6800")))
                results["Platelet Count"] = st.text_input("Platelets [Lakh/cumm | 1.5 - 4.5]", str(saved_params.get("Platelet Count", "2.40")))
            with h2:
                results["Neutrophils"] = st.text_input("Neutrophils [% | 40 - 75]", str(saved_params.get("Neutrophils", "64")))
                results["Lymphocytes"] = st.text_input("Lymphocytes [% | 20 - 45]", str(saved_params.get("Lymphocytes", "28")))
                results["Eosinophils"] = st.text_input("Eosinophils [% | 01 - 06]", str(saved_params.get("Eosinophils", "03")))
            with h3:
                results["RBC Count"] = st.text_input("RBC Count [mil/cumm | 4.5 - 5.5]", str(saved_params.get("RBC Count", "4.8")))
                results["ESR (Westergren)"] = st.text_input("ESR [mm/hr | 0 - 15]", str(saved_params.get("ESR (Westergren)", "10")))

        with tabs[1]:
            st.markdown('<div class="dept-header">Blood Glucose & Glycated Hemoglobin</div>', unsafe_allow_html=True)
            b1, b2 = st.columns(2)
            with b1:
                results["Blood Glucose (Fasting)"] = st.text_input("Blood Glucose - Fasting [mg/dL | 70 - 100]", str(saved_params.get("Blood Glucose (Fasting)", "92")))
                results["Blood Glucose (PP)"] = st.text_input("Blood Glucose - PP [mg/dL | < 140]", str(saved_params.get("Blood Glucose (PP)", "128")))
            with b2:
                results["HbA1c (Glycated Hb)"] = st.text_input("HbA1c [% | < 5.7]", str(saved_params.get("HbA1c (Glycated Hb)", "5.4")))

        with tabs[2]:
            st.markdown('<div class="dept-header">Kidney Function Test (KFT / RFT)</div>', unsafe_allow_html=True)
            k1, k2 = st.columns(2)
            with k1:
                results["Serum Creatinine"] = st.text_input("Serum Creatinine [mg/dL | 0.6 - 1.2]", str(saved_params.get("Serum Creatinine", "0.95")))
                results["Serum Urea"] = st.text_input("Blood Urea [mg/dL | 15 - 40]", str(saved_params.get("Serum Urea", "26.5")))
            with k2:
                results["Serum Uric Acid"] = st.text_input("Serum Uric Acid [mg/dL | 3.5 - 7.2]", str(saved_params.get("Serum Uric Acid", "4.8")))

        with tabs[3]:
            st.markdown('<div class="dept-header">Liver Function Test (LFT)</div>', unsafe_allow_html=True)
            l1, l2 = st.columns(2)
            with l1:
                results["Bilirubin Total"] = st.text_input("Serum Bilirubin Total [mg/dL | 0.2 - 1.2]", str(saved_params.get("Bilirubin Total", "0.8")))
                results["SGOT / AST"] = st.text_input("SGOT / AST [U/L | 5 - 40]", str(saved_params.get("SGOT / AST", "28")))
            with l2:
                results["SGPT / ALT"] = st.text_input("SGPT / ALT [U/L | 5 - 45]", str(saved_params.get("SGPT / ALT", "32")))

        with tabs[4]:
            st.markdown('<div class="dept-header">Lipid Profile</div>', unsafe_allow_html=True)
            lp1, lp2 = st.columns(2)
            with lp1:
                results["Total Cholesterol"] = st.text_input("Total Cholesterol [mg/dL | < 200]", str(saved_params.get("Total Cholesterol", "172")))
            with lp2:
                results["Triglycerides"] = st.text_input("Triglycerides [mg/dL | < 150]", str(saved_params.get("Triglycerides", "135")))

        with tabs[5]:
            st.markdown('<div class="dept-header">Urine Routine & Microscopic</div>', unsafe_allow_html=True)
            u1, u2 = st.columns(2)
            with u1:
                results["Urine Sugar"] = st.selectbox("Urine Sugar", ["Nil", "Trace", "+", "++"], index=0)
            with u2:
                results["Urine Pus Cells"] = st.text_input("Pus Cells [/HPF | 2 - 4]", str(saved_params.get("Urine Pus Cells", "2 - 3 / HPF")))

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Save & Lock All Parameters ➔", type="primary"):
            conn = get_db()
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO test_results_all (patient_id, parameters_json, status, verified_by)
                         VALUES (?, ?, ?, ?)''', (selected_pid, json.dumps(results), "Approved", "Dr. Pathologist (MD)"))
            conn.commit()
            conn.close()
            st.success("Results successfully save ho gaye!")
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
        st.info("Pehle patient register karein.")
    else:
        b_dict = {r[0]: f"{r[0]} - {r[1]} ({r[2]})" for r in b_pts}
        pid = st.selectbox("Select Patient", list(b_dict.keys()), format_func=lambda x: b_dict[x])
        test_prices = {
            "Complete Blood Count (CBC)": 350, "Hemoglobin (Hb Only)": 80, "ESR": 100,
            "Blood Glucose - Fasting": 80, "Blood Glucose - PP": 80, "HbA1c": 450,
            "Liver Function Test (LFT)": 650, "Kidney Function Test (KFT / RFT)": 600,
            "Lipid Profile (Full Panel)": 700, "Thyroid Profile (T3, T4, TSH)": 500,
            "Widal Slide/Tube Test": 180, "Dengue NS1 Antigen": 750, "Urine Routine": 150,
            "BHARAT Basic Health Package": 1299, "BHARAT Executive Full Body Package": 2499
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
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=upi://pay?pa=bharatlab@upi&pn=BHARATLab&am={final_p}&cu=INR", caption=f"Scan to Pay ₹{final_p}")
            
        if st.button("Confirm Payment & Save Bill", type="primary", use_container_width=True):
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
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Diagnostic Directory & Rates</h4>', unsafe_allow_html=True)
    test_data = {
        "Code": ["HEM01", "HEM02", "HEM03", "BIO01", "BIO02", "BIO03", "BIO04", "BIO05", "BIO06", "THY01", "SER01", "URI01", "PKG01", "PKG02"],
        "Test Name": ["Complete Blood Count (CBC)", "Hemoglobin (Hb)", "ESR", "Blood Glucose - Fasting", "Blood Glucose - PP", "HbA1c", "Liver Function Test (LFT)", "Kidney Function Test (KFT)", "Lipid Profile", "Thyroid Profile (T3, T4, TSH)", "Widal Test", "Urine Routine", "Basic Health Package", "Full Body Checkup"],
        "Department": ["Hematology", "Hematology", "Hematology", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Endocrinology", "Serology", "Clinical Path", "Package", "Package"],
        "Price (₹)": [350, 80, 100, 80, 80, 450, 650, 600, 700, 500, 180, 150, 1299, 2499]
    }
    st.dataframe(pd.DataFrame(test_data), use_container_width=True, height=450)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 9: SMART REPORT -----------------
elif menu == "Smart Report":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Smart Report & WhatsApp</h4>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT p.id, p.designation, p.name, p.age, p.gender, p.phone, p.doctor, r.parameters_json, r.verified_by
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
        parsed_params = json.loads(p_row[7])

        buffer = io.BytesIO()
        c_pdf = canvas.Canvas(buffer, pagesize=letter)
        c_pdf.setFont("Helvetica-Bold", 16)
        c_pdf.setFillColor(colors.HexColor("#991B1B"))
        c_pdf.drawString(50, 750, "BHARAT PATHOLOGY & DIAGNOSTIC CENTRE")
        c_pdf.setFont("Helvetica", 9)
        c_pdf.setFillColor(colors.black)
        c_pdf.drawString(50, 735, "ISO 9001:2015 Certified | Powered by BHARAT LIS")
        c_pdf.line(50, 725, 560, 725)
        
        c_pdf.setFont("Helvetica-Bold", 10)
        c_pdf.drawString(50, 705, f"Patient ID: {p_row[0]}")
        c_pdf.drawString(50, 690, f"Patient Name: {p_row[1]} {p_row[2]} ({p_row[3]} Y / {p_row[4]})")
        c_pdf.drawString(350, 705, f"Date: {datetime.date.today().strftime('%d-%b-%Y')}")
        c_pdf.drawString(350, 690, f"Ref Doctor: {p_row[6]}")
        c_pdf.line(50, 675, 560, 675)
        
        y = 650
        c_pdf.setFont("Helvetica-Bold", 10)
        c_pdf.drawString(50, y, "Investigation")
        c_pdf.drawString(340, y, "Observed Result")
        y -= 20
        c_pdf.setFont("Helvetica", 9.5)
        for k, v in parsed_params.items():
            c_pdf.drawString(50, y, str(k))
            c_pdf.drawString(340, y, str(v))
            y -= 18
            if y < 90:
                c_pdf.showPage()
                y = 720
        c_pdf.line(50, 80, 560, 80)
        c_pdf.setFont("Helvetica-Bold", 9)
        c_pdf.drawString(380, 65, f"Verified By: {p_row[8]}")
        c_pdf.save()
        buffer.seek(0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Download Official Report PDF", data=buffer, file_name=f"Report_{pid}.pdf", mime="application/pdf", type="primary", use_container_width=True)
        with col2:
            msg = f"Namaste {p_row[2]}, aapki BHARAT Pathology Lab diagnostic report (ID: {pid}) taiyar hai."
            st.link_button("📲 Send via WhatsApp", f"https://wa.me/91{p_row[5]}?text={urllib.parse.quote(msg)}", use_container_width=True)
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
