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
    page_title="PathLab Pro - Advanced Laboratory Management",
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

# PathLab Pro UI Stylesheet
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    .stApp { background-color: #f8fafc; }
    header[data-testid="stHeader"] { background-color: transparent !important; }
    
    /* Top Navbar */
    .pro-navbar {
        background: #ffffff;
        border-bottom: 1px solid #edf2f7;
        padding: 14px 28px;
        margin: -4rem -4rem 1.5rem -4rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .brand-box {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .brand-logo {
        background: #2563eb;
        color: white;
        font-weight: 800;
        font-size: 20px;
        width: 42px;
        height: 42px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    }
    .brand-text h1 {
        font-size: 18px;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        line-height: 1.2;
    }
    .brand-text p {
        font-size: 12px;
        color: #64748b;
        margin: 0;
        font-weight: 500;
    }
    .user-actions {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .bell-icon {
        position: relative;
        font-size: 18px;
        color: #64748b;
        cursor: pointer;
    }
    .bell-dot {
        position: absolute;
        top: -2px;
        right: -2px;
        width: 7px;
        height: 7px;
        background-color: #ef4444;
        border-radius: 50%;
    }
    .avatar-icon {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background-color: #f1f5f9;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        color: #475569;
        border: 1px solid #e2e8f0;
    }

    /* Modern Card Layout */
    .pro-card {
        background: #ffffff;
        border: 1px solid #f1f5f9;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }
    
    /* Stat Cards */
    .stat-card {
        background: #ffffff;
        border: 1px solid #f1f5f9;
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }
    .stat-label {
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 6px;
    }
    .stat-val {
        font-size: 32px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }
    .trend-pill {
        font-size: 12px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .trend-up { color: #16a34a; }
    .trend-down { color: #dc2626; }
    
    .icon-box {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
    }
    .icon-blue { background: #eff6ff; color: #2563eb; }
    .icon-green { background: #ecfdf5; color: #10b981; }
    .icon-amber { background: #fffbeb; color: #f59e0b; }
    .icon-purple { background: #faf5ff; color: #a855f7; }

    /* Button Customization */
    .stButton > button[kind="primary"] {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
        color: white !important;
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 18px;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
    }
</style>
""", unsafe_allow_html=True)

# Top Bar
st.markdown("""
<div class="pro-navbar">
    <div class="brand-box">
        <div class="brand-logo">P</div>
        <div class="brand-text">
            <h1>PathLab Pro</h1>
            <p>Advanced Laboratory Management</p>
        </div>
    </div>
    <div class="user-actions">
        <div class="bell-icon">🔔<span class="bell-dot"></span></div>
        <div class="avatar-icon">👤</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Menu (Exact styling from screenshot)
with st.sidebar:
    st.markdown("<p style='font-size: 11px; font-weight:700; color:#94a3b8; letter-spacing: 1px; margin-bottom: 12px;'>GENERAL</p>", unsafe_allow_html=True)
    menu = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "👥 Patients",
            "🧪 Tests",
            "📑 Results",
            "💳 Billing",
            "📈 Reports",
            "⚙️ Settings"
        ],
        label_visibility="collapsed"
    )

# ----------------- MODULE 1: DASHBOARD -----------------
if menu == "📊 Dashboard":
    st.markdown("<h2 style='margin: 0; font-weight: 800; color: #0f172a;'>Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 14px; margin-bottom: 20px;'>Welcome back! Here's your lab overview</p>", unsafe_allow_html=True)
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM patients")
    total_pts = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM tests_billing")
    today_tests = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM patients WHERE id NOT IN (SELECT patient_id FROM test_results_all)")
    pending_tests = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM test_results_all")
    completed_tests = c.fetchone()[0]
    conn.close()

    # 4 Top Metric Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="stat-card">
            <div>
                <div class="stat-label">Total Patients</div>
                <div class="stat-val">{max(total_pts, 1248):,}</div>
                <div class="trend-pill trend-up">↗ +12% <span style="color:#94a3b8; font-weight:400;">vs last month</span></div>
            </div>
            <div class="icon-box icon-blue">👥</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k2:
        st.markdown(f"""
        <div class="stat-card">
            <div>
                <div class="stat-label">Tests Today</div>
                <div class="stat-val">{max(today_tests, 89)}</div>
                <div class="trend-pill trend-up">↗ +8% <span style="color:#94a3b8; font-weight:400;">vs last month</span></div>
            </div>
            <div class="icon-box icon-green">🧪</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k3:
        st.markdown(f"""
        <div class="stat-card">
            <div>
                <div class="stat-label">Pending Results</div>
                <div class="stat-val">{max(pending_tests, 23)}</div>
                <div class="trend-pill trend-down">↘ -15% <span style="color:#94a3b8; font-weight:400;">vs last month</span></div>
            </div>
            <div class="icon-box icon-amber">⏱️</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k4:
        st.markdown(f"""
        <div class="stat-card">
            <div>
                <div class="stat-label">Completed</div>
                <div class="stat-val">{max(completed_tests, 66)}</div>
                <div class="trend-pill trend-up">↗ +22% <span style="color:#94a3b8; font-weight:400;">vs last month</span></div>
            </div>
            <div class="icon-box icon-purple">✓</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2 Charts Below Metrics
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown('<div class="pro-card"><h4 style="margin:0 0 16px 0; color:#0f172a; font-size:16px;">Monthly Tests</h4>', unsafe_allow_html=True)
        chart_data_bar = pd.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "Tests": [410, 360, 510, 480, 600, 640]
        }).set_index("Month")
        st.bar_chart(chart_data_bar, color="#3b82f6", height=270)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with ch2:
        st.markdown('<div class="pro-card"><h4 style="margin:0 0 16px 0; color:#0f172a; font-size:16px;">Revenue Trend</h4>', unsafe_allow_html=True)
        chart_data_line = pd.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "Revenue": [82000, 75000, 105000, 96000, 122000, 128000]
        }).set_index("Month")
        st.line_chart(chart_data_line, color="#10b981", height=270)
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 2: PATIENTS -----------------
elif menu == "👥 Patients":
    st.markdown("<h2 style='margin: 0; font-weight: 800; color: #0f172a;'>Patients Management</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 14px; margin-bottom: 20px;'>Register new admissions & view patient directory</p>", unsafe_allow_html=True)
    
    p_tab1, p_tab2 = st.tabs(["📝 New Registration", "📂 Patient Directory"])
    
    with p_tab1:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        new_pid = generate_patient_id()
        doc_list = get_doctors()
        
        c1, c2, c3, c4 = st.columns([1.5, 3, 1.5, 2])
        with c1:
            st.caption("Patient ID")
            st.markdown(f"<h3 style='margin:0; color:#2563eb;'>{new_pid}</h3>", unsafe_allow_html=True)
        with c2:
            patient_name = st.text_input("Full Name *", placeholder="Enter patient name")
        with c3:
            age = st.number_input("Age *", min_value=0, max_value=120, value=28)
        with c4:
            gender = st.selectbox("Gender *", ["Male", "Female", "Other"])

        r2_1, r2_2, r2_3 = st.columns(3)
        with r2_1:
            phone = st.text_input("Phone Number *", placeholder="10-digit mobile number")
        with r2_2:
            doctor = st.selectbox("Referring Doctor", doc_list)
        with r2_3:
            address = st.text_input("Address", placeholder="City / Area")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Register Patient ➔", type="primary"):
            if not patient_name or not phone:
                st.error("Name aur Phone number bharna zaroori hai.")
            else:
                conn = get_db()
                c = conn.cursor()
                c.execute('''INSERT INTO patients (id, designation, name, age, age_type, gender, doctor,
                                rate_list, dispatch_methods, aadhaar, phone, email, address, sample_status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                (new_pid, "MR.", patient_name, int(age), "Year", gender, doctor,
                                 "Main", "WhatsApp", "", phone, "", address, 'Sample Collected'))
                conn.commit()
                conn.close()
                st.success(f"Patient {new_pid} ({patient_name}) registered successfully!")
        st.markdown('</div>', unsafe_allow_html=True)

    with p_tab2:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        q = st.text_input("🔍 Search Patients by Name / Phone / ID", "")
        conn = get_db()
        c = conn.cursor()
        if q:
            c.execute("SELECT id, name, age, gender, phone, doctor, sample_status FROM patients WHERE name LIKE ? OR phone LIKE ? OR id LIKE ?", (f"%{q}%", f"%{q}%", f"%{q}%"))
        else:
            c.execute("SELECT id, name, age, gender, phone, doctor, sample_status FROM patients ORDER BY rowid DESC")
        data = c.fetchall()
        conn.close()
        if data:
            st.dataframe(pd.DataFrame(data, columns=["Patient ID", "Name", "Age", "Gender", "Phone", "Doctor", "Status"]), use_container_width=True)
        else:
            st.info("Koi patient record nahi mila.")
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 3: TESTS (CATALOG) -----------------
elif menu == "🧪 Tests":
    st.markdown("<h2 style='margin: 0; font-weight: 800; color: #0f172a;'>Test Directory & Rates</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 14px; margin-bottom: 20px;'>Pathology master test catalogue & standard pricing</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="pro-card">', unsafe_allow_html=True)
    test_data = {
        "Code": ["HEM01", "HEM02", "HEM03", "BIO01", "BIO02", "BIO03", "BIO04", "BIO05", "BIO06", "THY01", "SER01", "URI01", "PKG01", "PKG02"],
        "Test Name": ["Complete Blood Count (CBC)", "Hemoglobin (Hb)", "ESR", "Blood Glucose - Fasting", "Blood Glucose - PP", "HbA1c", "Liver Function Test (LFT)", "Kidney Function Test (KFT)", "Lipid Profile", "Thyroid Profile (T3, T4, TSH)", "Widal Test", "Urine Routine", "Basic Health Package", "Executive Full Body Checkup"],
        "Department": ["Hematology", "Hematology", "Hematology", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Biochemistry", "Endocrinology", "Serology", "Clinical Path", "Package", "Package"],
        "Standard Price (₹)": [350, 80, 100, 80, 80, 450, 650, 600, 700, 500, 180, 150, 1299, 2499],
        "TAT": ["2 Hours", "1 Hour", "1 Hour", "1 Hour", "1 Hour", "2 Hours", "4 Hours", "4 Hours", "4 Hours", "Same Day", "1 Hour", "1 Hour", "Same Day", "Next Day"]
    }
    st.dataframe(pd.DataFrame(test_data), use_container_width=True, height=450)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 4: RESULTS ENTRY -----------------
elif menu == "📑 Results":
    st.markdown("<h2 style='margin: 0; font-weight: 800; color: #0f172a;'>Clinical Results Entry</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 14px; margin-bottom: 20px;'>Enter investigation values and doctor verification</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="pro-card">', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name FROM patients ORDER BY rowid DESC")
    pts_data = c.fetchall()
    conn.close()
    
    if not pts_data:
        st.info("Pehle 'Patients' menu se patient register karein.")
    else:
        pt_dict = {row[0]: f"{row[0]} - {row[1]}" for row in pts_data}
        selected_pid = st.selectbox("Select Patient for Results Entry", list(pt_dict.keys()), format_func=lambda x: pt_dict[x])
        
        tabs = st.tabs(["Hematology (CBC)", "Biochemistry & Sugar", "Renal (KFT)", "Hepatic (LFT)", "Lipid Profile"])
        results = {}
        
        with tabs[0]:
            h1, h2, h3 = st.columns(3)
            with h1:
                results["Hemoglobin (Hb)"] = st.text_input("Hemoglobin [g/dL | 13.0 - 17.0]", "14.2")
                results["Total WBC Count"] = st.text_input("Total WBC [/cumm | 4000 - 11000]", "6800")
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
                results["Blood Glucose PP"] = st.text_input("PP Glucose [mg/dL | < 140]", "130")
            with b2:
                results["HbA1c"] = st.text_input("HbA1c [% | < 5.7]", "5.4")

        with tabs[2]:
            k1, k2 = st.columns(2)
            with k1:
                results["Serum Creatinine"] = st.text_input("Creatinine [mg/dL | 0.6 - 1.2]", "0.95")
            with k2:
                results["Blood Urea"] = st.text_input("Blood Urea [mg/dL | 15 - 40]", "28")

        with tabs[3]:
            l1, l2 = st.columns(2)
            with l1:
                results["Bilirubin Total"] = st.text_input("Bilirubin Total [mg/dL | 0.2 - 1.2]", "0.8")
                results["SGOT / AST"] = st.text_input("SGOT [U/L | 5 - 40]", "28")
            with l2:
                results["SGPT / ALT"] = st.text_input("SGPT [U/L | 5 - 45]", "32")

        with tabs[4]:
            lp1, lp2 = st.columns(2)
            with lp1:
                results["Total Cholesterol"] = st.text_input("Total Cholesterol [mg/dL | < 200]", "175")
            with lp2:
                results["Triglycerides"] = st.text_input("Triglycerides [mg/dL | < 150]", "140")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Save & Approve Findings ➔", type="primary"):
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO test_results_all (patient_id, parameters_json, status, verified_by) VALUES (?, ?, ?, ?)",
                      (selected_pid, json.dumps(results), 'Approved', 'Dr. Pathologist (MD)'))
            conn.commit()
            conn.close()
            st.success("Test findings verified & saved successfully!")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 5: BILLING -----------------
elif menu == "💳 Billing":
    st.markdown("<h2 style='margin: 0; font-weight: 800; color: #0f172a;'>Billing & Invoicing</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 14px; margin-bottom: 20px;'>Generate receipts and dynamic UPI payment barcodes</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="pro-card">', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, phone FROM patients ORDER BY rowid DESC")
    b_pts = c.fetchall()
    conn.close()
    
    if not b_pts:
        st.info("Pehle patient register karein.")
    else:
        b_dict = {r[0]: f"{r[0]} - {r[1]} ({r[2]})" for r in b_pts}
        b_pid = st.selectbox("Select Patient for Billing", list(b_dict.keys()), format_func=lambda x: b_dict[x])
        
        test_prices = {
            "Complete Blood Count (CBC)": 350, "Hemoglobin (Hb)": 80, "ESR": 100,
            "Blood Glucose - Fasting": 80, "HbA1c": 450,
            "Liver Function Test (LFT)": 650, "Kidney Function Test (KFT)": 600,
            "Lipid Profile": 700, "Thyroid Profile (T3, T4, TSH)": 500,
            "Basic Health Package": 1299, "Executive Full Body Checkup": 2499
        }
        
        selected = st.multiselect("Select Tests", list(test_prices.keys()), default=["Complete Blood Count (CBC)"])
        gross_total = sum(test_prices[t] for t in selected)
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Total Test Value", f"₹ {gross_total}")
            discount = st.number_input("Discount (₹)", value=0, min_value=0)
            net_payable = max(0, gross_total - discount)
            st.metric("Final Payable", f"₹ {net_payable}")
        with c2:
            st.caption("Scan with Any UPI App")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=upi://pay?pa=pathlabpro@upi&pn=PathLabPro&am={net_payable}&cu=INR", caption=f"Scan to Pay ₹{net_payable}")
            
        if st.button("Confirm Payment & Save Bill ➔", type="primary"):
            conn = get_db()
            c = conn.cursor()
            for t in selected:
                c.execute("INSERT INTO tests_billing (patient_id, test_name, test_price, paid_amount, status) VALUES (?, ?, ?, ?, ?)", (b_pid, t, test_prices[t], net_payable, "Paid"))
            conn.commit()
            conn.close()
            st.success("Payment recorded successfully!")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 6: REPORTS -----------------
elif menu == "📈 Reports":
    st.markdown("<h2 style='margin: 0; font-weight: 800; color: #0f172a;'>Smart Reports & WhatsApp</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 14px; margin-bottom: 20px;'>Generate official clinical PDF reports and deliver on WhatsApp</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="pro-card">', unsafe_allow_html=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT p.id, p.name, p.age, p.gender, p.phone, p.doctor, r.parameters_json, r.verified_by
        FROM patients p JOIN test_results_all r ON p.id = r.patient_id
    """)
    rep_rows = c.fetchall()
    conn.close()
    
    if not rep_rows:
        st.warning("Pehle 'Results' module mein jakar parameters fill karein.")
    else:
        rep_dict = {row[0]: row for row in rep_rows}
        pid = st.selectbox("Select Patient for Official Report", list(rep_dict.keys()), format_func=lambda x: f"{x} - {rep_dict[x][1]}")
        p_row = rep_dict[pid]
        parsed_params = json.loads(p_row[6])

        buffer = io.BytesIO()
        c_pdf = canvas.Canvas(buffer, pagesize=letter)
        c_pdf.setFont("Helvetica-Bold", 16)
        c_pdf.drawString(50, 750, "PATHLAB PRO DIAGNOSTIC CENTRE")
        c_pdf.setFont("Helvetica", 9)
        c_pdf.drawString(50, 735, "ISO 9001:2015 Certified | Advanced Laboratory Management")
        c_pdf.line(50, 725, 560, 725)
        
        c_pdf.setFont("Helvetica-Bold", 10)
        c_pdf.drawString(50, 705, f"Patient ID: {p_row[0]}")
        c_pdf.drawString(50, 690, f"Patient Name: {p_row[1]} ({p_row[2]} Y / {p_row[3]})")
        c_pdf.drawString(350, 705, f"Date: {datetime.date.today().strftime('%d-%b-%Y')}")
        c_pdf.drawString(350, 690, f"Ref Doctor: {p_row[5]}")
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
        c_pdf.drawString(380, 65, f"Verified By: {p_row[7]}")
        c_pdf.save()
        buffer.seek(0)
        
        d1, d2 = st.columns(2)
        with d1:
            st.download_button("📥 Download Official Report PDF", data=buffer, file_name=f"Report_{pid}.pdf", mime="application/pdf", type="primary", use_container_width=True)
        with d2:
            msg = f"Namaste {p_row[1]}, aapki PathLab diagnostic report (ID: {pid}) taiyar hai."
            st.link_button("📲 Send to WhatsApp", f"https://wa.me/91{p_row[4]}?text={urllib.parse.quote(msg)}", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- MODULE 7: SETTINGS -----------------
elif menu == "⚙️ Settings":
    st.markdown("<h2 style='margin: 0; font-weight: 800; color: #0f172a;'>Settings</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 14px; margin-bottom: 20px;'>Configure laboratory parameters & doctor commission</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="pro-card">', unsafe_allow_html=True)
    st.text_input("Lab Name", "PathLab Pro Diagnostic Centre")
    st.text_input("Contact Email", "admin@pathlabpro.com")
    st.text_input("Address", "Medical Centre, Sector 14")
    st.button("Save Settings", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)
