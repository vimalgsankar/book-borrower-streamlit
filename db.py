"""
db.py — SQLite data-access layer for the Book Borrower Library System.

All reads return pandas DataFrames. Writes use parameterised SQL.
The module exposes a get_conn() singleton, table-creation, seed-data,
and thin CRUD helpers grouped by domain (users, books, checkouts, etc.).
"""

import hashlib
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / "library.db"

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_conn() -> sqlite3.Connection:
    """Return a module-level SQLite connection (one per process)."""
    if "db_conn" not in st.session_state:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        st.session_state["db_conn"] = conn
    return st.session_state["db_conn"]


def _exec(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    conn = get_conn()
    cur = conn.execute(sql, params)
    conn.commit()
    return cur


def _query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, get_conn(), params=params)


def clear_cache():
    """Call after any write to bust st.cache_data."""
    st.cache_data.clear()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        username        TEXT    UNIQUE NOT NULL,
        password_hash   TEXT    NOT NULL,
        full_name       TEXT    NOT NULL,
        email           TEXT    NOT NULL,
        dob             TEXT,
        grade           TEXT,
        school          TEXT,
        role            TEXT    NOT NULL DEFAULT 'student',
        status          TEXT    NOT NULL DEFAULT 'pending',
        parent_name     TEXT,
        parent_email    TEXT,
        parent_phone    TEXT,
        waiver_signature TEXT,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS books (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        title           TEXT    NOT NULL,
        author          TEXT    NOT NULL,
        genre           TEXT    NOT NULL,
        description     TEXT    DEFAULT '',
        image_url       TEXT    DEFAULT '',
        avg_rating      REAL    DEFAULT 0.0,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS book_copies (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id         INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
        copy_identifier TEXT    NOT NULL UNIQUE,
        status          TEXT    NOT NULL DEFAULT 'available',
        created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS checkouts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id),
        book_copy_id    INTEGER NOT NULL REFERENCES book_copies(id) ON DELETE CASCADE,
        checkout_date   TEXT    NOT NULL,
        due_date        TEXT    NOT NULL,
        return_date     TEXT,
        status          TEXT    NOT NULL DEFAULT 'active'
    );

    CREATE TABLE IF NOT EXISTS donations (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id),
        title           TEXT    NOT NULL,
        author          TEXT    NOT NULL,
        genre           TEXT    NOT NULL DEFAULT '',
        condition       TEXT    NOT NULL DEFAULT 'Good',
        review          TEXT    DEFAULT '',
        rating          INTEGER DEFAULT 3,
        status          TEXT    NOT NULL DEFAULT 'pending',
        admin_note      TEXT    DEFAULT '',
        dropoff_location TEXT   DEFAULT '',
        dropoff_deadline TEXT   DEFAULT '',
        created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS requests (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id),
        book_id         INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
        requested_date  TEXT    NOT NULL,
        queue_position  INTEGER NOT NULL DEFAULT 1,
        status          TEXT    NOT NULL DEFAULT 'waiting'
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id),
        message         TEXT    NOT NULL,
        category        TEXT    DEFAULT 'info',
        is_read         INTEGER NOT NULL DEFAULT 0,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id),
        book_id         INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
        rating          INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    );
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return _hash_pw(password) == hashed


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def create_user(
    username, password, full_name, email, dob, grade, school,
    parent_name="", parent_email="", parent_phone="",
    waiver_signature="", role="student", status="pending",
) -> bool:
    """Insert a new user.  Returns True on success, False if username taken."""
    try:
        _exec(
            """INSERT INTO users
               (username,password_hash,full_name,email,dob,grade,school,
                parent_name,parent_email,parent_phone,waiver_signature,role,status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (username, _hash_pw(password), full_name, email, str(dob), grade,
             school, parent_name, parent_email, parent_phone,
             waiver_signature, role, status),
        )
        clear_cache()
        return True
    except sqlite3.IntegrityError:
        return False


def authenticate(username: str, password: str) -> dict | None:
    """Return user row as dict, or None if credentials invalid."""
    row = get_conn().execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()
    if row and verify_password(password, row["password_hash"]):
        return dict(row)
    return None


@st.cache_data(ttl=30)
def get_pending_users() -> pd.DataFrame:
    return _query_df("SELECT * FROM users WHERE status='pending' ORDER BY created_at DESC")


@st.cache_data(ttl=30)
def get_all_users() -> pd.DataFrame:
    return _query_df("SELECT id,username,full_name,email,grade,school,role,status,created_at FROM users ORDER BY id")


def approve_user(user_id: int):
    _exec("UPDATE users SET status='active' WHERE id=?", (user_id,))
    add_notification(user_id, "🎉 Your account has been approved! Welcome to the library.", "account")
    clear_cache()


def reject_user(user_id: int):
    _exec("UPDATE users SET status='rejected' WHERE id=?", (user_id,))
    add_notification(user_id, "Your registration was not approved. Contact the librarian for details.", "account")
    clear_cache()


def update_user_status(user_id: int, status: str):
    _exec("UPDATE users SET status=? WHERE id=?", (status, user_id))
    clear_cache()


def delete_user(user_id: int):
    _exec("DELETE FROM users WHERE id=?", (user_id,))
    clear_cache()


# ---------------------------------------------------------------------------
# Books & Copies
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def get_all_books() -> pd.DataFrame:
    return _query_df("""
        SELECT b.*, 
               (SELECT COUNT(*) FROM book_copies WHERE book_id=b.id) as total_copies,
               (SELECT COUNT(*) FROM book_copies WHERE book_id=b.id AND status='available') as available_copies
        FROM books b 
        ORDER BY b.title
    """)


@st.cache_data(ttl=30)
def get_available_books() -> pd.DataFrame:
    return _query_df("""
        SELECT b.*, 
               (SELECT COUNT(*) FROM book_copies WHERE book_id=b.id AND status='available') as available_copies,
               (SELECT COUNT(*) FROM book_copies WHERE book_id=b.id) as total_copies
        FROM books b
        WHERE (SELECT COUNT(*) FROM book_copies WHERE book_id=b.id AND status='available') > 0
        ORDER BY b.title
    """)

@st.cache_data(ttl=30)
def get_all_copies() -> pd.DataFrame:
    return _query_df("""
        SELECT bc.id, bc.book_id, bc.copy_identifier, bc.status as copy_status, b.title, b.author
        FROM book_copies bc
        JOIN books b ON bc.book_id = b.id
        ORDER BY b.title, bc.copy_identifier
    """)

@st.cache_data(ttl=30)
def get_available_copies() -> pd.DataFrame:
    return _query_df("""
        SELECT bc.id, bc.book_id, bc.copy_identifier, bc.status as copy_status, b.title, b.author
        FROM book_copies bc
        JOIN books b ON bc.book_id = b.id
        WHERE bc.status = 'available'
        ORDER BY b.title, bc.copy_identifier
    """)

def search_books(query: str = "", genres: list[str] | None = None) -> pd.DataFrame:
    """Full-text-ish search + genre filter. Not cached (params vary)."""
    sql = """
        SELECT b.*, 
               (SELECT COUNT(*) FROM book_copies WHERE book_id=b.id) as total_copies,
               (SELECT COUNT(*) FROM book_copies WHERE book_id=b.id AND status='available') as available_copies
        FROM books b 
        WHERE 1=1
    """
    params: list = []
    if query:
        sql += " AND (b.title LIKE ? OR b.author LIKE ?)"
        params += [f"%{query}%", f"%{query}%"]
    if genres:
        placeholders = ",".join("?" * len(genres))
        sql += f" AND b.genre IN ({placeholders})"
        params += genres
    sql += " ORDER BY b.title"
    return _query_df(sql, tuple(params))


def get_book(book_id: int) -> dict | None:
    row = get_conn().execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    return dict(row) if row else None


def add_book(title, author, genre, description="", total_copies=1):
    cur = _exec(
        "INSERT INTO books (title,author,genre,description) VALUES (?,?,?,?)",
        (title, author, genre, description),
    )
    book_id = cur.lastrowid
    for i in range(1, total_copies + 1):
        copy_id = f"B{book_id}-C{i}"
        _exec("INSERT INTO book_copies (book_id, copy_identifier) VALUES (?, ?)", (book_id, copy_id))
    clear_cache()


def update_book(book_id, **kwargs):
    # Do not allow updating copies directly here
    allowed = {k: v for k, v in kwargs.items() if k in ["title", "author", "genre", "description", "avg_rating"]}
    if allowed:
        sets = ", ".join(f"{k}=?" for k in allowed)
        vals = list(allowed.values()) + [book_id]
        _exec(f"UPDATE books SET {sets} WHERE id=?", tuple(vals))
        clear_cache()


def delete_book(book_id: int):
    # Cascading deletes should handle copies and checkouts if setup properly, but lets rely on SQLite ON DELETE CASCADE
    _exec("DELETE FROM books WHERE id=?", (book_id,))
    clear_cache()


@st.cache_data(ttl=30)
def get_genres() -> list[str]:
    rows = get_conn().execute("SELECT DISTINCT genre FROM books ORDER BY genre").fetchall()
    return [r["genre"] for r in rows]


def _refresh_avg_rating(book_id: int):
    row = get_conn().execute(
        "SELECT AVG(rating) as avg_r FROM reviews WHERE book_id=?", (book_id,)
    ).fetchone()
    avg = round(row["avg_r"], 1) if row["avg_r"] else 0.0
    _exec("UPDATE books SET avg_rating=? WHERE id=?", (avg, book_id))
    clear_cache()


# ---------------------------------------------------------------------------
# Checkouts
# ---------------------------------------------------------------------------

def checkout_book(user_id: int, book_id: int, days: int = 14) -> bool:
    """Borrow a book. Backend picks the first available copy."""
    row = get_conn().execute("SELECT id FROM book_copies WHERE book_id=? AND status='available' LIMIT 1", (book_id,)).fetchone()
    if not row:
        return False
    
    copy_id = row["id"]
    return checkout_copy(user_id, copy_id, days)


def checkout_copy(user_id: int, book_copy_id: int, days: int = 14) -> bool:
    """Borrow a specific physical copy."""
    row = get_conn().execute("SELECT bc.*, b.title FROM book_copies bc JOIN books b ON bc.book_id=b.id WHERE bc.id=?", (book_copy_id,)).fetchone()
    if not row or row["status"] != 'available':
        return False
    
    today = date.today()
    _exec(
        "INSERT INTO checkouts (user_id,book_copy_id,checkout_date,due_date,status) VALUES (?,?,?,?,?)",
        (user_id, book_copy_id, str(today), str(today + timedelta(days=days)), "active"),
    )
    _exec("UPDATE book_copies SET status='checked_out' WHERE id=?", (book_copy_id,))
    add_notification(user_id, f"📚 You borrowed \"{row['title']}\" (Copy: {row['copy_identifier']}). Due back by {today + timedelta(days=days)}.", "checkout")
    clear_cache()
    return True


def return_book(checkout_id: int):
    row = get_conn().execute("SELECT * FROM checkouts WHERE id=?", (checkout_id,)).fetchone()
    if not row:
        return
    today = str(date.today())
    _exec("UPDATE checkouts SET status='returned', return_date=? WHERE id=?", (today, checkout_id))
    _exec("UPDATE book_copies SET status='available' WHERE id=?", (row["book_copy_id"],))
    
    copy_row = get_conn().execute("SELECT b.title FROM book_copies bc JOIN books b ON bc.book_id=b.id WHERE bc.id=?", (row["book_copy_id"],)).fetchone()
    title = copy_row["title"] if copy_row else "a book"
    status_label = "on time" if today <= row["due_date"] else "late"
    add_notification(row["user_id"], f"📗 You returned \"{title}\" ({status_label}).", "return")
    clear_cache()


@st.cache_data(ttl=15)
def get_user_checkouts(user_id: int) -> pd.DataFrame:
    return _query_df(
        """SELECT c.*, b.title, b.author, b.genre, bc.copy_identifier
           FROM checkouts c 
           JOIN book_copies bc ON c.book_copy_id=bc.id
           JOIN books b ON bc.book_id=b.id
           WHERE c.user_id=? ORDER BY c.checkout_date DESC""",
        (user_id,),
    )


@st.cache_data(ttl=15)
def get_active_checkouts() -> pd.DataFrame:
    return _query_df(
        """SELECT c.*, b.title, b.author, bc.copy_identifier, u.full_name as student_name
           FROM checkouts c
           JOIN book_copies bc ON c.book_copy_id=bc.id
           JOIN books b ON bc.book_id=b.id
           JOIN users u ON c.user_id=u.id
           WHERE c.status='active'
           ORDER BY c.due_date"""
    )


@st.cache_data(ttl=15)
def get_all_checkouts_filtered(search="", status_filter="All", date_from=None, date_to=None) -> pd.DataFrame:
    sql = """SELECT c.*, b.title, b.author, b.genre, bc.copy_identifier, u.full_name as student_name
             FROM checkouts c
             JOIN book_copies bc ON c.book_copy_id=bc.id
             JOIN books b ON bc.book_id=b.id
             JOIN users u ON c.user_id=u.id WHERE 1=1"""
    params: list = []
    if search:
        sql += " AND (b.title LIKE ? OR b.author LIKE ? OR u.full_name LIKE ? OR bc.copy_identifier LIKE ?)"
        params += [f"%{search}%"] * 4
    if status_filter and status_filter != "All":
        sql += " AND c.status=?"
        params.append(status_filter)
    if date_from:
        sql += " AND c.checkout_date >= ?"
        params.append(str(date_from))
    if date_to:
        sql += " AND c.checkout_date <= ?"
        params.append(str(date_to))
    sql += " ORDER BY c.checkout_date DESC"
    return _query_df(sql, tuple(params))


def count_overdue(user_id: int) -> int:
    today = str(date.today())
    row = get_conn().execute(
        "SELECT COUNT(*) as cnt FROM checkouts WHERE user_id=? AND status='active' AND due_date < ?",
        (user_id, today),
    ).fetchone()
    return row["cnt"] if row else 0


def mark_overdue():
    """Bulk-update any active checkout past its due date."""
    today = str(date.today())
    _exec("UPDATE checkouts SET status='overdue' WHERE status='active' AND due_date < ?", (today,))
    clear_cache()


# ---------------------------------------------------------------------------
# Donations
# ---------------------------------------------------------------------------

def donate_book(user_id, title, author, genre, condition, review, rating):
    _exec(
        """INSERT INTO donations (user_id,title,author,genre,condition,review,rating,status,created_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (user_id, title, author, genre, condition, review, rating, "pending", str(datetime.now())),
    )
    clear_cache()


@st.cache_data(ttl=15)
def get_user_donations(user_id: int) -> pd.DataFrame:
    return _query_df("SELECT * FROM donations WHERE user_id=? ORDER BY created_at DESC", (user_id,))


@st.cache_data(ttl=15)
def get_pending_donations() -> pd.DataFrame:
    return _query_df(
        """SELECT d.*, u.full_name as student_name
           FROM donations d JOIN users u ON d.user_id=u.id
           WHERE d.status='pending' ORDER BY d.created_at"""
    )


def accept_donation(donation_id, location, deadline):
    _exec(
        "UPDATE donations SET status='accepted', dropoff_location=?, dropoff_deadline=? WHERE id=?",
        (location, str(deadline), donation_id),
    )
    row = get_conn().execute("SELECT * FROM donations WHERE id=?", (donation_id,)).fetchone()
    if row:
        add_notification(
            row["user_id"],
            f"✅ Your donation of \"{row['title']}\" was accepted! Drop off at {location} by {deadline}.",
            "donation",
        )
    clear_cache()


def reject_donation(donation_id, reason):
    _exec("UPDATE donations SET status='rejected', admin_note=? WHERE id=?", (reason, donation_id))
    row = get_conn().execute("SELECT * FROM donations WHERE id=?", (donation_id,)).fetchone()
    if row:
        add_notification(
            row["user_id"],
            f"❌ Your donation of \"{row['title']}\" was not accepted. Reason: {reason}",
            "donation",
        )
    clear_cache()


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

def request_book(user_id: int, book_id: int) -> int:
    """Create a hold request.  Returns queue position."""
    pos_row = get_conn().execute(
        "SELECT COALESCE(MAX(queue_position),0)+1 as pos FROM requests WHERE book_id=? AND status='waiting'",
        (book_id,),
    ).fetchone()
    pos = pos_row["pos"]
    _exec(
        "INSERT INTO requests (user_id,book_id,requested_date,queue_position,status) VALUES (?,?,?,?,?)",
        (user_id, book_id, str(date.today()), pos, "waiting"),
    )
    book = get_book(book_id)
    title = book["title"] if book else "a book"
    add_notification(user_id, f"📋 You requested \"{title}\". Queue position: #{pos}.", "request")
    clear_cache()
    return pos


@st.cache_data(ttl=15)
def get_user_requests(user_id: int) -> pd.DataFrame:
    return _query_df(
        """SELECT r.*, b.title, b.author
           FROM requests r JOIN books b ON r.book_id=b.id
           WHERE r.user_id=? ORDER BY r.requested_date DESC""",
        (user_id,),
    )


@st.cache_data(ttl=15)
def get_pending_requests() -> pd.DataFrame:
    return _query_df(
        """SELECT r.*, b.title, b.author, u.full_name as student_name
           FROM requests r
           JOIN books b ON r.book_id=b.id
           JOIN users u ON r.user_id=u.id
           WHERE r.status IN ('waiting','available')
           ORDER BY r.requested_date"""
    )


def cancel_request(request_id: int):
    _exec("UPDATE requests SET status='cancelled' WHERE id=?", (request_id,))
    clear_cache()


def fulfill_request(request_id: int):
    _exec("UPDATE requests SET status='fulfilled' WHERE id=?", (request_id,))
    row = get_conn().execute("SELECT * FROM requests WHERE id=?", (request_id,)).fetchone()
    if row:
        book = get_book(row["book_id"])
        title = book["title"] if book else "a book"
        add_notification(row["user_id"], f"📗 Your request for \"{title}\" has been fulfilled!", "request")
    clear_cache()


def mark_request_available(request_id: int):
    _exec("UPDATE requests SET status='available' WHERE id=?", (request_id,))
    row = get_conn().execute("SELECT * FROM requests WHERE id=?", (request_id,)).fetchone()
    if row:
        book = get_book(row["book_id"])
        title = book["title"] if book else "a book"
        add_notification(row["user_id"], f"📬 \"{title}\" is available for pickup!", "request")
    clear_cache()


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def add_notification(user_id: int, message: str, category: str = "info"):
    _exec(
        "INSERT INTO notifications (user_id,message,category) VALUES (?,?,?)",
        (user_id, message, category),
    )


@st.cache_data(ttl=10)
def get_notifications(user_id: int) -> pd.DataFrame:
    return _query_df(
        "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 50",
        (user_id,),
    )


def unread_count(user_id: int) -> int:
    row = get_conn().execute(
        "SELECT COUNT(*) as cnt FROM notifications WHERE user_id=? AND is_read=0",
        (user_id,),
    ).fetchone()
    return row["cnt"] if row else 0


def mark_notification_read(notif_id: int):
    _exec("UPDATE notifications SET is_read=1 WHERE id=?", (notif_id,))
    clear_cache()


def mark_all_read(user_id: int):
    _exec("UPDATE notifications SET is_read=1 WHERE user_id=? AND is_read=0", (user_id,))
    clear_cache()


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

def add_review(user_id: int, book_id: int, rating: int):
    _exec(
        "INSERT INTO reviews (user_id,book_id,rating) VALUES (?,?,?)",
        (user_id, book_id, rating),
    )
    _refresh_avg_rating(book_id)


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

def seed_if_empty():
    """Populate sample data on first launch."""
    # Run migrations/init
    init_db()
    row = get_conn().execute("SELECT COUNT(*) as cnt FROM users").fetchone()
    if row["cnt"] > 0:
        return  # already seeded

    # ---- Admin ----
    create_user("admin", "admin123", "Library Admin", "admin@school.edu",
                "1990-01-01", "Staff", "Greenfield Academy",
                role="admin", status="active")

    get_conn().commit()
    clear_cache()
