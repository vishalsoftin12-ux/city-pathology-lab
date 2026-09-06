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
    page_title="BHARAT LIS - Modern Clinical Workspace",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Database Setup
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

# Modern Clinical UI Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #f1f5f9; }
    
    /* Clinical Navigation Header */
    .clinical-header {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px 24px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .clinical-title {
        font-size: 24px;
        font-weight: 800;
        color: #DC2626;
        letter-spacing: -0.5px;
    }
    .badge-premiere {
        background-color: #FEF2F2;
        color: #DC2626;
        border: 1px solid #FECACA;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
    }
    /* Workspace Card Container */
    .clinical-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
    }
    .dept-heading {
        background-color: #FEF2F2;
        color: #991B1B;
        padding: 10px 16px;
        font-weight: 700;
        font-size: 14px;
        border-left: 4px solid #DC2626;
        border-radius: 4px;
        margin: 16px 0 12px 0;
    }
    /* Tab Navigation Enhancements */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #ffffff;
        padding: 8px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        color: #475569;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FEF2F2 !important;
        color: #DC2626 !important;
        font-weight: 700 !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #DC2626 !important;
        border-color: #DC2626 !important;
        color: white !important;
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# Top Bar
st.markdown("""
<div class="clinical-header">
    <div style="display: flex; align-items: center; gap: 14px;">
        <span class="clinical-title">// BHARAT</span>
        <span class="badge-premiere">CLINICAL WORKSPACE</span>
        <span style="font-size: 14px; font-weight: 600; color: #334155;">Diagnostic & Pathology Information System</span>
    </div>
    <div style="display: flex; align-items: center; gap: 20px; font-size: 13px; color: #64748b;">
        <span>Branch: <b>Main Diagnostic Hub</b></span>
        <span>Status: <b style="color: #16a34a;">● Live Database</b></span>
    </div>
</div>
""", unsafe_allow_html=True)

# Top Tab Navigation Layout
tabs = st.tabs([
    "📝 1. Patient Registration",
    "🏷️ 2. Accession & Barcode",
    "🔬 3. Clinical Results Entry",
    "💳 4. Billing & UPI Pay",
    "📄 5. Smart Report & WhatsApp",
    "📊 6. Directory & Analytics"
])

