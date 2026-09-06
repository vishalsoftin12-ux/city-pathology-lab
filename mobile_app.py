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
    page_title="BHARAT LIS - Fast Counter Registration & Billing",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SQLite Database Setup
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
                    age_type TEXT DEFAULT 'Year',
                    gender TEXT,
                    doctor TEXT,
                    hospital TEXT,
                    rate_list TEXT DEFAULT 'Main',
                    dispatch_methods TEXT DEFAULT 'WhatsApp',
                    aadhaar TEXT DEFAULT '',
                    phone TEXT,
                    email TEXT DEFAULT '',
                    address TEXT,
                    sample_status TEXT DEFAULT 'Sample Collected',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Auto-add hospital column if missing
    c.execute("PRAGMA table_info(patients)")
    cols = [col[1] for col in c.fetchall()]
    if "hospital" not in cols:
        try:
            c.execute("ALTER TABLE patients ADD COLUMN hospital TEXT")
        except Exception:
            pass

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
    c.execute("INSERT OR IGNORE INTO doctors (name, commission) VALUES ('Self / Direct', 0)")
    c.execute("INSERT OR IGNORE INTO doctors (name, commission) VALUES ('Dr. Sharma (MBBS, MD)', 15)")
    c.execute("INSERT OR IGNORE INTO doctors (name, commission) VALUES ('Dr. Rajesh Verma (Consultant)', 20)")
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
    .section-title {
        color: #991B1B;
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
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
        <span style="background: #FEF2F2; color: #DC2626; border: 1px solid #FCA5A5; padding: 2px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;">FAST COUNTER</span>
    </div>
    <div style="display: flex; align-items: center; gap: 20px; font-size: 13px; color: #475569;">
        <span>Branch: <b>BHARAT Diagnostic Centre</b></span>
        <span>Operator: <b>Reception Counter</b></span>
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
            "Fast Registration & Billing",
            "Credent (Accession & Barcode)",
            "Enter & Verify",
            "Smart Report",
            "Patient List",
            "Financial Analysis",
            "Tests & Rate List"
        ]
    )

