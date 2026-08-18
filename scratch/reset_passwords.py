import sqlite3
import csv
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def update_passwords():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get all students
    cur.execute("SELECT id, username, full_name FROM users WHERE role='student'")
    students = cur.fetchall()
    
    new_credentials = []
    new_credentials.append(["Full Name", "Username", "Password"])
    
    for row in students:
        student_id = row['id']
        username = row['username']
        full_name = row['full_name']
        
        # New password: lowercase name + id (e.g., vimal2)
        first_name = full_name.split()[0].lower()
        new_password = f"{first_name}{student_id}"
        
        # Update DB
        hashed = hash_password(new_password)
        cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed, student_id))
        
        # Save to CSV list
        new_credentials.append([full_name, username, new_password])
        
    conn.commit()
    conn.close()
    
    # Write to CSV
    with open('scratch/credentials.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(new_credentials)
        
    # Overwrite the artifact as well
    with open(r'C:\Users\econs\.gemini\antigravity\brain\29e093df-6574-4a0e-9532-982769c5f6d3\credentials.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(new_credentials)
        
    print(f"Updated passwords for {len(students)} students.")

if __name__ == '__main__':
    update_passwords()