# ----------------- TAB 1: REGISTRATION -----------------
with tabs[0]:
    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
    new_pid = generate_patient_id()
    doc_list = get_doctors()
    
    st.markdown("#### Patient Admission & Registration Form")
    c1, c2, c3, c4, c5 = st.columns([1.5, 1.2, 3, 1.5, 2.5])
    with c1:
        st.caption("Patient ID")
        st.markdown(f"<h3 style='margin:0; color:#DC2626;'>{new_pid}</h3>", unsafe_allow_html=True)
    with c2:
        designation = st.selectbox("Designation", ["MR.", "MRS.", "MS.", "DR.", "BABY", "MASTER"])
    with c3:
        full_name = st.text_input("Patient Full Name *", placeholder="Enter patient name")
    with c4:
        age = st.number_input("Age *", min_value=0, max_value=120, value=30)
    with c5:
        gender = st.radio("Gender *", ["Male", "Female", "Other"], horizontal=True)

    st.markdown("<hr style='margin: 14px 0; border: none; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)
    
    r2_1, r2_2, r2_3 = st.columns(3)
    with r2_1:
        doctor = st.selectbox("Referring Doctor", doc_list)
    with r2_2:
        phone = st.text_input("Contact Number (IN +91) *", placeholder="10-digit mobile number")
    with r2_3:
        rate_list = st.selectbox("Pricing Scheme", ["Main / Walk-in", "Corporate", "B2B Partner"])

    r3_1, r3_2 = st.columns(2)
    with r3_1:
        aadhaar = st.text_input("Aadhaar / ID Card Number", placeholder="Optional 12-digit number")
    with r3_2:
        address = st.text_input("City / Residential Address", placeholder="Optional address")

    st.markdown("<br>", unsafe_allow_html=True)
    b_left, b_right = st.columns([8, 2])
    with b_right:
        if st.button("Complete Registration ➔", type="primary", use_container_width=True):
            if not full_name or not phone:
                st.error("Full Name aur Mobile Number zaroori hain.")
            else:
                conn = get_db()
                c = conn.cursor()
                c.execute('''INSERT INTO patients (id, designation, name, age, age_type, gender, doctor,
                                rate_list, dispatch_methods, aadhaar, phone, email, address, sample_status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                (new_pid, designation, full_name, int(age), "Year", gender, doctor,
                                 rate_list, "WhatsApp,Hardcopy", aadhaar, phone, "", address, 'Sample Collected'))
                conn.commit()
                conn.close()
                st.success(f"Patient {new_pid} ({full_name}) registered successfully! Ab next tab par proceed karein.")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- TAB 2: ACCESSION & BARCODE -----------------
with tabs[1]:
    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
    st.markdown("#### Sample Accession & Barcode Labeling")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, gender, age, sample_status FROM patients ORDER BY rowid DESC")
    pts_rows = c.fetchall()
    conn.close()
    
    if not pts_rows:
        st.info("Pehle Tab 1 se patient register karein.")
    else:
        df_pts = pd.DataFrame(pts_rows, columns=["Patient ID", "Name", "Gender", "Age", "Sample Status"])
        col_list, col_bc = st.columns([1.8, 1])
        with col_list:
            st.dataframe(df_pts, use_container_width=True, height=280)
        with col_bc:
            sel_pid = st.selectbox("Select Patient for Label", df_pts['Patient ID'].tolist())
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=BHARAT-{sel_pid}"
            st.image(qr_url, caption=f"Vial Barcode: BHARAT-{sel_pid}")
            new_status = st.selectbox("Update Accession Status", ["Sample Collected", "Received at Lab", "In Processing", "Sample Rejected"])
            if st.button("Update Status", type="primary"):
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE patients SET sample_status = ? WHERE id = ?", (new_status, sel_pid))
                conn.commit()
                conn.close()
                st.success("Sample status updated!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- TAB 3: RESULTS ENTRY -----------------
with tabs[2]:
    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
    st.markdown("#### Clinical Investigation & Findings Entry")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name FROM patients ORDER BY rowid DESC")
    pts_list = c.fetchall()
    conn.close()
    
    if not pts_list:
        st.info("Pehle patient register karein.")
    else:
        p_dict = {r[0]: f"{r[0]} - {r[1]}" for r in pts_list}
        selected_pid = st.selectbox("Select Patient for Results", list(p_dict.keys()), format_func=lambda x: p_dict[x])
        
        # Check existing saved data
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT parameters_json FROM test_results_all WHERE patient_id = ?", (selected_pid,))
        saved = c.fetchone()
        conn.close()
        saved_dict = json.loads(saved[0]) if saved and saved[0] else {}

        sub_tabs = st.tabs(["🩸 CBC / Hematology", "🧪 Sugar & Diabetes", "🫘 Renal / KFT", "🩺 Liver / LFT", "🫀 Lipid Panel", "🔬 Urine Analysis"])
        res = {}
        
        with sub_tabs[0]:
            st.markdown('<div class="dept-heading">Complete Blood Count (CBC) with Differential</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                res["Hemoglobin (Hb)"] = st.text_input("Hemoglobin [g/dL | 13.0 - 17.0]", saved_dict.get("Hemoglobin (Hb)", "14.2"))
                res["Total WBC Count"] = st.text_input("Total WBC [/cumm | 4000 - 11000]", saved_dict.get("Total WBC Count", "6800"))
                res["Platelet Count"] = st.text_input("Platelets [Lakhs/cumm | 1.5 - 4.5]", saved_dict.get("Platelet Count", "2.40"))
            with c2:
                res["Neutrophils"] = st.text_input("Neutrophils [% | 40 - 75]", saved_dict.get("Neutrophils", "62"))
                res["Lymphocytes"] = st.text_input("Lymphocytes [% | 20 - 45]", saved_dict.get("Lymphocytes", "30"))
                res["Eosinophils"] = st.text_input("Eosinophils [% | 1 - 6]", saved_dict.get("Eosinophils", "3"))
            with c3:
                res["RBC Count"] = st.text_input("RBC Count [mil/cumm | 4.5 - 5.5]", saved_dict.get("RBC Count", "4.8"))
                res["ESR"] = st.text_input("ESR [mm/hr | 0 - 15]", saved_dict.get("ESR", "10"))
                res["PCV / Hematocrit"] = st.text_input("PCV [% | 40 - 50]", saved_dict.get("PCV / Hematocrit", "42.0"))

        with sub_tabs[1]:
            st.markdown('<div class="dept-heading">Blood Glucose Panel</div>', unsafe_allow_html=True)
            s1, s2 = st.columns(2)
            with s1:
                res["Blood Glucose (Fasting)"] = st.text_input("Glucose Fasting [mg/dL | 70 - 100]", saved_dict.get("Blood Glucose (Fasting)", "95"))
                res["Blood Glucose (PP)"] = st.text_input("Glucose PP [mg/dL | < 140]", saved_dict.get("Blood Glucose (PP)", "130"))
            with s2:
                res["HbA1c (Glycated Hb)"] = st.text_input("HbA1c [% | < 5.7]", saved_dict.get("HbA1c (Glycated Hb)", "5.4"))
                res["Average Blood Glucose"] = st.text_input("Avg Glucose [mg/dL | 90 - 120]", saved_dict.get("Average Blood Glucose", "108"))

        with sub_tabs[2]:
            st.markdown('<div class="dept-heading">Renal / Kidney Function Test</div>', unsafe_allow_html=True)
            k1, k2 = st.columns(2)
            with k1:
                res["Serum Creatinine"] = st.text_input("Serum Creatinine [mg/dL | 0.6 - 1.2]", saved_dict.get("Serum Creatinine", "0.95"))
                res["Blood Urea"] = st.text_input("Blood Urea [mg/dL | 15 - 40]", saved_dict.get("Blood Urea", "28.0"))
            with k2:
                res["Serum Uric Acid"] = st.text_input("Serum Uric Acid [mg/dL | 3.5 - 7.2]", saved_dict.get("Serum Uric Acid", "4.8"))
                res["Serum Calcium"] = st.text_input("Serum Calcium [mg/dL | 8.8 - 10.2]", saved_dict.get("Serum Calcium", "9.4"))

        with sub_tabs[3]:
            st.markdown('<div class="dept-heading">Liver Function Test (LFT)</div>', unsafe_allow_html=True)
            l1, l2 = st.columns(2)
            with l1:
                res["Bilirubin Total"] = st.text_input("Bilirubin Total [mg/dL | 0.2 - 1.2]", saved_dict.get("Bilirubin Total", "0.8"))
                res["Bilirubin Direct"] = st.text_input("Bilirubin Direct [mg/dL | 0.0 - 0.3]", saved_dict.get("Bilirubin Direct", "0.2"))
                res["SGOT / AST"] = st.text_input("SGOT [U/L | 5 - 40]", saved_dict.get("SGOT / AST", "28"))
            with l2:
                res["SGPT / ALT"] = st.text_input("SGPT [U/L | 5 - 45]", saved_dict.get("SGPT / ALT", "32"))
                res["Alkaline Phosphatase (ALP)"] = st.text_input("ALP [U/L | 30 - 120]", saved_dict.get("Alkaline Phosphatase (ALP)", "75"))
                res["Total Protein"] = st.text_input("Total Protein [g/dL | 6.0 - 8.3]", saved_dict.get("Total Protein", "7.2"))

        with sub_tabs[4]:
            st.markdown('<div class="dept-heading">Lipid Profile & Cardiac Markers</div>', unsafe_allow_html=True)
            lp1, lp2 = st.columns(2)
            with lp1:
                res["Total Cholesterol"] = st.text_input("Total Cholesterol [mg/dL | < 200]", saved_dict.get("Total Cholesterol", "175"))
                res["Serum Triglycerides"] = st.text_input("Triglycerides [mg/dL | < 150]", saved_dict.get("Serum Triglycerides", "140"))
            with lp2:
                res["HDL Cholesterol (Good)"] = st.text_input("HDL Cholesterol [mg/dL | > 40]", saved_dict.get("HDL Cholesterol (Good)", "46"))
                res["LDL Cholesterol (Bad)"] = st.text_input("LDL Cholesterol [mg/dL | < 100]", saved_dict.get("LDL Cholesterol (Bad)", "98"))

        with sub_tabs[5]:
            st.markdown('<div class="dept-heading">Urine Routine & Microscopic Examination</div>', unsafe_allow_html=True)
            u1, u2 = st.columns(2)
            with u1:
                res["Urine Color"] = st.text_input("Color", saved_dict.get("Urine Color", "Pale Yellow, Clear"))
                res["Urine Protein"] = st.selectbox("Protein", ["Nil", "Trace", "+", "++"], index=0)
            with u2:
                res["Urine Sugar"] = st.selectbox("Sugar", ["Nil", "Trace", "+", "++"], index=0)
                res["Urine Pus Cells"] = st.text_input("Pus Cells [/HPF | 2 - 4]", saved_dict.get("Urine Pus Cells", "2 - 3 / HPF"))

        st.markdown("<br>", unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns([7, 3])
        with btn_c2:
            approver = st.selectbox("Approving Authority", ["Dr. Pathologist (MD, DNB)", "Dr. Consultant Pathologist"])
            if st.button("Save & Lock Findings ➔", type="primary", use_container_width=True):
                conn = get_db()
                c = conn.cursor()
                c.execute('''INSERT OR REPLACE INTO test_results_all (patient_id, parameters_json, status, verified_by)
                             VALUES (?, ?, ?, ?)''', (selected_pid, json.dumps(res), 'Approved', approver))
                conn.commit()
                conn.close()
                st.success("Test parameters verified and saved for reporting!")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- TAB 4: BILLING & UPI -----------------
with tabs[3]:
    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
    st.markdown("#### Billing & Dynamic UPI Settlement")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, phone FROM patients ORDER BY rowid DESC")
    b_pts = c.fetchall()
    conn.close()
    
    if not b_pts:
        st.info("Pehle patient register karein.")
    else:
        b_dict = {r[0]: f"{r[0]} - {r[1]} ({r[2]})" for r in b_pts}
        b_pid = st.selectbox("Select Billing Patient", list(b_dict.keys()), format_func=lambda x: b_dict[x])
        
        test_catalog = {
            "Complete Blood Count (CBC)": 350,
            "Blood Glucose - Fasting": 80,
            "Blood Glucose - PP": 80,
            "HbA1c (Glycated Hemoglobin)": 450,
            "Liver Function Test (LFT)": 650,
            "Kidney Function Test (KFT)": 600,
            "Lipid Profile (Full Panel)": 700,
            "Thyroid Profile (T3, T4, TSH)": 500,
            "Widal Slide/Tube Test": 180,
            "Dengue NS1 Antigen": 750,
            "Urine Routine & Microscopic": 150,
            "Vitamin D (25-OH)": 1200,
            "Vitamin B12": 900,
            "BHARAT Basic Health Package": 1299,
            "BHARAT Executive Full Body Package": 2499
        }
        
        tests_chosen = st.multiselect("Select Diagnostic Tests / Packages", list(test_catalog.keys()), default=["Complete Blood Count (CBC)"])
        gross_total = sum(test_catalog[t] for t in tests_chosen)
        
        col_pay_left, col_pay_right = st.columns(2)
        with col_pay_left:
            st.metric("Total Test Amount", f"₹ {gross_total}")
            discount = st.number_input("Discount Applied (₹)", value=0, min_value=0)
            net_payable = max(0, gross_total - discount)
            st.metric("Net Payable Amount", f"₹ {net_payable}")
        with col_pay_right:
            st.caption("Dynamic UPI QR Code")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=upi://pay?pa=bharatlab@upi&pn=BHARATLab&am={net_payable}&cu=INR", caption=f"Scan to Pay ₹{net_payable}")
            
        if st.button("Confirm Payment & Print Bill ➔", type="primary"):
            conn = get_db()
            c = conn.cursor()
            for t in tests_chosen:
                c.execute("INSERT INTO tests_billing (patient_id, test_name, test_price, paid_amount, status) VALUES (?, ?, ?, ?, ?)", 
                          (b_pid, t, test_catalog[t], net_payable, "Paid"))
            conn.commit()
            conn.close()
            st.success(f"Bill for ₹{net_payable} recorded successfully!")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- TAB 5: SMART REPORT -----------------
with tabs[4]:
    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
    st.markdown("#### Official Diagnostic Report & WhatsApp Delivery")
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT p.id, p.designation, p.name, p.age, p.gender, p.phone, p.doctor, r.parameters_json, r.verified_by
        FROM patients p JOIN test_results_all r ON p.id = r.patient_id
    """)
    rep_list = c.fetchall()
    conn.close()
    
    if not rep_list:
        st.warning("Pehle Tab 3 ('Clinical Results Entry') mein parameters save karein.")
    else:
        rep_dict = {r[0]: r for r in rep_list}
        r_pid = st.selectbox("Select Patient for Official Report", list(rep_dict.keys()), format_func=lambda x: f"{x} - {rep_dict[x][2]}")
        patient_data = rep_dict[r_pid]
        p_tests = json.loads(patient_data[7])

        # PDF Generator
        buffer = io.BytesIO()
        c_pdf = canvas.Canvas(buffer, pagesize=letter)
        c_pdf.setFont("Helvetica-Bold", 16)
        c_pdf.setFillColor(colors.HexColor("#991B1B"))
        c_pdf.drawString(50, 750, "BHARAT PATHOLOGY & DIAGNOSTIC CENTRE")
        c_pdf.setFont("Helvetica", 9)
        c_pdf.setFillColor(colors.black)
        c_pdf.drawString(50, 735, "ISO 9001:2015 Certified | Modern Clinical LIS Workspace")
        c_pdf.line(50, 725, 560, 725)
        
        c_pdf.setFont("Helvetica-Bold", 10)
        c_pdf.drawString(50, 705, f"Patient ID: {patient_data[0]}")
        c_pdf.drawString(50, 690, f"Patient: {patient_data[1]} {patient_data[2]} ({patient_data[3]} Y / {patient_data[4]})")
        c_pdf.drawString(340, 705, f"Date: {datetime.date.today().strftime('%d-%b-%Y')}")
        c_pdf.drawString(340, 690, f"Ref Doctor: {patient_data[6]}")
        c_pdf.line(50, 675, 560, 675)
        
        y_pos = 650
        c_pdf.setFont("Helvetica-Bold", 10)
        c_pdf.drawString(50, y_pos, "Investigation")
        c_pdf.drawString(320, y_pos, "Observed Result")
        y_pos -= 20
        
        c_pdf.setFont("Helvetica", 9.5)
        for k, v in p_tests.items():
            if str(v).strip():
                c_pdf.drawString(50, y_pos, str(k)[:40])
                c_pdf.drawString(320, y_pos, str(v))
                y_pos -= 18
                if y_pos < 90:
                    c_pdf.showPage()
                    y_pos = 720
                    c_pdf.setFont("Helvetica", 9.5)
        
        c_pdf.line(50, 80, 560, 80)
        c_pdf.setFont("Helvetica-Bold", 9)
        c_pdf.drawString(380, 65, f"Verified By: {patient_data[8]}")
        c_pdf.save()
        buffer.seek(0)
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button("📥 Download Official Report PDF", data=buffer, file_name=f"Report_{r_pid}.pdf", mime="application/pdf", type="primary", use_container_width=True)
        with col_d2:
            msg = f"Namaste {patient_data[2]}, aapki BHARAT Pathology diagnostic report (ID: {r_pid}) taiyar hai."
            st.link_button("📲 Send to Patient WhatsApp", f"https://wa.me/91{patient_data[5]}?text={urllib.parse.quote(msg)}", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- TAB 6: DIRECTORY & ANALYTICS -----------------
with tabs[5]:
    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
    st.markdown("#### Patient Directory & Financial Overview")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, age, gender, phone, doctor, sample_status, created_at FROM patients ORDER BY rowid DESC")
    pts_all = c.fetchall()
    c.execute("SELECT bill_id, patient_id, test_name, test_price, paid_amount, status, created_at FROM tests_billing ORDER BY bill_id DESC")
    bills_all = c.fetchall()
    conn.close()
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Total Registered Patients", len(pts_all))
    with col_m2:
        tot_coll = sum(b[4] for b in bills_all) if bills_all else 0.0
        st.metric("Total Counter Collection", f"₹ {tot_coll:,.2f}")

    st.markdown("<hr style='margin: 16px 0;'>", unsafe_allow_html=True)
    st.markdown("##### Recent Patients")
    if pts_all:
        st.dataframe(pd.DataFrame(pts_all, columns=["ID", "Name", "Age", "Gender", "Phone", "Doctor", "Status", "Date"]), use_container_width=True)
    else:
        st.info("Koi patient data available nahi hai.")
    st.markdown('</div>', unsafe_allow_html=True)
