from datetime import datetime
import streamlit as st
import pandas as pd
import db

def render():
    user = st.session_state.get("user")
    if not user or user["role"] != "admin":
        st.session_state["view"] = "auth"
        st.rerun()

    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    _render_header(user)

    if "admin_view" not in st.session_state:
        st.session_state["admin_view"] = "donations"

    _render_nav_pills()
    st.write("") # spacing

    # Route to sub-view
    av = st.session_state["admin_view"]
    if av == "donations":
        _render_donation_requests()
    elif av == "requests":
        _render_book_requests()
    elif av == "checkout":
        _render_checkout_return()
    elif av == "users":
        _render_manage_users()
    elif av == "history":
        _render_history()
    elif av == "books":
        _render_manage_books()

    st.markdown('</div>', unsafe_allow_html=True)

def _render_header(user):
    col_logo, col_title, col_logout = st.columns([1, 5, 1])
    with col_logo:
        st.image("assets/logo.jpg", use_container_width=True)
    with col_title:
        st.markdown(f"<h1 class='gradient-text fade-in stagger-1' style='margin-bottom:0;'>Admin Dashboard <span class='floating-icon'>⚙️</span></h1>", unsafe_allow_html=True)
        st.caption(f"Logged in as **{user['full_name']}**")

    with col_logout:
        st.write("")
        if st.button("Log Out", type="secondary"):
            st.session_state["user"] = None
            st.session_state["view"] = "auth"
            st.rerun()

