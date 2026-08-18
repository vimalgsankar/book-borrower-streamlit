import sys
from pathlib import Path
import random
import csv
import json

# Ensure the parent directory is in the path to import db
sys.path.append(str(Path(__file__).parent.parent))

import db

# Force DB initialization
db.init_db()

# --- Book Data ---
books_file = Path(__file__).parent / "books.json"
with open(books_file, 'r', encoding='utf-8') as f:
    unique_books = json.load(f)

print(f"Adding {len(unique_books)} real books from OpenLibrary...")
for b in unique_books:
    copies = random.randint(2, 5) # 2 to 5 copies each
    db.add_book(b['title'], b['author'], b['genre'], b['description'], copies)

# --- User Data ---
specific_names = ["Vimal", "Shiva", "Ashwin", "Jayvanth", "Keerthana", "Sankar", "Vigneshwari", "Hasan", "Atif", "Mohammed"]
first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy", "Mallory", "Niaj", "Olivia", "Peggy", "Sybil", "Trent", "Victor", "Walter", "Zoey", "Aaron", "Betty", "Chris", "David", "Ella", "Fiona", "George", "Hannah", "Isaac", "Julia", "Kevin", "Laura", "Mike", "Nina", "Oscar", "Paul", "Quinn", "Rachel", "Steve", "Tina", "Uma", "Vince", "Wendy", "Xander", "Yara", "Zack"]
last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson"]

# Start with the specific names
all_students = []
for name in specific_names:
    all_students.append(name)

# Generate the remaining to reach 300
while len(all_students) < 300:
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    all_students.append(name)

print(f"Adding {len(all_students)} users...")
credentials = []

# Assuming user IDs will start from 2 (since admin is ID 1 via seed_if_empty)
# We will just use enumerate to generate the ID number (approx)
for idx, name in enumerate(all_students, start=2):
    first_name = name.split()[0].lower()
    username = f"{idx}{first_name}"
    # Password = name + some random string/order
    random_str = "".join(random.choices("abcdefghijklmnopqrstuvwxyz1234567890", k=4))
    password = f"{first_name}{random_str}"
    
    success = db.create_user(
        username=username, 
        password=password, 
        full_name=name, 
        email=f"{username}@school.edu", 
        dob="2005-01-01", 
        grade="10th", 
        school="Greenfield Academy",
        role="student", 
        status="active"
    )
    if success:
        credentials.append((name, username, password))

# Write credentials to CSV
out_path = Path(__file__).parent / "credentials.csv"
with open(out_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Name", "Username", "Password"])
    writer.writerows(credentials)

print(f"Data generation complete! Credentials saved to {out_path}")
