import sqlite3
import urllib.parse

def add_covers():
    conn = sqlite3.connect('library.db')
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM books")
    books = cur.fetchall()
    
    for book_id, title in books:
        # Generate Open Library Cover URL by title
        safe_title = urllib.parse.quote_plus(title.lower())
        cover_url = f"https://covers.openlibrary.org/b/title/{safe_title}-M.jpg"
        
        conn.execute("UPDATE books SET image_url = ? WHERE id = ?", (cover_url, book_id))
    
    conn.commit()
    print("Cover URLs updated!")

if __name__ == '__main__':
    add_covers()
