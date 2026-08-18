from datetime import datetime
import streamlit as st
import pandas as pd
import db

def render():
    user = st.session_state.get("user")
    if not user or user["role"] != "student":
        st.session_state["view"] = "auth"
        st.rerun()

    # Wrap entire view in a fade-in div
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    _render_header(user)

    if "student_view" not in st.session_state:
        st.session_state["student_view"] = "borrow"

    _render_nav_pills()
    st.write("") # spacing

    # Route to sub-view
    sv = st.session_state["student_view"]
    if sv == "borrow":
        _render_borrow()
    elif sv == "donate":
        _render_donate()
    elif sv == "requests":
        _render_requests()
    elif sv == "history":
        _render_history()

    st.markdown('</div>', unsafe_allow_html=True)

def _render_header(user):
    hour = datetime.now().hour
    if hour < 12: greeting = "Good morning"
    elif hour < 18: greeting = "Good afternoon"
    else: greeting = "Good evening"

    col_logo, col_title, col_notif, col_logout = st.columns([1, 5, 1, 1])
    with col_logo:
        st.image("assets/logo.jpg", use_container_width=True)
    with col_title:
        st.markdown(f"<h1 class='gradient-text fade-in stagger-1' style='margin-bottom:0;'>{greeting}, {user['full_name']}! <span class='floating-icon'>👋</span></h1>", unsafe_allow_html=True)
        st.caption(datetime.now().strftime("%A, %B %d, %Y"))

    with col_notif:
        st.write("") 
        unread = db.unread_count(user["id"])
        btn_label = f"🔔 ({unread})" if unread > 0 else "🔔"
        with st.popover(btn_label):
            st.subheader("Notifications")
            notifs = db.get_notifications(user["id"])
            if notifs.empty:
                st.info("No new notifications.")
            else:
                if st.button("Mark all read", key="btn_mark_all_read"):
                    db.mark_all_read(user["id"])
                    st.rerun()
                for _, n in notifs.iterrows():
                    icon = "ℹ️"
                    if n["category"] == "checkout": icon = "📚"
                    elif n["category"] == "return": icon = "📗"
                    elif n["category"] == "request": icon = "📋"
                    elif n["category"] == "donation": icon = "🎁"
                    elif n["category"] == "account": icon = "👤"
                    
                    style = "" if n["is_read"] else "font-weight: bold; color: #5B51D8;"
                    st.markdown(f"<span style='{style}'>{icon} {n['message']}</span>", unsafe_allow_html=True)
                    st.caption(n["created_at"][:16])
                    if not n["is_read"]:
                        if st.button("Mark read", key=f"read_{n['id']}", help="Mark as read"):
                            db.mark_notification_read(n["id"])
                            st.rerun()
                    st.divider()

    with col_logout:
        st.write("")
        if st.button("Log Out", type="secondary"):
            st.session_state["user"] = None
            st.session_state["view"] = "auth"
            st.rerun()

