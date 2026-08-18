import streamlit as st

# Must be the very first Streamlit command
st.set_page_config(
    page_title="Library System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

import db
from views import auth, student, admin

def inject_css():
    """Inject custom CSS for styling (animations, badges, typography tweaks)."""
    custom_css = """
    <style>
        /* Import Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* Apply Inter to all text */
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
        }

        /* Modern Fade-in animation */
        .fade-in {
            opacity: 0;
            animation: slideUpFade 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        
        .stagger-1 { animation-delay: 0.1s; }
        .stagger-2 { animation-delay: 0.2s; }
        .stagger-3 { animation-delay: 0.3s; }
        .stagger-4 { animation-delay: 0.4s; }
        .stagger-5 { animation-delay: 0.5s; }

        @keyframes slideUpFade {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Gradient Text */
        .gradient-text {
            background: linear-gradient(135deg, #2563EB, #7C3AED);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            display: inline-block;
        }

        /* Custom Modern Stat Cards */
        .stat-card {
            background-color: white;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            transition: all 0.2s ease;
        }
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border-color: #d1d5db;
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: #111827;
            margin: 0;
            line-height: 1.2;
        }
        .stat-label {
            color: #6b7280;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.8rem;
            margin-top: 8px;
        }

        /* Modern Badges */
        .badge {
            display: inline-block;
            padding: 0.4em 1em;
            font-size: 0.75em;
            font-weight: 700;
            border-radius: 9999px;
            margin-top: 8px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .badge-avail {
            background: linear-gradient(135deg, #10B981, #059669);
            color: white;
            box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3);
            border: none;
        }
        .badge-out {
            background: linear-gradient(135deg, #EF4444, #DC2626);
            color: white;
            box-shadow: 0 4px 10px rgba(239, 68, 68, 0.3);
            border: none;
        }
        
        /* Button pulse and pop animation */
        [data-testid="baseButton-primary"] {
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            border-radius: 12px;
            font-weight: 700;
            letter-spacing: 0.02em;
            background: linear-gradient(135deg, #5B51D8, #8B5CF6);
            border: none;
        }
        [data-testid="baseButton-primary"]:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 10px 20px rgba(91, 81, 216, 0.35);
        }
        [data-testid="baseButton-primary"]:active {
            transform: scale(0.96);
        }

        /* Secondary buttons */
        [data-testid="baseButton-secondary"] {
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
            background-color: transparent;
            border: 2px solid #e5e7eb;
        }
        [data-testid="baseButton-secondary"]:hover {
            border-color: #5B51D8;
            color: #5B51D8;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(91, 81, 216, 0.1);
        }

        /* Hide default Streamlit sidebar */
        [data-testid="stSidebar"] {
            border-right: 1px solid #e5e7eb;
            background-color: #f9fafb;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def main():
    inject_css()
    
    # Initialize database and seed data if needed
    db.init_db()
    db.seed_if_empty()

    # Default view initialization
    if "view" not in st.session_state:
        st.session_state["view"] = "auth"

    # Routing
    view = st.session_state["view"]
    if view == "auth":
        auth.render()
    elif view == "student_dashboard":
        student.render()
    elif view == "admin_dashboard":
        admin.render()

if __name__ == "__main__":
    main()
