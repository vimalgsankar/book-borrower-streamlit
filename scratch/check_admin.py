import sqlite3
conn = sqlite3.connect('library.db')
cur = conn.cursor()
cur.execute("SELECT id, username, role, status FROM users WHERE username='admin'")
res = cur.fetchall()
print("Admin row:", res)

cur.execute("SELECT count(*) FROM users")
print("Total users:", cur.fetchone())
