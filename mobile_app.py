import streamlit as st
import sqlite3
import os
import urllib.parse
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

st.set_page_config(page_title="City Pathology Lab", page_icon="??", layout="wide")
st.title("?? City Diagnostic & Pathology Lab")

def get_connection():
    return sqlite3.connect("lab.db")

conn = get_connection()
conn.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        age INTEGER,
        gender TEXT,
        referring_doctor TEXT
    )
''')
conn.execute('''
    CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_name TEXT UNIQUE,
        price REAL
    )
''')
conn.execute('''
    CREATE TABLE IF NOT EXISTS billing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        test_name TEXT,
        total_amount REAL,
        paid_amount REAL,
        due_amount REAL,
        status TEXT,
        created_at TEXT
    )
''')
conn.close()

def generate_multi_param_report(p_name, p_phone, p_age, p_gender, p_doc, test_cat, results, report_id, sample_id):
    os.makedirs("reports", exist_ok=True)
    file_path = f"reports/Report_{report_id}_{p_name.replace(' ', '_')}.pdf"
    c = canvas.Canvas(file_path, pagesize=letter)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "CITY DIAGNOSTIC & PATHOLOGY LAB")
    c.setFont("Helvetica", 9)
    c.drawString(50, 735, "Govt. Approved ISO Certified Diagnostic Center | Ph: +91-9876543210")
    c.setStrokeColor(colors.HexColor("#1A365D"))
    c.setLineWidth(1.5)
    c.line(50, 725, 550, 725)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 705, f"Report ID: #{report_id}")
    c.drawString(240, 705, f"Sample Barcode: {sample_id}")
    c.drawString(410, 705, f"Date: {datetime.now().strftime('%d-%m-%Y')}")
    
    c.setFont("Helvetica", 10)
    c.drawString(50, 688, f"Patient Name: {p_name}")
    c.drawString(410, 688, f"Age/Sex: {p_age}Y / {p_gender}")
    c.drawString(50, 672, f"Contact: {p_phone}")
    c.drawString(410, 672, f"Ref: Dr. {p_doc if p_doc else 'Self'}")
    c.line(50, 660, 550, 660)
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 640, f"DEPARTMENT OF INVESTIGATION: {test_cat.upper()}")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 615, "Investigation / Parameter")
    c.drawString(250, 615, "Observed Value")
    c.drawString(360, 615, "Unit")
    c.drawString(440, 615, "Normal Interval")
    c.line(50, 605, 550, 605)
    
    y = 585
    for r in results:
        c.setFont("Helvetica", 9)
        c.drawString(50, y, str(r['param']))
        
        if r['flag'] == "HIGH":
            c.setFillColor(colors.red)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(250, y, f"{r['val']} (HIGH)")
            c.setFillColor(colors.black)
        elif r['flag'] == "LOW":
            c.setFillColor(colors.blue)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(250, y, f"{r['val']} (LOW)")
            c.setFillColor(colors.black)
        else:
            c.drawString(250, y, str(r['val']))
            
        c.setFont("Helvetica", 9)
        c.drawString(360, y, str(r['unit']))
        c.drawString(440, y, str(r['range']))
        y -= 22
        if y < 140:
            c.showPage()
            y = 700

    c.line(50, y - 10, 550, y - 10)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, y - 25, "* Note: Tests performed under automated clinical standards. Correlate clinically.")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(420, y - 65, "Authorized Signatory")
    c.drawString(420, y - 80, "Chief Pathologist")
    c.save()
    return file_path

menu = st.sidebar.radio("Lab Management Menu", [
    "1. Patient Registration",
    "2. Billing & UPI Scan-Pay",
    "3. Clear Pending Dues",
    "4. Enter Multi-Param Test Results",
    "5. Search Patient History",
    "6. Test Rate List Master",
    "7. Admin Dashboard & Backup"
])

if menu == "1. Patient Registration":
    st.subheader("?? New Patient Admission")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Patient Name")
        phone = st.text_input("Mobile Number (10 Digits)")
        age = st.number_input("Age (Years)", 1, 110, 28)
    with col2:
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        doc = st.text_input("Referring Doctor Name", placeholder="e.g. Dr. A. K. Sharma")

    if st.button("Save Patient"):
        if name and phone:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO patients (name, phone, age, gender, referring_doctor) VALUES (?, ?, ?, ?, ?)",
                        (name, phone, age, gender, doc))
            conn.commit()
            conn.close()
            st.success(f"Patient '{name}' successfully register ho gaye!")
        else:
            st.error("Naam aur Mobile Number daalna zaroori hai.")

elif menu == "2. Billing & UPI Scan-Pay":
    st.subheader("?? Billing & Instant UPI Payment")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, phone, referring_doctor FROM patients ORDER BY id DESC")
    patients = cur.fetchall()
    cur.execute("SELECT test_name, price FROM tests ORDER BY test_name ASC")
    tests = cur.fetchall()
    conn.close()

    if patients and tests:
        p_dict = {f"{p[1]} | Mob: {p[2]}": p for p in patients}
        selected_p = p_dict[st.selectbox("Select Registered Patient", list(p_dict.keys()))]

        test_dict = {t[0]: t[1] for t in tests}
        selected_test = st.selectbox("Select Test Category", list(test_dict.keys()))
        price = float(test_dict[selected_test])

        col1, col2 = st.columns(2)
        col1.write(f"**Test Rate:** ? {price}")
        paid = col2.number_input("Amount Collected (?)", 0.0, price, price)
        due = price - paid
        st.write(f"**Balance Due:** ? {due}")

        lab_upi = "labname@upi"
        upi_url = f"upi://pay?pa={lab_upi}&pn=CityPathologyLab&am={paid}&cu=INR"
        qr_image_url = f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data={urllib.parse.quote(upi_url)}"
        
        st.image(qr_image_url, caption=f"Scan to Pay ?{paid} via UPI")

        if st.button("Finalize Bill & WhatsApp"):
            conn = get_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO billing (patient_id, test_name, total_amount, paid_amount, due_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (selected_p[0], selected_test, price, paid, due, "Paid" if due == 0 else "Due", datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            bill_id = cur.lastrowid
            conn.close()

            sample_code = f"LAB-{bill_id:04d}"
            msg = f"City Pathology Lab\nReceipt ID: #{bill_id}\nPatient: {selected_p[1]}\nTest: {selected_test}\nTotal: Rs.{price}\nPaid: Rs.{paid}\nDue: Rs.{due}\nSample ID: {sample_code}\nThank you!"
            wa_link = f"https://wa.me/91{selected_p[2]}?text={urllib.parse.quote(msg)}"
            
            st.success(f"Receipt #{bill_id} ban gayi!")
            st.markdown(f'''
                <a href="{wa_link}" target="_blank">
                    <button style="background-color:#25D366; color:white; padding:10px 18px; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">
                        ?? Send Receipt on WhatsApp
                    </button>
                </a>
            ''', unsafe_allow_html=True)
    elif not tests:
        st.warning("Koi test available nahi hai. Menu 6 me jakar naya test add karein.")
    else:
        st.info("Pehle patient register karein.")

elif menu == "3. Clear Pending Dues":
    st.subheader("?? Settle Pending Patient Dues")
    conn = get_connection()
    due_bills = pd.read_sql_query('''
        SELECT b.id as bill_id, p.name, p.phone, b.test_name, b.total_amount, b.paid_amount, b.due_amount, b.created_at
        FROM billing b
        JOIN patients p ON b.patient_id = p.id
        WHERE b.due_amount > 0
    ''', conn)
    conn.close()

    if not due_bills.empty:
        st.dataframe(due_bills, use_container_width=True)
        bill_opts = {f"Bill #{row['bill_id']} - {row['name']} (Due: ?{row['due_amount']})": row['bill_id'] for _, row in due_bills.iterrows()}
        selected_due_bill = st.selectbox("Select Bill to Clear", list(bill_opts.keys()))
        b_id = bill_opts[selected_due_bill]

        recovering_amt = st.number_input("Enter Amount Receiving (?)", min_value=1.0, value=float(due_bills[due_bills['bill_id'] == b_id]['due_amount'].values[0]))

        if st.button("Confirm Payment Collection"):
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT total_amount, paid_amount FROM billing WHERE id = ?", (b_id,))
            row = cur.fetchone()
            new_paid = row[1] + recovering_amt
            new_due = max(0.0, row[0] - new_paid)
            new_status = "Paid" if new_due == 0 else "Due"
            
            cur.execute("UPDATE billing SET paid_amount = ?, due_amount = ?, status = ? WHERE id = ?", (new_paid, new_due, new_status, b_id))
            conn.commit()
            conn.close()
            st.success(f"Payment received! Remaining due: ?{new_due}")
            st.rerun()
    else:
        st.success("Sabhi accounts clear hain! Kisi bhi patient ka koi due pending nahi hai.")

elif menu == "4. Enter Multi-Param Test Results":
    st.subheader("?? Enter Clinical Test Results")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, phone, age, gender, referring_doctor FROM patients ORDER BY id DESC")
    patients = cur.fetchall()
    conn.close()

    if patients:
        p_dict = {f"{p[1]} (Age: {p[3]}, Dr. {p[5]})": p for p in patients}
        selected_p = p_dict[st.selectbox("Select Patient", list(p_dict.keys()))]
        test_type = st.selectbox("Choose Profile/Panel", ["Complete Blood Count (CBC)", "Lipid Profile", "Blood Glucose"])

        templates = {
            "Complete Blood Count (CBC)": [
                ("Hemoglobin (Hb)", 13.0, 17.0, "g/dL"),
                ("Total Leukocyte Count (WBC)", 4000, 11000, "/cumm"),
                ("Platelet Count", 150000, 450000, "/cumm"),
                ("RBC Count", 4.5, 5.5, "mil/cumm")
            ],
            "Lipid Profile": [
                ("Total Cholesterol", 0, 200, "mg/dL"),
                ("Triglycerides", 0, 150, "mg/dL"),
                ("HDL Cholesterol", 40, 999, "mg/dL"),
                ("LDL Cholesterol", 0, 100, "mg/dL")
            ],
            "Blood Glucose": [
                ("Fasting Blood Sugar", 70, 100, "mg/dL"),
                ("Post Prandial (PP) Sugar", 70, 140, "mg/dL")
            ]
        }

        results_data = []
        st.write("### Fill Test Findings:")
        for param, low, high, unit in templates[test_type]:
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            c1.markdown(f"**{param}**")
            val_str = c2.text_input(f"Value", key=f"inp_{param}", placeholder="e.g. 12.5")
            c3.write(f"Unit: {unit}")
            c4.write(f"Ref: {low} - {high}")
            
            flag = "NORMAL"
            if val_str:
                try:
                    num_val = float(val_str)
                    if num_val < low and low > 0:
                        flag = "LOW"
                    elif num_val > high:
                        flag = "HIGH"
                except ValueError:
                    flag = "NORMAL"
                    
            results_data.append({"param": param, "val": val_str, "unit": unit, "range": f"{low} - {high}", "flag": flag})

        if st.button("Generate & Download Official Report"):
            report_id = int(datetime.now().strftime("%d%H%M%S"))
            sample_code = f"SMP-{selected_p[0]}-{datetime.now().strftime('%H%M')}"
            pdf_path = generate_multi_param_report(
                selected_p[1], selected_p[2], selected_p[3], selected_p[4], selected_p[5],
                test_type, results_data, report_id, sample_code
            )
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="?? Download Official Medical Report (PDF)",
                    data=f,
                    file_name=f"Report_{selected_p[1]}_{test_type}.pdf",
                    mime="application/pdf"
                )
            st.success(f"Report ready! Sample Tube: {sample_code}")
    else:
        st.info("Pehle patient register karein.")

elif menu == "5. Search Patient History":
    st.subheader("?? Patient Records")
    q = st.text_input("Search by Name or Contact Number")
    conn = get_connection()
    if q:
        df = pd.read_sql_query("SELECT id, name, phone, age, gender, referring_doctor FROM patients WHERE name LIKE ? OR phone LIKE ?", conn, params=(f"%{q}%", f"%{q}%"))
    else:
        df = pd.read_sql_query("SELECT id, name, phone, age, gender, referring_doctor FROM patients ORDER BY id DESC LIMIT 10", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

elif menu == "6. Test Rate List Master":
    st.subheader("?? Lab Test & Price Master")
    conn = get_connection()
    cur = conn.cursor()
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("### Add / Update Test")
        t_name = st.text_input("Test Name", placeholder="e.g. Vitamin D3 (25-OH)")
        t_price = st.number_input("Test Rate (?)", min_value=10.0, step=50.0, value=500.0)
        if st.button("Save Test Rate"):
            if t_name:
                cur.execute("INSERT OR REPLACE INTO tests (test_name, price) VALUES (?, ?)", (t_name.strip(), t_price))
                conn.commit()
                st.success(f"Test '{t_name}' rate ?{t_price} save ho gaya!")
                st.rerun()
            else:
                st.error("Test ka naam likhna zaroori hai.")

    with col2:
        st.write("### Current Active Price List")
        tests_df = pd.read_sql_query("SELECT id, test_name, price FROM tests ORDER BY test_name ASC", conn)
        st.dataframe(tests_df, use_container_width=True)
    conn.close()

elif menu == "7. Admin Dashboard & Backup":
    st.subheader("?? Owner Dashboard & Security")
    pin = st.text_input("Enter 4-Digit Owner Security PIN", type="password")
    
    if pin == "1234":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT SUM(total_amount), SUM(paid_amount), SUM(due_amount) FROM billing")
        totals = cur.fetchone()
        
        cur.execute("SELECT referring_doctor, count(*) FROM patients GROUP BY referring_doctor")
        docs = cur.fetchall()
        
        billing_df = pd.read_sql_query("SELECT * FROM billing ORDER BY id DESC", conn)
        conn.close()

        total_rev = totals[0] if totals[0] else 0.0
        total_paid = totals[1] if totals[1] else 0.0
        total_due = totals[2] if totals[2] else 0.0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Business", f"? {total_rev:,.2f}")
        c2.metric("Total Cash Collected", f"? {total_paid:,.2f}")
        c3.metric("Pending Market Due", f"? {total_due:,.2f}")

        st.write("---")
        st.write("### ?? Patients Referred by Doctor:")
        for d in docs:
            d_name = d[0] if d[0] else "Direct Walk-in / Self"
            st.write(f"- **Dr. {d_name}**: {d[1]} Referrals")

        st.write("---")
        c_down1, c_down2 = st.columns(2)
        with c_down1:
            st.write("### ?? Financial Statement")
            csv = billing_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Revenue Excel/CSV", data=csv, file_name="lab_revenue_data.csv", mime="text/csv")
            
        with c_down2:
            st.write("### ?? Full Database Backup")
            if os.path.exists("lab.db"):
                with open("lab.db", "rb") as db_file:
                    st.download_button(
                        label="Download Entire Lab Database (.db)",
                        data=db_file,
                        file_name=f"CityLab_Backup_{datetime.now().strftime('%Y%m%d')}.db",
                        mime="application/octet-stream"
                    )
    elif pin:
        st.error("Incorrect PIN! Access denied.")
    else:
        st.info("PIN enter karein (Default: 1234).")
