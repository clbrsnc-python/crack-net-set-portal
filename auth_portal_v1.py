import streamlit as st
import hashlib
import base64
import re
from supabase import Client

# ==========================================
SUBJECT_LIST = [
    "Paper 1 (General Paper)",
    "Bengali",
    "Chemical Sciences",
    "Commerce",
    "Computer Science & Applications",
    "Earth, Atmospheric, Ocean & Planetary Sciences",
    "Economics",
    "Education",
    "Electronic Science",
    "English",
    "Geography",
    "Hindi",
    "History",
    "Home Science",
    "Law",
    "Library & Information Science",
    "Life Sciences",
    "Management",
    "Mass Communication & Journalism",
    "Mathematical Sciences",
    "Philosophy",
    "Physical Sciences",
    "Political Science",
    "Psychology"
]

UNIT_LIST = [f"Unit {i}" for i in range(1, 11)]

# ==========================================
def hash_text(text: str) -> str:
    """Hashes string using SHA-256 for secure comparison."""
    return hashlib.sha256(text.strip().encode()).hexdigest()

def verify_credential(input_text: str, stored_val: str) -> bool:
    """Verifies input string against stored string (supports both plain text and SHA-256 hash)."""
    if not input_text or not stored_val:
        return False
    clean_input = input_text.strip()
    clean_stored = stored_val.strip()
    return clean_stored == clean_input or clean_stored == hash_text(clean_input)


def render_footer():
    """Renders mandatory copyright & attribution footer across all pages."""
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 10px; font-size: 0.9em;'>"
        "<strong>Curated by Dr. Joydip Chandra, BRSC</strong><br>"
        "Copyright 2026 All rights reserved"
        "</div>",
        unsafe_allow_html=True
    )

