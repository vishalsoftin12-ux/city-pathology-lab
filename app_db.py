import sqlite3

def setup_lab():
    conn = sqlite3.connect('lab.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        age INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_name TEXT NOT NULL,
        price INTEGER NOT NULL
    )
    ''')

    cursor.execute("INSERT OR IGNORE INTO tests (id, test_name, price) VALUES (1, 'CBC (Blood Test)', 350)")
    cursor.execute("INSERT OR IGNORE INTO tests (id, test_name, price) VALUES (2, 'Lipid Profile', 600)")

    conn.commit()
    conn.close()
    print('Mubarak ho! Lab ka Database successfully ban gaya hai.')

if __name__ == '__main__':
    setup_lab()