def _render_nav_pills():
    st.markdown('<div class="fade-in stagger-2">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    def nav_btn(col, icon, label, view_name):
        with col:
            is_active = (st.session_state["admin_view"] == view_name)
            if st.button(f"{icon} {label}", key=f"nav_{view_name}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state["admin_view"] = view_name
                st.rerun()

    nav_btn(c1, "🎁", "Donations", "donations")
    nav_btn(c2, "📋", "Requests", "requests")
    nav_btn(c3, "🔁", "Checkout", "checkout")
    nav_btn(c4, "👤", "Users", "users")
    nav_btn(c5, "📖", "History", "history")
    nav_btn(c6, "📚", "Books", "books")
    st.markdown('</div>', unsafe_allow_html=True)

@st.fragment
def _render_donation_requests():
    st.markdown('<div class="fade-in stagger-3">', unsafe_allow_html=True)
    st.markdown("<h3 style='color: #1f2937;'>Donation Requests</h3>", unsafe_allow_html=True)
    donations = db.get_pending_donations()
    
    if donations.empty:
        st.info("No pending donation requests.")
    else:
        for i, d in donations.iterrows():
            stagger_class = f"stagger-{(i % 5) + 1}"
            st.markdown(f'<div class="fade-in {stagger_class}">', unsafe_allow_html=True)
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"<strong style='font-size:1.1em;'>{d['title']}</strong> by {d['author']}", unsafe_allow_html=True)
                    st.caption(f"Donated by: {d['student_name']} | Genre: {d['genre']} | Condition: {d['condition']}")
                    if d['review']:
                        st.write(f"**Review:** {d['review']} ({d['rating']}/5 stars)")
                with col2:
                    if st.button("Accept", key=f"acc_don_{d['id']}", type="primary", use_container_width=True):
                        _dialog_accept_donation(d)
                    if st.button("Reject", key=f"rej_don_{d['id']}", use_container_width=True):
                        _dialog_reject_donation(d)
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

@st.dialog("Accept Donation")
def _dialog_accept_donation(donation):
    st.write(f"Accepting **{donation['title']}** from {donation['student_name']}")
    with st.form(f"form_acc_{donation['id']}", clear_on_submit=True):
        loc = st.text_input("Drop-off Location", value="Front Desk")
        deadline = st.date_input("Drop-off Deadline", min_value=db.date.today())
        if st.form_submit_button("Confirm Acceptance"):
            db.accept_donation(donation['id'], loc, deadline)
            st.rerun()

@st.dialog("Reject Donation")
def _dialog_reject_donation(donation):
    st.write(f"Rejecting **{donation['title']}** from {donation['student_name']}")
    with st.form(f"form_rej_{donation['id']}", clear_on_submit=True):
        reason = st.text_area("Reason for rejection")
        if st.form_submit_button("Confirm Rejection"):
            db.reject_donation(donation['id'], reason)
            st.rerun()

@st.fragment
def _render_book_requests():
    st.markdown('<div class="fade-in stagger-3">', unsafe_allow_html=True)
    st.markdown("<h3 style='color: #1f2937;'>Book Requests (Holds)</h3>", unsafe_allow_html=True)
    reqs = db.get_pending_requests()
    
    if reqs.empty:
        st.info("No pending book requests.")
    else:
        display_df = reqs[['id', 'student_name', 'title', 'requested_date', 'queue_position', 'status']].copy()
        display_df.columns = ['ID', 'Student', 'Book', 'Requested', 'Queue #', 'Status']
        
        with st.container(border=True):
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.write("")
        st.markdown("<h4 style='color: #1f2937;'>Manage Request</h4>", unsafe_allow_html=True)
        with st.container(border=True):
            req_id = st.selectbox("Select Request ID to update", options=reqs['id'].tolist())
            
            if req_id:
                req = reqs[reqs['id'] == req_id].iloc[0]
                st.write(f"Selected: **{req['title']}** requested by **{req['student_name']}** (Current Status: {req['status']})")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Mark Available for Pickup", use_container_width=True, disabled=req['status']=='available'):
                        db.mark_request_available(req_id)
                        st.toast("Marked available and notified student.")
                        st.rerun()
                with col2:
                    if st.button("Mark Fulfilled", type="primary", use_container_width=True):
                        db.fulfill_request(req_id)
                        st.toast("Request fulfilled.")
                        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

@st.fragment
def _render_checkout_return():
    st.markdown('<div class="fade-in stagger-3">', unsafe_allow_html=True)
    st.markdown("<h3 style='color: #1f2937;'>Checkout & Return</h3>", unsafe_allow_html=True)
    
    tab_out, tab_in = st.tabs(["📚 Checkout Book", "📗 Return Book"])
    
    with tab_out:
        st.write("")
        users = db.get_all_users()
        active_users = users[users['status'] == 'active']
        copies = db.get_available_copies()
        
        if active_users.empty:
            st.warning("No active users to checkout to.")
        elif copies.empty:
            st.warning("No copies available to checkout.")
        else:
            user_options = {u['id']: f"{u['full_name']} ({u['username']})" for _, u in active_users.iterrows()}
            copy_options = {c['id']: f"{c['title']} - Copy: {c['copy_identifier']}" for _, c in copies.iterrows()}
            
            with st.container(border=True):
                with st.form("admin_checkout_form", clear_on_submit=True):
                    sel_user_id = st.selectbox("Select Student", options=list(user_options.keys()), format_func=lambda x: user_options[x])
                    sel_copy_id = st.selectbox("Select Physical Copy", options=list(copy_options.keys()), format_func=lambda x: copy_options[x])
                    
                    st.write("")
                    submitted = st.form_submit_button("Confirm Checkout", type="primary")
                    if submitted:
                        overdue = db.count_overdue(sel_user_id)
                        if overdue >= 3:
                            st.error(f"Cannot checkout. Student has {overdue} overdue books.")
                        else:
                            if db.checkout_copy(sel_user_id, sel_copy_id):
                                st.success(f"Successfully checked out to {user_options[sel_user_id]}.")
                            else:
                                st.error("Checkout failed (copy may have become unavailable).")

    with tab_in:
        st.write("")
        active_cos = db.get_active_checkouts()
        if active_cos.empty:
            st.info("No active checkouts.")
        else:
            co_options = {
                c['id']: f"{c['student_name']} - {c['title']} (Due: {c['due_date']})" 
                for _, c in active_cos.iterrows()
            }
            with st.container(border=True):
                with st.form("admin_return_form", clear_on_submit=True):
                    sel_co_id = st.selectbox("Select Checkout to Return", options=list(co_options.keys()), format_func=lambda x: co_options[x])
                    st.write("")
                    if st.form_submit_button("Confirm Return", type="primary"):
                        db.return_book(sel_co_id)
                        st.success("Book returned successfully.")
                        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

@st.fragment
def _render_manage_users():
    st.markdown('<div class="fade-in stagger-3">', unsafe_allow_html=True)
    st.markdown("<h3 style='color: #1f2937;'>Manage Users</h3>", unsafe_allow_html=True)
    
    pending = db.get_pending_users()
    if not pending.empty:
        st.markdown(f"<h4 style='color: #F59E0B;'>Pending Approvals ({len(pending)})</h4>", unsafe_allow_html=True)
        for i, u in pending.iterrows():
            stagger_class = f"stagger-{(i % 5) + 1}"
            st.markdown(f'<div class="fade-in {stagger_class}">', unsafe_allow_html=True)
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"<strong style='font-size:1.1em;'>{u['full_name']}</strong> ({u['username']}) - Grade {u['grade']}", unsafe_allow_html=True)
                    st.caption(f"Email: {u['email']} | Parent: {u['parent_name']} ({u['parent_email']})")
                with col2:
                    if st.button("Approve", key=f"app_u_{u['id']}", type="primary", use_container_width=True):
                        db.approve_user(u['id'])
                        st.rerun()
                    if st.button("Reject", key=f"rej_u_{u['id']}", use_container_width=True):
                        db.reject_user(u['id'])
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.write("")

    with st.expander("➕ Add New User"):
        with st.form("add_user_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            full_name = col_a.text_input("Full Name *")
            email = col_b.text_input("Email *")
            
            username = col_a.text_input("Username *")
            password = col_b.text_input("Password *", type="password")
            
            role = col_a.selectbox("Role", ["student", "admin"])
            status = col_b.selectbox("Status", ["active", "pending"])
            
            st.write("")
            if st.form_submit_button("Add User", type="primary"):
                if not all([full_name, email, username, password]):
                    st.error("Please fill in all required fields.")
                else:
                    success = db.create_user(
                        username=username, password=password, full_name=full_name,
                        email=email, dob="N/A", grade="N/A", school="N/A",
                        role=role, status=status
                    )
                    if success:
                        st.success(f"User '{username}' added successfully!")
                        st.rerun()
                    else:
                        st.error("Username already taken.")

    st.write("")
    st.markdown("<h4 style='color: #1f2937;'>All Users</h4>", unsafe_allow_html=True)
    all_users = db.get_all_users()
    
    st.write("Edit 'status' or 'role' directly below:")
    with st.container(border=True):
        edited_users = st.data_editor(
            all_users,
            column_config={
                "id": None, 
                "status": st.column_config.SelectboxColumn("Status", options=["active", "pending", "suspended", "rejected"]),
                "role": st.column_config.SelectboxColumn("Role", options=["student", "admin"]),
                "created_at": st.column_config.DatetimeColumn("Created At", disabled=True),
            },
            disabled=["username", "full_name", "email", "grade", "school"],
            hide_index=True,
            key="users_editor",
            use_container_width=True
        )
    
    if "users_editor" in st.session_state:
        changes = st.session_state["users_editor"].get("edited_rows", {})
        if changes:
            for row_idx, updates in changes.items():
                user_id = all_users.iloc[row_idx]['id']
                if "status" in updates:
                    db.update_user_status(user_id, updates["status"])
            st.success("User(s) updated.")
            st.rerun()
            
    st.write("")
    with st.expander("🗑️ Delete a User"):
        del_id = st.selectbox("Select user to delete", options=all_users['id'].tolist(), format_func=lambda x: all_users[all_users['id']==x]['username'].iloc[0])
        if st.button("Delete User", type="primary"):
            _dialog_delete_user(del_id, all_users[all_users['id']==del_id]['username'].iloc[0])
    st.markdown('</div>', unsafe_allow_html=True)

@st.dialog("Confirm Deletion")
def _dialog_delete_user(user_id, username):
    st.warning(f"Are you sure you want to delete user '{username}'? This cannot be undone.")
    if st.button("Yes, Delete", type="primary"):
        db.delete_user(user_id)
        st.rerun()

@st.fragment
def _render_history():
    st.markdown('<div class="fade-in stagger-3">', unsafe_allow_html=True)
    st.markdown("<h3 style='color: #1f2937;'>Borrowing History</h3>", unsafe_allow_html=True)
    
    with st.container(border=True):
        col_s, col_stat, col_dt1, col_dt2 = st.columns(4)
        search = col_s.text_input("🔍 Search student/book")
        status = col_stat.selectbox("Status", ["All", "active", "returned", "overdue"])
        date_from = col_dt1.date_input("From", value=None)
        date_to = col_dt2.date_input("To", value=None)
    
    df = db.get_all_checkouts_filtered(search, status, date_from, date_to)
    
    if df.empty:
        st.info("No records found.")
    else:
        st.write("")
        col_m1, col_m2 = st.columns(2)
        most_borrowed = df['title'].mode()[0] if not df['title'].mode().empty else "N/A"
        this_month = len(df[pd.to_datetime(df['checkout_date']).dt.month == datetime.now().month])
        
        with col_m1:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-value" style="font-size: 1.5rem; margin-top: 15px;">{most_borrowed}</p>
                <p class="stat-label">Most Borrowed Book</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_m2:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-value">{this_month}</p>
                <p class="stat-label">Checkouts This Month</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        with st.container(border=True):
            disp_df = df[['id', 'student_name', 'title', 'copy_identifier', 'checkout_date', 'due_date', 'return_date', 'status']]
            disp_df.columns = ['ID', 'Student', 'Book', 'Copy ID', 'Checked Out', 'Due Date', 'Return Date', 'Status']
            st.dataframe(disp_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

@st.fragment
def _render_manage_books():
    st.markdown('<div class="fade-in stagger-3">', unsafe_allow_html=True)
    st.markdown("<h3 style='color: #1f2937;'>Manage Library Books</h3>", unsafe_allow_html=True)
    
    with st.expander("➕ Add New Book"):
        with st.form("add_book_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            title = col1.text_input("Title *")
            author = col2.text_input("Author *")
            
            genres = db.get_genres()
            genre = col1.selectbox("Genre *", genres + ["New Genre..."])
            if genre == "New Genre...":
                genre = col1.text_input("Specify Genre *")
                
            copies = col2.number_input("Total Copies *", min_value=1, value=1)
            desc = st.text_area("Description")
            
            st.write("")
            if st.form_submit_button("Add Book", type="primary"):
                if not title or not author or not genre:
                    st.error("Title, Author, and Genre are required.")
                else:
                    db.add_book(title, author, genre, desc, copies)
                    st.success(f"Added '{title}'!")
                    st.rerun()
                    
    st.write("")
    st.markdown("<h4 style='color: #1f2937;'>Book Catalog</h4>", unsafe_allow_html=True)
    books = db.get_all_books()
    
    st.write("Edit title, author, genre, or copies directly:")
    with st.container(border=True):
        edited_books = st.data_editor(
            books[['id', 'title', 'author', 'genre', 'total_copies', 'available_copies', 'avg_rating']],
            column_config={
                "id": None,
                "avg_rating": st.column_config.NumberColumn("Rating", disabled=True),
                "total_copies": st.column_config.NumberColumn("Total", disabled=True),
                "available_copies": st.column_config.NumberColumn("Available", disabled=True)
            },
            hide_index=True,
            key="books_editor",
            use_container_width=True
        )
    
    if "books_editor" in st.session_state:
        changes = st.session_state["books_editor"].get("edited_rows", {})
        if changes:
            for row_idx, updates in changes.items():
                book_id = books.iloc[row_idx]['id']
                db.update_book(int(book_id), **updates)
            st.success("Book(s) updated.")
            st.rerun()

    st.write("")
    with st.expander("🗑️ Delete a Book"):
        del_id = st.selectbox("Select book to delete", options=books['id'].tolist(), format_func=lambda x: books[books['id']==x]['title'].iloc[0])
        if st.button("Delete Book", type="primary"):
            _dialog_delete_book(del_id, books[books['id']==del_id]['title'].iloc[0])
    st.markdown('</div>', unsafe_allow_html=True)

@st.dialog("Confirm Deletion")
def _dialog_delete_book(book_id, title):
    st.warning(f"Are you sure you want to delete '{title}'? This will fail if there are active checkouts for this book.")
    if st.button("Yes, Delete", type="primary"):
        try:
            db.delete_book(book_id)
            st.rerun()
        except Exception as e:
            st.error(f"Cannot delete book. Ensure it is not currently checked out. Error: {e}")
