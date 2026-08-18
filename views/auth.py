import streamlit as st
import db

def render():
    # If a user is already in session, redirect to their dashboard
    if "user" in st.session_state and st.session_state["user"]:
        user = st.session_state["user"]
        if user["role"] == "admin":
            st.session_state["view"] = "admin_dashboard"
        else:
            st.session_state["view"] = "student_dashboard"
        st.rerun()

    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "login"

    # Split-screen layout
    col_left, col_right = st.columns([1.2, 1], gap="large")

    with col_left:
        st.markdown('<div class="fade-in stagger-1">', unsafe_allow_html=True)
        st.write("")
        st.write("")
        st.write("")
        st.markdown("<h1 class='gradient-text' style='font-size: 3.5rem; margin-bottom: 0;'>Welcome to the<br>Library System</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #6b7280; font-weight: 400; margin-top: 10px;'>Your gateway to infinite knowledge, organized and accessible.</h3>", unsafe_allow_html=True)
        st.write("")
        st.image("assets/logo.jpg", width=250)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.write("")
        st.write("")
        if st.session_state["auth_mode"] == "login":
            _render_login()
        else:
            _render_signup()

def _render_login():
    st.markdown('<div class="fade-in stagger-2">', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<h3 style='margin-bottom: 20px; font-weight: 700;'>Log in to your account</h3>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            st.write("") # spacing
            submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                user = db.authenticate(username, password)
                if user:
                    if user["status"] == "pending":
                        st.warning("Your account is still under review by the librarian.")
                    elif user["status"] == "rejected":
                        st.error("Your registration was not approved.")
                    elif user["status"] == "suspended":
                        st.error("Your account has been suspended.")
                    else:
                        st.session_state["user"] = user
                        st.success(f"Welcome back, {user['full_name']}!")
                        if user["role"] == "admin":
                            st.session_state["view"] = "admin_dashboard"
                        else:
                            st.session_state["view"] = "student_dashboard"
                        st.rerun()
                else:
                    st.error("Invalid username or password.")

        st.write("")
        st.markdown("<p style='text-align: center; color: #6b7280;'>Don't have an account?</p>", unsafe_allow_html=True)
        if st.button("Create an account", use_container_width=True):
            st.session_state["auth_mode"] = "signup"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def _render_signup():
    st.markdown('<div class="fade-in stagger-2">', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<h3 style='margin-bottom: 20px; font-weight: 700;'>Create an account</h3>", unsafe_allow_html=True)
        
        with st.form("signup_form", clear_on_submit=True):
            st.markdown("<p style='font-weight: 600; color: #5B51D8; margin-bottom: 5px;'>Student Details</p>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            full_name = col_a.text_input("Full Name *")
            email = col_b.text_input("School Email *")
            
            col_c, col_d = st.columns(2)
            dob = col_c.date_input("Date of Birth *", min_value=db.date(1900, 1, 1), max_value=db.date.today())
            grade = col_d.selectbox("Grade Level *", ["6", "7", "8", "9", "10", "11", "12"])
            school = st.text_input("School Name *", value="Greenfield Academy")
            
            st.markdown("<p style='font-weight: 600; color: #5B51D8; margin-bottom: 5px; margin-top: 15px;'>Account Details</p>", unsafe_allow_html=True)
            username = st.text_input("Choose a Username *")
            col_e, col_f = st.columns(2)
            password = col_e.text_input("Password *", type="password")
            confirm_pwd = col_f.text_input("Confirm Password *", type="password")

            st.markdown("<p style='font-weight: 600; color: #5B51D8; margin-bottom: 5px; margin-top: 15px;'>Parent / Guardian Info</p>", unsafe_allow_html=True)
            parent_name = st.text_input("Parent/Guardian Name *")
            col_g, col_h = st.columns(2)
            parent_email = col_g.text_input("Parent/Guardian Email *")
            parent_phone = col_h.text_input("Parent/Guardian Phone")

            st.markdown("<p style='font-weight: 600; color: #5B51D8; margin-bottom: 5px; margin-top: 15px;'>Digital Waiver</p>", unsafe_allow_html=True)
            st.info("By checking the box below, you agree to the Library Rules: to treat books with care, return them on time, and pay for lost or damaged materials.")
            waiver_sig = st.text_input("Parent/Guardian Digital Signature (Type full name) *")
            waiver_agree = st.checkbox("I agree to the Library Rules *")

            st.write("")
            submitted = st.form_submit_button("Submit Registration", use_container_width=True, type="primary")

        if submitted:
            if not all([full_name, email, username, password, confirm_pwd, parent_name, parent_email, waiver_sig]):
                st.error("Please fill in all required fields.")
            elif password != confirm_pwd:
                st.error("Passwords do not match.")
            elif not waiver_agree:
                st.error("You must agree to the Library Rules.")
            else:
                success = db.create_user(
                    username=username, password=password, full_name=full_name,
                    email=email, dob=dob, grade=grade, school=school,
                    parent_name=parent_name, parent_email=parent_email,
                    parent_phone=parent_phone, waiver_signature=waiver_sig
                )
                if success:
                    st.success("Registration successful!")
                    st.info("Your account is pending approval by the librarian. You will not be able to log in until it is approved.")
                else:
                    st.error("Username is already taken. Please choose another.")

        st.write("")
        st.markdown("<p style='text-align: center; color: #6b7280;'>Already have an account?</p>", unsafe_allow_html=True)
        if st.button("Log in", use_container_width=True):
            st.session_state["auth_mode"] = "login"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
