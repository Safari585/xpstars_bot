import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referred_by INTEGER,
    points INTEGER,
    name TEXT
)
''')
conn.commit()
conn.close()
