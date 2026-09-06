from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3

app = FastAPI(title='Pathology Lab API')

class Patient(BaseModel):
    name: str
    phone: str
    age: int

def get_db():
    conn = sqlite3.connect('lab.db')
    return conn

@app.get('/')
def home():
    return {'message': 'Lab Server Active Hai!'}

@app.get('/tests')
def get_tests():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, test_name, price FROM tests')
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'test_name': r[1], 'price': r[2]} for r in rows]

@app.post('/register-patient')
def add_patient(p: Patient):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO patients (name, phone, age) VALUES (?, ?, ?)', (p.name, p.phone, p.age))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {'status': 'success', 'patient_id': new_id, 'message': 'Patient successfully registered!'}