def render_auth_page():
    st.markdown("""
    <style>
    .stApp {
        background-color: #092169;
    }
    div[data-testid="stColumn"]:nth-child(1) {
        background-color: #092169;
        padding: 30px 20px;
        border-radius: 12px;
    }
    div[data-testid="stColumn"]:nth-child(2) {
        background-color: #EBF4FB;
        padding: 30px 25px;
        border-radius: 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    }
    div[data-baseweb="tab-list"] {
        background-color: transparent !important;
    }
    button[data-baseweb="tab"] {
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
    }
    .stButton>button {
        background-color: #EBF4FB !important;
        color: #FFFFFF !important;
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 1.1rem !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown(f"""
<div style="text-align: center; margin-bottom: 25px;">
    <img src="data:image/png;base64,{LOGO_B64}" style="width: 380px; max-width: 95%; height: auto; display: block; margin: 0 auto;">
</div>

<p style="font-family: 'Times New Roman', Times, serif; font-size: 1.2rem; line-height: 1.5; color: #FFFFFF; text-align: center; margin-bottom: 25px; padding: 0 10px;">
    Comprehensive online MCQ practice and mock test portal for UGC NET and SET.
</p>

<div style="display: flex; flex-direction: column; gap: 14px; text-align: left; max-width: 380px; margin: 0 auto 30px auto; font-family: 'Times New Roman', Times, serif; font-size: 1.05rem; color: #FFFFFF;">
    <div style="background: rgba(255,255,255,0.08); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #875e07;">
        🎯 <strong>Unit-wise Targeted Practice</strong>
    </div>
    <div style="background: rgba(255,255,255,0.08); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #875e07;">
        ⏱️ <strong>120-Min Full Paper Mocks</strong>
    </div>
    <div style="background: rgba(255,255,255,0.08); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #875e07;">
        📊 <strong>Instant Scoring & Detailed Solutions</strong>
    </div>
</div>

<div style="text-align: center; margin-top: 25px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.15); font-family: 'Times New Roman', Times, serif; font-size: 0.95rem; color: #E2E8F0;">
    Designed & Crafted by: <span style="color: #875e07; font-weight: bold;">Dr Joydip Chandra</span> | &copy; 2026
</div>
""", unsafe_allow_html=True)

    with col_right:
        st.markdown("""
<div style="background-color: #EBF4FB; font-family: 'Times New Roman', Times, serif;">
""", unsafe_allow_html=True)

        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔒 Login", "📝 New Registration", "🔑 Forgot Password"])

        with auth_tab1:
            st.markdown("<h3 style='font-family: \"Times New Roman\", Times, serif; color: #092169; margin-top: 10px; margin-bottom: 20px;'>Login to Your Account</h3>", unsafe_allow_html=True)
            with st.form("login_form"):
                email_input = st.text_input("Email Address").strip().lower()
                pass_input = st.text_input("Password", type="password").strip()
                login_submitted = st.form_submit_button("Sign In", use_container_width=True)

            if login_submitted:
                if not email_input or not pass_input:
                    st.warning("Please enter both email and password.")
                else:
                    try:
                        res = db.table("users").select("*").eq("email", email_input).execute()
                        if res.data and len(res.data) > 0:
                            user_data = res.data[0]
                            stored_password = user_data.get("password", "")

                            if verify_credential(pass_input, stored_password):
                                st.session_state.logged_in = True
                                st.session_state.user = user_data
                                st.session_state.role = user_data.get("role", "student")
                                st.success(f"Welcome back, {user_data.get('name', 'User')}!")
                                st.rerun()
                            else:
                                st.error("Incorrect password. Please try again.")
                        else:
                            st.error("No account found with this email address.")
                    except Exception as e:
                        st.error(f"Login failed: {e}")

        with auth_tab2:
            st.markdown("<h3 style='font-family: \"Times New Roman\", Times, serif; color: #092169; margin-top: 10px; margin-bottom: 20px;'>Create a New Account</h3>", unsafe_allow_html=True)
            with st.form("register_form", clear_on_submit=True):
                reg_name = st.text_input("Full Name")
                reg_email = st.text_input("Email Address").strip().lower()
                reg_subject = st.selectbox("Target Subject", SUBJECT_LIST)
                reg_pass = st.text_input("Password", type="password")
                reg_question = st.selectbox(
                    "Security Question",
                    [
                        "What is your mother's maiden name?",
                        "What was the name of your first pet?",
                        "What is your favorite book/subject?",
                        "What city were you born in?"
                    ]
                )
                reg_answer = st.text_input("Security Answer", type="password")
                reg_submitted = st.form_submit_button("Submit Registration", use_container_width=True)

            if reg_submitted:
                if not reg_name or not reg_email or not reg_pass or not reg_answer:
                    st.warning("Please fill in all required fields.")
                else:
                    try:
                        existing = db.table("users").select("email").eq("email", reg_email).execute()
                        if existing.data and len(existing.data) > 0:
                            st.error("An account with this email already exists.")
                        else:
                            new_user = {
                                "name": reg_name.strip(),
                                "email": reg_email,
                                "subject": reg_subject,
                                "password": hash_text(reg_pass),
                                "secret_question": reg_question,
                                "secret_answer": hash_text(reg_answer),
                                "role": "student"
                            }
                            db.table("users").insert(new_user).execute()
                            st.success("✅ Registration successful! Please switch to the Login tab to sign in.")
                    except Exception as e:
                        st.error(f"Registration failed: {e}")

        with auth_tab3:
            st.markdown("<h3 style='font-family: \"Times New Roman\", Times, serif; color: #092169; margin-top: 10px; margin-bottom: 20px;'>Reset Your Password</h3>", unsafe_allow_html=True)
            e_rec = st.text_input("Enter Registered Email").strip().lower()

            if e_rec:
                try:
                    user_res = db.table("users").select("secret_question", "secret_answer").eq("email", e_rec).execute()
                    if user_res.data and len(user_res.data) > 0:
                        user_record = user_res.data[0]
                        sec_q = user_record.get("secret_question", "Security Question")
                        stored_ans = user_record.get("secret_answer", "")

                        st.info(f"**Security Question:** {sec_q}")

                        with st.form("reset_pass_form"):
                            ans_input = st.text_input("Your Security Answer", type="password")
                            new_pass_input = st.text_input("Enter New Password", type="password")
                            reset_submitted = st.form_submit_button("Reset Password", use_container_width=True)

                        if reset_submitted:
                            if verify_credential(ans_input, stored_ans):
                                new_hashed_pass = hash_text(new_pass_input)
                                db.table("users").update({"password": new_hashed_pass}).eq("email", e_rec).execute()
                                st.success("✅ Password updated successfully! Please log in with your new password.")
                            else:
                                st.error("Incorrect security answer.")
                        else:
                            st.warning("Email address not found.")
                except Exception as e:
                    st.error(f"Error fetching user details: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    render_footer()
