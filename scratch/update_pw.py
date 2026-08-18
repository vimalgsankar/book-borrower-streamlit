import sqlite3, hashlib
conn = sqlite3.connect('library.db')
cur = conn.cursor()
h = hashlib.sha256(b'student123').hexdigest()
cur.execute("UPDATE users SET password_hash = ? WHERE role = 'student'", (h,))
conn.commit()
print('Success!')
