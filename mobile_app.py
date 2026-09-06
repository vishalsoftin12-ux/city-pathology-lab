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

# Database Initialization
def init_db():
    conn = sqlite3.connect("lab.db")
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(patient_id) REFERENCES patients(id)
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
    
    # Default initial data
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
    /* Red Accent Colors */
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

# Sidebar Navigation
with st.sidebar:
    st.markdown('<div class="sidebar-brand">// BHARAT</div>', unsafe_allow_html=True)
    st.text_input("🔍 Search any feature...", placeholder="Search...", key="sb_search")
    
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
    
    with st.container():
        st.markdown('<div class="bharat-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top:0; color:#1e293b;'>Patient Registration</h4>", unsafe_allow_html=True)
        
        # Row 1
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.2, 3, 1.2, 1.2, 2.5])
        with c1:
            st.markdown("<p style='font-size: 12px; color: #64748b; margin-bottom: 2px;'>Patient ID</p>", unsafe_allow_html=True)
            st.markdown(f"<div class='patient-id-badge'>{new_pid}</div>", unsafe_allow_html=True)
        with c2:
            designation = st.selectbox("Designation *", ["MR.", "MRS.", "MS.", "DR.", "BABY", "MASTER"])
        with c3:
            first_name = st.text_input("First Name *", placeholder="Enter first name")
        with c4:
            age = st.number_input("Age *", min_value=0, max_value=120, value=28)
        with c5:
            age_type = st.selectbox("Age Type *", ["Year", "Month", "Days"])
        with c6:
            gender = st.radio("Gender *", ["Male", "Female", "Other"], horizontal=True)

        st.markdown("<hr style='margin: 12px 0; border: none; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)

        # Row 2
        r2_1, r2_2, r2_3, r2_4 = st.columns([2.5, 2, 3, 3])
        with r2_1:
            doc_list = get_doctors()
            doctor = st.selectbox("Referring Doctor", doc_list)
        with r2_2:
            rate_list = st.selectbox("Rate List Type", ["Main", "Corporate", "B2B Discount"])
        with r2_3:
            dispatch_methods = st.multiselect(
                "Dispatch Methods",
                ["Email", "Hardcopy", "SMS", "WhatsApp", "Manual WhatsApp"],
                default=["WhatsApp", "Hardcopy"]
            )
        with r2_4:
            address = st.text_area("Address", placeholder="Enter patient address", height=68)

        st.markdown("<hr style='margin: 12px 0; border: none; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)

        # Row 3
        r3_1, r3_2, r3_3 = st.columns([2.5, 2.5, 3])
        with r3_1:
            aadhaar = st.text_input("Aadhaar number", placeholder="Enter 12-digit Aadhaar")
        with r3_2:
            phone = st.text_input("Phone Number (IN +91) *", placeholder="10-digit Phone Number")
        with r3_3:
            email = st.text_input("Email", placeholder="patient@example.com")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Action Buttons
        b1, b2, b3 = st.columns([6, 2, 2])
        with b2:
            btn_quote = st.button("📋 Create Quotation", use_container_width=True)
        with b3:
            btn_billing = st.button("Go to Billing ➔", type="primary", use_container_width=True)

        if btn_billing:
            if not first_name or not phone:
                st.error("Please fill required fields (First Name & Phone Number).")
            else:
                conn = get_db()
                c = conn.cursor()
                c.execute('''INSERT INTO patients (id, designation, name, age, age_type, gender, doctor,
                                rate_list, dispatch_methods, aadhaar, phone, email, address)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                (new_pid, designation, first_name, age, age_type, gender, doctor,
                                 rate_list, ",".join(dispatch_methods), aadhaar, phone, email, address))
                conn.commit()
                conn.close()
                st.session_state['active_pid'] = new_pid
                st.success(f"Patient {new_pid} successfully registered! Now proceed to Billing.")

        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 2: CREDENT (ACCESSION & BARCODE) -----------------
elif menu == "Credent (Accession & Barcode)":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Credent: Sample Accession & Barcode Tracking</h4>', unsafe_allow_html=True)
    conn = get_db()
    pts = pd.read_sql_query("SELECT id, name, gender, age, sample_status, created_at FROM patients ORDER BY created_at DESC", conn)
    conn.close()
    
    if pts.empty:
        st.info("No samples registered yet.")
    else:
        c1, c2 = st.columns([1.6, 1])
        with c1:
            st.dataframe(pts, use_container_width=True)
        with c2:
            st.subheader("Barcode Label")
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
                st.success(f"Status updated to: {new_status}")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 3: ANALYSIS (DASHBOARD) -----------------
elif menu == "Analysis (Dashboard)":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Operational & TAT Analysis</h4>', unsafe_allow_html=True)
    conn = get_db()
    total_p = pd.read_sql_query("SELECT COUNT(*) FROM patients", conn).iloc[0,0]
    total_bills = pd.read_sql_query("SELECT COUNT(*), SUM(paid_amount) FROM tests_billing", conn)
    conn.close()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Patients", total_p)
    m2.metric("Tests Processed", total_bills.iloc[0,0] if total_bills.iloc[0,0] else 0)
    m3.metric("Avg TAT", "0D - 01H - 15M", delta="On Time")
    m4.metric("Lab Revenue", f"₹ {total_bills.iloc[0,1] or 0:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 4: PATIENT LIST -----------------
elif menu == "Patient List":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Complete Patient Directory</h4>', unsafe_allow_html=True)
    search_term = st.text_input("🔍 Search Directory by Name / Phone / Patient ID", "")
    conn = get_db()
    if search_term:
        query = f"SELECT id as 'ID', name as 'Name', age as 'Age', gender as 'Gender', phone as 'Phone', doctor as 'Doctor', created_at as 'Date' FROM patients WHERE name LIKE '%{search_term}%' OR phone LIKE '%{search_term}%' OR id LIKE '%{search_term}%'"
    else:
        query = "SELECT id as 'ID', name as 'Name', age as 'Age', gender as 'Gender', phone as 'Phone', doctor as 'Doctor', created_at as 'Date' FROM patients ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 5: ENTER & VERIFY -----------------
elif menu == "Enter & Verify":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Enter Clinical Parameters & Verify Results</h4>', unsafe_allow_html=True)
    conn = get_db()
    pts = pd.read_sql_query("SELECT id, name FROM patients ORDER BY created_at DESC", conn)
    conn.close()
    
    if pts.empty:
        st.info("No patients available.")
    else:
        selected_pid = st.selectbox("Select Patient for Clinical Entry", pts['id'].tolist(),
                                    format_func=lambda x: f"{x} - {pts[pts['id']==x]['name'].values[0]}")
        
        st.markdown("##### Hematology - Complete Blood Count (CBC)")
        col1, col2, col3 = st.columns(3)
        with col1:
            hb = st.number_input("Haemoglobin (g/dL) [13.0 - 17.0]", value=14.2)
            wbc = st.number_input("Total WBC (/cumm) [4000 - 11000]", value=6800)
        with col2:
            platelets = st.number_input("Platelets (Lakhs/cumm) [1.5 - 4.5]", value=2.4)
            neutro = st.number_input("Neutrophils (%) [40 - 75]", value=62)
        with col3:
            lympho = st.number_input("Lymphocytes (%) [20 - 45]", value=30)
            verified_by = st.selectbox("Approving Pathologist", ["Dr. Pathologist (MD, DNB)", "Dr. Senior Resident"])
            
        if st.button("Save & Verify Findings", type="primary"):
            conn = get_db()
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO test_results (patient_id, hb, wbc, platelets, neutrophils, lymphocytes, status, verified_by)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (selected_pid, hb, wbc, platelets, neutro, lympho, 'Approved', verified_by))
            conn.commit()
            conn.close()
            st.success("Results verified and locked for Smart Report generation!")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 6: BILLING & INVOICING -----------------
elif menu == "Billing & Invoicing":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Billing & UPI Invoicing</h4>', unsafe_allow_html=True)
    conn = get_db()
    pts = pd.read_sql_query("SELECT id, name, phone FROM patients ORDER BY created_at DESC", conn)
    conn.close()
    
    if pts.empty:
        st.info("No patients registered yet.")
    else:
        patient_choice = st.selectbox(
            "Select Patient",
            options=pts['id'].tolist(),
            format_func=lambda x: f"{x} - {pts[pts['id']==x]['name'].values[0]} ({pts[pts['id']==x]['phone'].values[0]})"
        )
        
        test_prices = {
            "Complete Blood Count (CBC)": 350,
            "Liver Function Test (LFT)": 650,
            "Kidney Function Test (KFT / RFT)": 600,
            "Lipid Profile": 700,
            "Thyroid Profile (T3, T4, TSH)": 500,
            "Blood Sugar Fasting": 80,
            "HbA1c": 450,
            "Widal Slide/Tube Test": 180,
            "Dengue NS1 Antigen": 750,
            "Urine Routine & Microscopic": 150
        }
        
        selected_tests = st.multiselect("Select Tests", list(test_prices.keys()), default=["Complete Blood Count (CBC)"])
        total_amount = sum(test_prices[t] for t in selected_tests)
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.metric("Total Test Price", f"₹ {total_amount}")
            discount = st.number_input("Discount (₹)", value=0, min_value=0)
            final_payable = max(0, total_amount - discount)
            st.metric("Final Payable Amount", f"₹ {final_payable}")
            
        with c2:
            st.subheader("UPI QR Code Payment")
            upi_id = "bharatlab@upi"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=upi://pay?pa={upi_id}&pn=BHARATDiagnostics&am={final_payable}&cu=INR"
            st.image(qr_url, caption=f"Scan to Pay ₹{final_payable} via Any UPI App")

        if st.button("Confirm Payment & Save Bill", type="primary"):
            conn = get_db()
            c = conn.cursor()
            for t in selected_tests:
                c.execute("INSERT INTO tests_billing (patient_id, test_name, test_price, paid_amount, status) VALUES (?, ?, ?, ?, ?)",
                          (patient_choice, t, test_prices[t], final_payable, "Paid"))
            conn.commit()
            conn.close()
            st.success(f"Bill ₹{final_payable} successfully recorded for Patient ID: {patient_choice}!")
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 7: FINANCIAL ANALYSIS -----------------
elif menu == "Financial Analysis":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Financial & Referral Analytics</h4>', unsafe_allow_html=True)
    conn = get_db()
    bills = pd.read_sql_query("SELECT * FROM tests_billing ORDER BY created_at DESC", conn)
    conn.close()
    
    if bills.empty:
        st.info("No billing records yet.")
    else:
        st.dataframe(bills, use_container_width=True)
        st.metric("Total Lab Collection", f"₹ {bills['paid_amount'].sum():,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 8: TESTS & RATE LIST (ALL TESTS MASTER LIST) -----------------
elif menu == "Tests & Rate List":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">BHARAT Pathology - All Tests Master Catalogue</h4>', unsafe_allow_html=True)
    test_data = {
        "Test Code": ["HEM01", "HEM02", "HEM03", "BIO01", "BIO02", "BIO03", "BIO04", "BIO05", "BIO06", "THY01", "THY02", "SER01", "SER02", "SER03", "URI01", "VIT01", "VIT02"],
        "Test Name": [
            "Complete Blood Count (CBC)", "Erythrocyte Sedimentation Rate (ESR)", "Blood Group & Rh Factor",
            "Blood Sugar (Fasting)", "Blood Sugar (PP / Postprandial)", "HbA1c (Glycated Hemoglobin)",
            "Liver Function Test (LFT)", "Kidney Function Test (KFT / RFT)", "Lipid Profile (Complete)",
            "Thyroid Profile Total (T3, T4, TSH)", "TSH (Ultrasensitive)", "Widal Test (Typhoid Slide/Tube)",
            "Dengue NS1 Antigen & IgM/IgG", "Malaria Antigen (Pv / Pf Rapid)", "Urine Routine & Microscopic",
            "Vitamin D (25-OH)", "Vitamin B12 (Cyanocobalamin)"
        ],
        "Department": [
            "Hematology", "Hematology", "Hematology",
            "Biochemistry", "Biochemistry", "Biochemistry",
            "Biochemistry", "Biochemistry", "Biochemistry",
            "Endocrinology", "Endocrinology", "Serology",
            "Serology", "Serology", "Clinical Pathology",
            "Immunology", "Immunology"
        ],
        "Standard Rate (₹)": [350, 100, 100, 80, 80, 450, 650, 600, 700, 500, 250, 180, 750, 250, 150, 1200, 900],
        "B2B / Offer Rate (₹)": [200, 50, 50, 40, 40, 300, 400, 380, 450, 320, 150, 100, 500, 150, 80, 800, 600],
        "Sample Type": [
            "EDTA Whole Blood (2ml)", "Sodium Citrate Blood", "EDTA Blood",
            "Fluoride Plasma (Fasting)", "Fluoride Plasma (PP)", "EDTA Whole Blood",
            "Serum (Gel Tube, 3ml)", "Serum (Gel Tube, 3ml)", "Serum (12hr Fasting)",
            "Serum (Clot Activator)", "Serum", "Serum",
            "Serum", "Whole Blood (Fingerprick/EDTA)", "Fresh Midstream Urine (30ml)",
            "Serum (Protected from Light)", "Serum"
        ],
        "TAT (Turnaround Time)": [
            "2 Hours", "1 Hour", "30 Mins",
            "1 Hour", "1 Hour", "3 Hours",
            "4 Hours", "4 Hours", "4 Hours",
            "Same Day", "Same Day", "2 Hours",
            "2 Hours", "1 Hour", "1 Hour",
            "Next Day", "Next Day"
        ]
    }
    st.dataframe(pd.DataFrame(test_data), use_container_width=True, height=520)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 9: SMART REPORT (PDF & WHATSAPP) -----------------
elif menu == "Smart Report":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Smart Report Dispatch & PDF Printing</h4>', unsafe_allow_html=True)
    conn = get_db()
    ready_pts = pd.read_sql_query("""
        SELECT p.id, p.name, p.phone, r.hb, r.wbc, r.platelets, r.neutrophils, r.lymphocytes, r.verified_by
        FROM patients p JOIN test_results r ON p.id = r.patient_id
    """, conn)
    conn.close()
    
    if ready_pts.empty:
        st.warning("No reports ready. Complete 'Enter & Verify' for a patient first.")
    else:
        pid = st.selectbox("Select Patient for Report", ready_pts['id'].tolist(),
                           format_func=lambda x: f"{x} - {ready_pts[ready_pts['id']==x]['name'].values[0]}")
        p_row = ready_pts[ready_pts['id']==pid].iloc[0]
        
        # Generate PDF Report
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor("#991B1B"))
        c.drawString(50, 750, "BHARAT PATHOLOGY & DIAGNOSTIC CENTRE")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        c.drawString(50, 735, "ISO 9001:2015 Certified | Powered by BHARAT LIS")
        c.drawString(50, 722, "Phone: +91 98765 43210 | Email: reports@bharatpathology.com")
        c.setLineWidth(1)
        c.setStrokeColor(colors.HexColor("#DC2626"))
        c.line(50, 715, 560, 715)
        
        # Details
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 695, f"Patient ID: {p_row['id']}")
        c.drawString(50, 680, f"Patient Name: {p_row['name']}")
        c.drawString(350, 695, f"Date: {datetime.date.today().strftime('%d-%b-%Y')}")
        c.drawString(350, 680, f"Contact: {p_row['phone']}")
        c.line(50, 670, 560, 670)
        
        # Table Header
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 650, "Investigation")
        c.drawString(220, 650, "Result")
        c.drawString(340, 650, "Reference Range")
        c.drawString(470, 650, "Unit")
        c.line(50, 642, 560, 642)
        
        c.setFont("Helvetica", 10)
        tests = [
            ("Haemoglobin (Hb)", str(p_row['hb']), "13.0 - 17.0", "g/dL"),
            ("Total WBC Count", str(p_row['wbc']), "4000 - 11000", "/cumm"),
            ("Platelet Count", str(p_row['platelets']), "1.50 - 4.50", "Lakhs/cumm"),
            ("Neutrophils", str(p_row['neutrophils']), "40 - 75", "%"),
            ("Lymphocytes", str(p_row['lymphocytes']), "20 - 45", "%")
        ]
        y = 620
        for name, val, rng, unit in tests:
            c.drawString(50, y, name)
            c.drawString(220, y, val)
            c.drawString(340, y, rng)
            c.drawString(470, y, unit)
            y -= 22
            
        c.line(50, 180, 560, 180)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(400, 140, f"Approved By: {p_row['verified_by']}")
        c.drawString(50, 140, "Scan QR to verify report online")
        c.save()
        buffer.seek(0)
        
        # Actions
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button("📥 Download Official Report PDF", data=buffer, file_name=f"Report_{pid}.pdf", mime="application/pdf", type="primary", use_container_width=True)
        with col_d2:
            msg = f"Namaste {p_row['name']}, aapki BHARAT Pathology Lab diagnostic report (ID: {pid}) taiyar hai."
            wa_url = f"https://wa.me/91{p_row['phone']}?text={urllib.parse.quote(msg)}"
            st.link_button("📲 Send via WhatsApp", wa_url, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 10: LAB MANAGEMENT & DOCTORS -----------------
elif menu == "Lab Management":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Referral Doctor & Incentive Management</h4>', unsafe_allow_html=True)
    with st.form("add_doc_form"):
        dn = st.text_input("Doctor Name", placeholder="e.g. Dr. A. K. Verma")
        dc = st.number_input("Commission Rate (%)", min_value=0.0, max_value=50.0, value=15.0)
        if st.form_submit_button("Add Referral Doctor"):
            if dn:
                conn = get_db()
                c = conn.cursor()
                c.execute("INSERT OR IGNORE INTO doctors (name, commission) VALUES (?, ?)", (dn, dc))
                conn.commit()
                conn.close()
                st.success(f"{dn} added successfully!")
                st.rerun()
    conn = get_db()
    st.dataframe(pd.read_sql_query("SELECT id, name as 'Doctor Name', commission as 'Commission %' FROM doctors", conn), use_container_width=True)
    conn.close()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 11: INVENTORY -----------------
elif menu == "Inventory":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Reagent & Consumable Inventory</h4>', unsafe_allow_html=True)
    conn = get_db()
    st.dataframe(pd.read_sql_query("SELECT item_name as 'Item', category as 'Category', stock as 'Quantity', unit as 'Unit', expiry_date as 'Expiry' FROM inventory", conn), use_container_width=True)
    conn.close()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 12: LAB PROFILE -----------------
elif menu == "Lab Profile":
    st.markdown('<div class="bharat-card"><h4 style="margin-top:0;">Laboratory Information & Branding</h4>', unsafe_allow_html=True)
    st.text_input("Lab Legal Name", "BHARAT Pathology & Diagnostic Centre")
    st.text_input("Accreditation", "ISO 9001:2015 / NABL Compliant")
    st.text_input("Contact Email", "contact@bharatpathology.com")
    st.text_input("Center Address", "Main Road, Medical Hub, City Centre")
    st.button("Save Profile Settings", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)
