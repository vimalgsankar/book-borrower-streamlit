import sqlite3
import random
from datetime import datetime, timedelta

def seed_activity():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get all users and books
    cur.execute("SELECT id FROM users WHERE role='student'")
    students = [row['id'] for row in cur.fetchall()]
    
    cur.execute("SELECT id FROM book_copies")
    copies = [row['id'] for row in cur.fetchall()]
    
    cur.execute("SELECT id FROM books")
    books = [row['id'] for row in cur.fetchall()]
    
    if not students or not copies or not books:
        print("Database not populated enough to seed activity.")
        return

    # Create past checkouts (returned)
    for _ in range(150):
        student_id = random.choice(students)
        copy_id = random.choice(copies)
        
        checkout_date = datetime.now() - timedelta(days=random.randint(10, 60))
        due_date = checkout_date + timedelta(days=14)
        return_date = checkout_date + timedelta(days=random.randint(5, 20))
        
        status = 'returned'
        
        cur.execute("""
            INSERT INTO checkouts (user_id, book_copy_id, checkout_date, due_date, return_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, copy_id, checkout_date.strftime("%Y-%m-%d"), due_date.strftime("%Y-%m-%d"), return_date.strftime("%Y-%m-%d"), status))

    # Create active checkouts
    active_copies = random.sample(copies, k=50)
    for copy_id in active_copies:
        student_id = random.choice(students)
        checkout_date = datetime.now() - timedelta(days=random.randint(1, 20))
        due_date = checkout_date + timedelta(days=14)
        
        status = 'active'
        if due_date < datetime.now():
            status = 'overdue'
            
        cur.execute("""
            INSERT INTO checkouts (user_id, book_copy_id, checkout_date, due_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, copy_id, checkout_date.strftime("%Y-%m-%d"), due_date.strftime("%Y-%m-%d"), status))
        
        cur.execute("UPDATE book_copies SET status='checked_out' WHERE id=?", (copy_id,))

    # Create Book Requests
    for _ in range(40):
        student_id = random.choice(students)
        book_id = random.choice(books)
        req_date = datetime.now() - timedelta(days=random.randint(1, 10))
        status = random.choice(['waiting', 'available', 'fulfilled', 'cancelled'])
        
        queue_pos = 0
        if status == 'waiting':
            cur.execute("SELECT MAX(queue_position) as m FROM requests WHERE book_id=? AND status='waiting'", (book_id,))
            max_q = cur.fetchone()['m'] or 0
            queue_pos = max_q + 1
            
        cur.execute("""
            INSERT INTO requests (user_id, book_id, requested_date, status, queue_position)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, book_id, req_date.strftime("%Y-%m-%d"), status, queue_pos))

    # Create Donations
    for _ in range(25):
        student_id = random.choice(students)
        title = f"Donated Book {random.randint(1,100)}"
        author = "Local Author"
        genre = random.choice(['Fiction', 'Non-Fiction', 'Sci-Fi'])
        cond = random.choice(['New', 'Good', 'Fair'])
        rating = random.randint(3, 5)
        status = random.choice(['pending', 'accepted', 'rejected'])
        
        cur.execute("""
            INSERT INTO donations (user_id, title, author, genre, condition, rating, review, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, title, author, genre, cond, rating, "A great read!", status))
        
    conn.commit()
    conn.close()
    print("Activity data seeded successfully!")

if __name__ == '__main__':
    seed_activity()