def _render_nav_pills():
    st.markdown('<div class="fade-in stagger-2">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    
    def nav_btn(col, icon, label, view_name):
        with col:
            is_active = (st.session_state["student_view"] == view_name)
            if st.button(f"{icon} {label}", key=f"nav_{view_name}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state["student_view"] = view_name
                st.rerun()

    nav_btn(c1, "📚", "Borrow Book", "borrow")
    nav_btn(c2, "🎁", "Donate Book", "donate")
    nav_btn(c3, "📋", "View Requests", "requests")
    nav_btn(c4, "📖", "View History", "history")
    st.markdown('</div>', unsafe_allow_html=True)

@st.fragment
def _render_borrow():
    st.markdown('<div class="fade-in stagger-3">', unsafe_allow_html=True)
    
    col_search, col_filter = st.columns([3, 1])
    query = col_search.text_input("🔍 Search title or author", key="borrow_search", placeholder="e.g. Harry Potter")
    genres = db.get_genres()
    selected_genres = col_filter.multiselect("Filter by Genre", genres, key="borrow_genres")

    books = db.search_books(query, selected_genres)
    
    if books.empty:
        st.info("No books found matching your search.")
        return

    # Pagination logic
    PAGE_SIZE = 12
    if "borrow_page" not in st.session_state:
        st.session_state["borrow_page"] = 1
        
    total_pages = max(1, (len(books) - 1) // PAGE_SIZE + 1)
    
    # Reset page if out of bounds (e.g. search narrowed results)
    if st.session_state["borrow_page"] > total_pages:
        st.session_state["borrow_page"] = 1
        
    start_idx = (st.session_state["borrow_page"] - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    
    page_books = books.iloc[start_idx:end_idx]

    st.write("") # spacing
    # Responsive Grid (3 columns) with cascading stagger
    cols = st.columns(3)
    for i, (_, book) in enumerate(page_books.iterrows()):
        stagger_class = f"stagger-{(i % 5) + 1}"
        with cols[i % 3]:
            st.markdown(f'<div class="fade-in {stagger_class}">', unsafe_allow_html=True)
            with st.container(border=True):
                if 'image_url' in book and pd.notna(book['image_url']) and book['image_url']:
                    st.image(book['image_url'], use_container_width=True)
                st.markdown(f"<h4 style='margin-bottom: 0; color: #1f2937;'>{book['title']}</h4>", unsafe_allow_html=True)
                st.caption(f"by {book['author']}")
                
                # Rating stars
                rating = book['avg_rating']
                stars = int(round(rating))
                empty_stars = 5 - stars
                st.markdown(f"<span style='color: #F59E0B;'>{'★'*stars}</span><span style='color: #D1D5DB;'>{'★'*empty_stars}</span> ({rating:.1f})", unsafe_allow_html=True)
                
                # Availability badge
                avail = book['available_copies']
                if avail > 0:
                    st.markdown(f"<span class='badge badge-avail'>{avail} Available</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='badge badge-out'>Checked Out</span>", unsafe_allow_html=True)
                
                st.write("") 
                if st.button("View Details", key=f"view_{book['id']}", use_container_width=True):
                    _show_book_details(book.to_dict())
            st.markdown('</div>', unsafe_allow_html=True)
            
    # Pagination controls
    st.write("")
    col_prev, col_page, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.session_state["borrow_page"] > 1:
            if st.button("⬅️ Previous"):
                st.session_state["borrow_page"] -= 1
                st.rerun()
    with col_page:
        st.markdown(f"<div style='text-align: center; color: #6b7280; margin-top: 8px;'>Page {st.session_state['borrow_page']} of {total_pages}</div>", unsafe_allow_html=True)
    with col_next:
        if st.session_state["borrow_page"] < total_pages:
            if st.button("Next ➡️"):
                st.session_state["borrow_page"] += 1
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

@st.dialog("Book Details")
def _show_book_details(book):
    st.markdown(f"### {book['title']}")
    st.write(f"**Author:** {book['author']}")
    st.write(f"**Genre:** {book['genre']}")
    
    st.write("**Description:**")
    st.write(book['description'] or "No description available.")
    
    st.divider()
    
    avail = book['available_copies']
    user_id = st.session_state["user"]["id"]
    
    if avail > 0:
        st.success(f"✅ {avail} copies available!")
        if st.button("Borrow Now", type="primary", use_container_width=True):
            if db.count_overdue(user_id) > 0:
                st.error("You have overdue books! Please return them before borrowing more.")
            else:
                if db.checkout_book(user_id, book['id']):
                    st.toast(f"You borrowed '{book['title']}'!")
                    st.rerun()
                else:
                    st.error("Sorry, this book was just checked out.")
    else:
        st.warning("⚠️ All copies are currently checked out.")
        if st.button("Request Hold", use_container_width=True):
            pos = db.request_book(user_id, book['id'])
            st.toast(f"Request placed! You are #{pos} in queue.")
            st.rerun()

@st.fragment
def _render_donate():
    st.markdown('<div class="fade-in stagger-3">', unsafe_allow_html=True)
    st.markdown("<h3 style='color: #1f2937;'>Donate a Book</h3>", unsafe_allow_html=True)
    st.write("Help grow our library! Submit the details below. Drop the book off with the librarian once approved.")
    
    with st.container(border=True):
        with st.form("donate_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            title = col1.text_input("Title *")
            author = col2.text_input("Author *")
            
            genres = db.get_genres()
            genre = col1.selectbox("Genre *", genres + ["Other"])
            if genre == "Other":
                genre = col1.text_input("Specify Genre *")
                
            condition = col2.selectbox("Condition *", ["New", "Good", "Fair"])
            
            rating = st.slider("Your Rating", 1, 5, 3)
            review = st.text_area("Short Review (Optional)")
            
            st.write("")
            submitted = st.form_submit_button("Submit Donation", type="primary")
            if submitted:
                if not title or not author or not genre:
                    st.error("Please fill in the required fields.")
                else:
                    db.donate_book(st.session_state["user"]["id"], title, author, genre, condition, review, rating)
                    st.toast("Donation submitted! Awaiting review.")
                    st.rerun()
                
    st.write("")
    st.markdown("<h4 style='color: #1f2937;'>My Donations</h4>", unsafe_allow_html=True)
    donations = db.get_user_donations(st.session_state["user"]["id"])
    if donations.empty:
        st.info("You haven't donated any books yet.")
    else:
        st.dataframe(donations[['title', 'author', 'condition', 'status', 'created_at']], use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

@st.fragment
def _render_requests():
    st.markdown('<div class="fade-in stagger-3">', unsafe_allow_html=True)
    st.markdown("<h3 style='color: #1f2937;'>My Book Requests</h3>", unsafe_allow_html=True)
    requests = db.get_user_requests(st.session_state["user"]["id"])
    
    if requests.empty:
        st.info("You don't have any pending book requests.")
    else:
        for i, req in requests.iterrows():
            stagger_class = f"stagger-{(i % 5) + 1}"
            st.markdown(f'<div class="fade-in {stagger_class}">', unsafe_allow_html=True)
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"<strong style='font-size: 1.1em;'>{req['title']}</strong> by {req['author']}", unsafe_allow_html=True)
                    st.caption(f"Requested on {req['requested_date']}")
                with col2:
                    status = req['status']
                    if status == 'waiting':
                        st.markdown(f"<span style='color: #F59E0B; font-weight: 600;'>⏳ Waiting (Queue: #{req['queue_position']})</span>", unsafe_allow_html=True)
                    elif status == 'available':
                        st.markdown("<span style='color: #10B981; font-weight: 600;'>📬 Available for pickup!</span>", unsafe_allow_html=True)
                    elif status == 'fulfilled':
                        st.markdown("<span style='color: #6B7280; font-weight: 600;'>✅ Fulfilled</span>", unsafe_allow_html=True)
                    elif status == 'cancelled':
                        st.markdown("<span style='color: #EF4444; font-weight: 600;'>❌ Cancelled</span>", unsafe_allow_html=True)
                with col3:
                    if status in ('waiting', 'available'):
                        if st.button("Cancel", key=f"cancel_req_{req['id']}", use_container_width=True):
                            db.cancel_request(req['id'])
                            st.toast("Request cancelled.")
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

@st.fragment
def _render_history():
    st.markdown('<div class="fade-in stagger-3">', unsafe_allow_html=True)
    
    checkouts = db.get_user_checkouts(st.session_state["user"]["id"])
    
    if checkouts.empty:
        st.info("You haven't borrowed any books yet.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
        
    total_read = len(checkouts[checkouts['status'] == 'returned'])
    fav_genre = "None"
    if not checkouts.empty:
        fav_genre = checkouts['genre'].mode()[0] if not checkouts['genre'].mode().empty else "None"
        
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value">{total_read}</p>
            <p class="stat-label">Books Read</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_m2:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value" style="font-size: 1.8rem; margin-top: 10px;">{fav_genre}</p>
            <p class="stat-label">Favorite Genre</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    st.markdown("<h4 style='color: #1f2937;'>Checkout Log</h4>", unsafe_allow_html=True)
    
    def format_status(row):
        if row['status'] == 'returned':
            return f"Returned ({row['return_date']})"
        elif row['status'] == 'active':
            return "Active"
        elif row['status'] == 'overdue':
            return "⚠️ OVERDUE"
        return row['status']
        
    display_df = checkouts.copy()
    display_df['Status'] = display_df.apply(format_status, axis=1)
    display_df = display_df.rename(columns={
        'title': 'Title', 'author': 'Author', 'checkout_date': 'Checked Out', 'due_date': 'Due Date', 'copy_identifier': 'Copy ID'
    })
    
    with st.container(border=True):
        st.dataframe(display_df[['Title', 'Author', 'Copy ID', 'Checked Out', 'Due Date', 'Status']], use_container_width=True, hide_index=True)

        
    st.markdown('</div>', unsafe_allow_html=True)
