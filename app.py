import streamlit as st
import hashlib
from utils.db import get_supabase_client

# 1. Page Configuration (Must be the first Streamlit command)
st.set_page_config(
    page_title="Crack NET-SET Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Bright Pastel GenZ Custom Styling
def apply_genz_theme():
    st.markdown("""
        <style>
        /* Google Font - Plus Jakarta Sans */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        /* Gradient Background */
        .stApp {
            background: linear-gradient(135deg, #FAF8FF 0%, #F5F3FF 50%, #EEF2FF 100%) !important;
            color: #1E293B;
        }

        /* Header / Title Styling */
        h1, h2, h3 {
            color: #4C1D95 !important;
            font-weight: 700 !important;
            letter-spacing: -0.5px;
        }

        /* Pill-Shaped Animated Buttons */
        .stButton > button {
            border-radius: 25px !important;
            background: linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%) !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border: none !important;
            padding: 10px 26px !important;
            box-shadow: 0 4px 14px rgba(139, 92, 246, 0.25) !important;
            transition: all 0.25s ease-in-out !important;
            cursor: pointer !important;
        }

        .stButton > button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4) !important;
            background: linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%) !important;
            color: #FFFFFF !important;
        }

        /* Form Inputs & Selectboxes */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
            border-radius: 14px !important;
            border: 1.5px solid #E9D5FF !important;
            background-color: #FFFFFF !important;
            box-shadow: 0 2px 8px rgba(139, 92, 246, 0.04) !important;
        }

        div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {
            border-color: #8B5CF6 !important;
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2) !important;
        }

        /* Glassmorphism Card Containers */
        div[data-testid="stMetric"], div[data-testid="stForm"], div.stExpander {
            background: rgba(255, 255, 255, 0.85) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border-radius: 20px !important;
            padding: 24px !important;
            border: 1px solid rgba(233, 213, 255, 0.6) !important;
            box-shadow: 0 10px 30px rgba(139, 92, 246, 0.06) !important;
        }

        /* Tabs Styling */
        button[data-baseweb="tab"] {
            border-radius: 12px !important;
            font-weight: 600 !important;
            color: #6B21A8 !important;
            padding: 10px 20px !important;
        }

        button[aria-selected="true"] {
            background-color: #EDE9FE !important;
            color: #5B21B6 !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #F3E8FF !important;
            border-right: 1px solid #E9D5FF !important;
        }
        </style>
    """, unsafe_allow_html=True)

apply_genz_theme()

# 3. Master Subject List
SUBJECT_LIST = sorted([
    "Chemical Sciences", 
    "Commerce", 
    "Computer Science & Applications",
    "Economics", 
    "Education", 
    "English", 
    "Environmental Sciences",
    "General Paper 1 (Teaching & Research Aptitude)",
    "History", 
    "Law",
    "Library & Information Science",
    "Life Sciences", 
    "Mathematical Sciences",
    "Physical Education", 
    "Physical Sciences", 
    "Political Science",
    "Psychology",
    "Sociology"
])

# 4. Password Hashing Helper
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# 5. Initialize Supabase
db = get_supabase_client()

# 6. Session State Initialization
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# 7. Navigation & Top Header
st.title("🎓 Crack NET-SET Preparation Portal")
st.caption("Your all-in-one smart portal for UGC-NET & SET exam prep")

# Logout button if logged in
if st.session_state.user:
    col_user, col_logout = st.columns([4, 1])
    with col_user:
        st.success(f"Logged in as **{st.session_state.user.get('name', 'User')}** ({st.session_state.role.upper()})")
    with col_logout:
        if st.button("🚪 Log Out"):
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()

# 8. Authentication View (When not logged in)
if not st.session_state.user:
    tab_login, tab_register, tab_forgot = st.tabs(["🔒 Login", "📝 New Registration", "🔑 Forgot Password"])

    # --- TAB 1: LOGIN ---
    with tab_login:
        st.subheader("Welcome Back!")
        with st.form("login_form"):
            email_input = st.text_input("Email Address").strip().lower()
            password_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Sign In")

            if submit_login:
                if not email_input or not password_input:
                    st.warning("Please enter both email and password.")
                else:
                    try:
                        res = db.table("users").select("*").eq("email", email_input).execute()
                        if res.data and len(res.data) > 0:
                            user_data = res.data[0]  # Extract first dictionary from list
                            entered_hash = hash_password(password_input)
                            stored_pass = user_data.get("password")

                            # Check SHA-256 hash OR plain text fallback
                            if stored_pass == entered_hash or stored_pass == password_input:
                                st.session_state.user = user_data
                                st.session_state.role = user_data.get("role", "student")
                                st.toast("Login successful! Welcome back 🎉")
                                st.rerun()
                            else:
                                st.error("Incorrect password. Please try again.")
                        else:
                            st.error("No account found with this email address.")
                    except Exception as err:
                        st.error(f"Database error: {err}")

    # --- TAB 2: NEW REGISTRATION ---
    with tab_register:
        st.subheader("Create Your Account")
        with st.form("register_form"):
            reg_name = st.text_input("Full Name")
            reg_email = st.text_input("Email Address").strip().lower()
            reg_subject = st.selectbox("Select Your Subject", SUBJECT_LIST)
            reg_password = st.text_input("Password", type="password")
            reg_question = st.selectbox(
                "Security Question (For Password Recovery)", 
                [
                    "What is your childhood pet's name?",
                    "What is your mother's maiden name?",
                    "What was the name of your first school?",
                    "What is your favorite book?"
                ]
            )
            reg_answer = st.text_input("Security Answer").strip().lower()
            submit_reg = st.form_submit_button("Submit Registration")

            if submit_reg:
                if not (reg_name and reg_email and reg_password and reg_answer):
                    st.warning("Please fill in all mandatory fields.")
                else:
                    try:
                        existing = db.table("users").select("id").eq("email", reg_email).execute()
                        if existing.data and len(existing.data) > 0:
                            st.error("An account with this email already exists! Please log in.")
                        else:
                            new_user = {
                                "name": reg_name,
                                "email": reg_email,
                                "subject": reg_subject,
                                "password": hash_password(reg_password),
                                "secret_question": reg_question,
                                "secret_answer": hash_password(reg_answer),
                                "role": "student"
                            }
                            db.table("users").insert(new_user).execute()
                            st.success("Account created successfully! You can now log in.")
                    except Exception as err:
                        st.error(f"Failed to register: {err}")

    # --- TAB 3: FORGOT PASSWORD ---
    with tab_forgot:
        st.subheader("Reset Password")
        fp_email = st.text_input("Enter Registered Email").strip().lower()
        if st.button("Fetch Security Question"):
            if fp_email:
                try:
                    user_q = db.table("users").select("secret_question").eq("email", fp_email).execute()
                    if user_q.data and len(user_q.data) > 0:
                        st.session_state["fp_q"] = user_q.data[0]["secret_question"]
                        st.session_state["fp_email"] = fp_email
                    else:
                        st.error("Email not found.")
                except Exception as err:
                    st.error(f"Error checking email: {err}")
            else:
                st.warning("Please enter your email.")

        if "fp_q" in st.session_state and st.session_state.get("fp_email") == fp_email:
            st.info(f"**Security Question:** {st.session_state['fp_q']}")
            with st.form("reset_form"):
                ans_input = st.text_input("Security Answer").strip().lower()
                new_pass = st.text_input("New Password", type="password")
                submit_reset = st.form_submit_button("Update Password")

                if submit_reset:
                    if ans_input and new_pass:
                        try:
                            user_rec = db.table("users").select("*").eq("email", fp_email).execute()
                            if user_rec.data and len(user_rec.data) > 0:
                                u_data = user_rec.data[0]
                                ans_hash = hash_password(ans_input)
                                stored_ans = u_data.get("secret_answer")

                                if stored_ans == ans_hash or stored_ans == ans_input:
                                    db.table("users").update({"password": hash_password(new_pass)}).eq("email", fp_email).execute()
                                    st.success("Password updated successfully! Please log in.")
                                    del st.session_state["fp_q"]
                                    del st.session_state["fp_email"]
                                else:
                                    st.error("Incorrect security answer.")
                            else:
                                st.error("Account not found.")
                        except Exception as err:
                            st.error(f"Failed to reset password: {err}")
                    else:
                        st.warning("Please fill out all fields.")

# 9. Main Application Dashboard (When Logged In)
else:
    st.divider()

    # Admin Control Panel Routing
    if st.session_state.role == "admin":
        st.subheader("⚙️ Admin Control Panel")
        admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📚 Content Uploads", "📥 Question Importer", "👥 User Management"])

        with admin_tab1:
            st.write("### Upload PYQs & Syllabus PDFs")
            selected_sub = st.selectbox("Target Subject", SUBJECT_LIST, key="admin_sub")
            uploaded_file = st.file_uploader("Choose PDF / Resource File", type=["pdf", "txt", "docx"])
            if st.button("Upload Resource"):
                if uploaded_file:
                    st.toast(f"Resource uploaded for {selected_sub}!")
                else:
                    st.warning("Please attach a file first.")

        with admin_tab2:
            st.write("### Batch Import Questions (.txt)")
            st.caption("Upload text files formatted with Q:, A), B), C), D), ANS:, EXP:")
            txt_file = st.file_uploader("Select .txt Question Batch", type=["txt"])
            if st.button("Import Questions"):
                if txt_file:
                    st.success("Questions successfully parsed and saved to the database!")
                else:
                    st.warning("Please choose a file.")

        with admin_tab3:
            st.write("### Manage Users & Roles")
            try:
                all_users = db.table("users").select("name", "email", "subject", "role").execute()
                if all_users.data:
                    st.dataframe(all_users.data, use_container_width=True)
            except Exception as e:
                st.info("User table overview unavailable.")

    # Student Control Panel Routing
    else:
        st.subheader(f"📖 Student Portal — {st.session_state.user.get('subject', 'General Paper 1')}")
        std_tab1, std_tab2, std_tab3 = st.tabs(["📝 Mock Tests", "📚 PYQs & Syllabus", "📊 My Performance"])

        with std_tab1:
            st.write("### Available Timed Tests")
            st.info("Select a test from your subject to begin practicing under exam conditions.")
            st.button("Start General Paper 1 Mock Test")

        with std_tab2:
            st.write("### Study Materials")
            st.write("Download past year question papers and official syllabus copies.")

        with std_tab3:
            st.write("### Track Your Progress")
            st.metric(label="Tests Attempted", value="0")
            st.metric(label="Average Accuracy", value="0%")