# ----------------- MODULE 1: FAST REGISTRATION & BILLING COMBINED -----------------
if menu == "Fast Registration & Billing":
    new_pid = generate_patient_id()
    doc_list = get_doctors()

    st.markdown('<div class="bharat-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">👤 STEP 1: PATIENT BASIC DETAILS</div>', unsafe_allow_html=True)

    # Row 1: ID, Gender (Auto sets Designation), Name, Age
    c1, c2, c3, c4 = st.columns([1.5, 2.5, 3.5, 1.5])
    with c1:
        st.caption("Patient ID")
        st.markdown(f"<h3 style='margin:0; color:#DC2626;'>{new_pid}</h3>", unsafe_allow_html=True)
    with c2:
        gender = st.radio("Gender *", ["Male", "Female", "Other"], horizontal=True)
        # Auto Designation Logic
        if gender == "Male":
            auto_designation = "MR."
        elif gender == "Female":
            auto_designation = "MS."
        else:
            auto_designation = "MR."
    with c3:
        first_name = st.text_input("Patient Full Name *", placeholder=f"Auto Title: {auto_designation}")
    with c4:
        age = st.number_input("Age *", min_value=0, max_value=120, value=28)

    # Row 2: Phone, Ref Doctor, Ref Hospital, Address
    r2_1, r2_2, r2_3, r2_4 = st.columns([2.5, 2.5, 2.5, 2.5])
    with r2_1:
        phone = st.text_input("Contact Number (IN +91) *", placeholder="10-digit mobile number")
    with r2_2:
        doctor = st.selectbox("Referring Doctor", doc_list)
    with r2_3:
        hospital = st.text_input("Ref Hospital / Clinic", placeholder="e.g. City Hospital / Self")
    with r2_4:
        address = st.text_input("Patient Address", placeholder="Village / City Area")

    st.markdown("<hr style='margin: 18px 0; border: none; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🧪 STEP 2: TEST SELECTION & INSTANT BILLING</div>', unsafe_allow_html=True)

    test_prices = {
        "Complete Blood Count (CBC)": 350, "Hemoglobin (Hb Only)": 80, "ESR": 100, "Platelet Count": 120,
        "Blood Glucose - Fasting": 80, "Blood Glucose - PP": 80, "HbA1c": 450,
        "Liver Function Test (LFT)": 650, "Kidney Function Test (KFT / RFT)": 600, "Serum Creatinine": 150,
        "Lipid Profile (Full Panel)": 700, "Thyroid Profile (T3, T4, TSH)": 500, "TSH Ultrasensitive": 250,
        "Widal Slide/Tube Test": 180, "Dengue NS1 Antigen": 750, "Malaria Antigen Rapid": 250,
        "Urine Routine & Microscopic": 150, "Vitamin D (25-OH)": 1200, "Vitamin B12": 900,
        "BHARAT Basic Health Package": 1299, "BHARAT Executive Full Body Package": 2499
    }

    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        selected_tests = st.multiselect("Select Tests / Packages for Patient", list(test_prices.keys()), default=["Complete Blood Count (CBC)"])
        gross_total = sum(test_prices[t] for t in selected_tests)
        
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.metric("Gross Amount", f"₹ {gross_total}")
        with c_p2:
            discount = st.number_input("Counter Discount (₹)", value=0, min_value=0)
            final_payable = max(0, gross_total - discount)
            st.metric("Net Amount to Collect", f"₹ {final_payable}")

    with col_t2:
        st.markdown("<p style='font-size:12px; font-weight:600; color:#475569; margin-bottom:4px;'>Scan & Pay (Any UPI App)</p>", unsafe_allow_html=True)
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=upi://pay?pa=bharatlab@upi&pn=BHARATLab&am={final_payable}&cu=INR", caption=f"Collect ₹{final_payable}")

    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2 = st.columns([7, 3])
    with b2:
        btn_submit = st.button("Complete Registration & Record Bill ➔", type="primary", use_container_width=True)

    if btn_submit:
        if not first_name or not phone:
            st.error("Patient Name aur Contact Number bharna zaroori hai.")
        elif not selected_tests:
            st.error("Kam se kam ek test select karein.")
        else:
            conn = get_db()
            c = conn.cursor()
            # 1. Save Patient
            c.execute('''INSERT INTO patients (id, designation, name, age, age_type, gender, doctor,
                            hospital, rate_list, dispatch_methods, aadhaar, phone, email, address, sample_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (new_pid, auto_designation, first_name, int(age), "Year", gender, doctor,
                             hospital, "Main", "WhatsApp", "", phone, "", address, 'Sample Collected'))
            
            # 2. Save Billing
            for t in selected_tests:
                c.execute("INSERT INTO tests_billing (patient_id, test_name, test_price, paid_amount, status) VALUES (?, ?, ?, ?, ?)",
                          (new_pid, t, test_prices[t], final_payable, "Paid"))
            conn.commit()
            conn.close()
            st.success(f"Patient {new_pid} ({auto_designation} {first_name}) registered & ₹{final_payable} Bill Saved!")
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
        st.info("Pehle patient register karein.")
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
            if st.button("Update Status", type="primary"):
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE patients SET sample_status = ? WHERE id = ?", (new_status, sel_pid))
                conn.commit()
                conn.close()
                st.success("Status update ho gaya!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 3: ENTER & VERIFY -----------------
elif menu == "Enter & Verify":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Clinical Results Entry</h4>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name FROM patients ORDER BY rowid DESC")
    pts_data = c.fetchall()
    conn.close()
    
    if not pts_data:
        st.info("Pehle patient register karein.")
    else:
        pt_dict = {row[0]: row[1] for row in pts_data}
        selected_pid = st.selectbox("Select Patient", list(pt_dict.keys()), format_func=lambda x: f"{x} - {pt_dict[x]}")
        
        tabs = st.tabs(["Hematology (CBC)", "Biochemistry & Sugar", "KFT / Renal", "LFT / Liver", "Lipid Profile"])
        results = {}

        with tabs[0]:
            h1, h2, h3 = st.columns(3)
            with h1:
                results["Hemoglobin (Hb)"] = st.text_input("Hemoglobin [g/dL | 13.0 - 17.0]", "14.2")
                results["Total Leucocyte Count (TLC)"] = st.text_input("Total WBC [/cumm | 4000 - 11000]", "6800")
            with h2:
                results["Platelet Count"] = st.text_input("Platelets [Lakhs/cumm | 1.5 - 4.5]", "2.40")
                results["Neutrophils"] = st.text_input("Neutrophils [% | 40 - 75]", "62")
            with h3:
                results["Lymphocytes"] = st.text_input("Lymphocytes [% | 20 - 45]", "30")
                results["ESR"] = st.text_input("ESR [mm/hr | 0 - 15]", "10")

        with tabs[1]:
            b1, b2 = st.columns(2)
            with b1:
                results["Blood Glucose Fasting"] = st.text_input("Fasting Glucose [mg/dL | 70 - 100]", "95")
            with b2:
                results["HbA1c"] = st.text_input("HbA1c [% | < 5.7]", "5.4")

        with tabs[2]:
            k1, k2 = st.columns(2)
            with k1:
                results["Serum Creatinine"] = st.text_input("Creatinine [mg/dL | 0.6 - 1.2]", "0.95")
            with k2:
                results["Blood Urea"] = st.text_input("Blood Urea [mg/dL | 15 - 40]", "28.0")

        with tabs[3]:
            l1, l2 = st.columns(2)
            with l1:
                results["Bilirubin Total"] = st.text_input("Bilirubin Total [mg/dL | 0.2 - 1.2]", "0.8")
            with l2:
                results["SGOT / AST"] = st.text_input("SGOT [U/L | 5 - 40]", "28")

        with tabs[4]:
            lp1, lp2 = st.columns(2)
            with lp1:
                results["Total Cholesterol"] = st.text_input("Total Cholesterol [mg/dL | < 200]", "172")
            with lp2:
                results["Triglycerides"] = st.text_input("Triglycerides [mg/dL | < 150]", "135")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Save & Lock Findings ➔", type="primary"):
            conn = get_db()
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO test_results_all (patient_id, parameters_json, status, verified_by)
                         VALUES (?, ?, ?, ?)''', (selected_pid, json.dumps(results), "Approved", "Dr. Pathologist (MD)"))
            conn.commit()
            conn.close()
            st.success("Findings saved successfully!")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 4: SMART REPORT -----------------
elif menu == "Smart Report":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Official Report & WhatsApp</h4>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT p.id, p.designation, p.name, p.age, p.gender, p.phone, p.doctor, p.hospital, r.parameters_json, r.verified_by
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
        parsed_params = json.loads(p_row[8])

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
        c_pdf.drawString(50, 690, f"Name: {p_row[1]} {p_row[2]} ({p_row[3]} Y / {p_row[4]})")
        c_pdf.drawString(340, 705, f"Date: {datetime.date.today().strftime('%d-%b-%Y')}")
        c_pdf.drawString(340, 690, f"Doctor: {p_row[6]}")
        if p_row[7]:
            c_pdf.drawString(340, 675, f"Hospital: {p_row[7]}")
        c_pdf.line(50, 665, 560, 665)
        
        y = 640
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
        c_pdf.drawString(380, 65, f"Verified By: {p_row[9]}")
        c_pdf.save()
        buffer.seek(0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Download PDF Report", data=buffer, file_name=f"Report_{pid}.pdf", mime="application/pdf", type="primary", use_container_width=True)
        with col2:
            msg = f"Namaste {p_row[2]}, aapki diagnostic test report taiyar hai."
            st.link_button("📲 Send to WhatsApp", f"https://wa.me/91{p_row[5]}?text={urllib.parse.quote(msg)}", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 5: PATIENT LIST -----------------
elif menu == "Patient List":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Patient Directory</h4>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, age, gender, phone, doctor, hospital, sample_status FROM patients ORDER BY rowid DESC")
    data = c.fetchall()
    conn.close()
    if data:
        st.dataframe(pd.DataFrame(data, columns=["ID", "Name", "Age", "Gender", "Phone", "Doctor", "Hospital", "Status"]), use_container_width=True)
    else:
        st.info("Koi patient nahi mila.")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 6: FINANCIAL ANALYSIS -----------------
elif menu == "Financial Analysis":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Daily Collection & Financials</h4>', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT bill_id, patient_id, test_name, test_price, paid_amount, status, created_at FROM tests_billing ORDER BY bill_id DESC")
    bills_data = c.fetchall()
    conn.close()
    if bills_data:
        df_bills = pd.DataFrame(bills_data, columns=["Bill ID", "Patient ID", "Test", "Price", "Paid", "Status", "Date"])
        st.dataframe(df_bills, use_container_width=True)
        st.metric("Total Counter Collection", f"₹ {df_bills['Paid'].sum():,.2f}")
    else:
        st.info("Koi billing record nahi hai.")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 7: TESTS & RATE LIST -----------------
elif menu == "Tests & Rate List":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Diagnostic Directory & Rates</h4>', unsafe_allow_html=True)
    test_data = {
        "Test Name": ["Complete Blood Count (CBC)", "Hemoglobin (Hb)", "ESR", "Blood Glucose - Fasting", "Blood Glucose - PP", "HbA1c", "Liver Function Test (LFT)", "Kidney Function Test (KFT)", "Lipid Profile", "Thyroid Profile (T3, T4, TSH)", "Basic Health Package", "Full Body Checkup"],
        "Department": ["Hematology", "Hematology", "Hematology", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Endocrinology", "Package", "Package"],
        "Price (₹)": [350, 80, 100, 80, 80, 450, 650, 600, 700, 500, 1299, 2499]
    }
    st.dataframe(pd.DataFrame(test_data), use_container_width=True, height=450)
    st.markdown('</div>', unsafe_allow_html=True)
