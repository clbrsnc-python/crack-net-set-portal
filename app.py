import streamlit as st
from supabase import create_client, Client
from auth_portal_v3 import render_auth_page
from student_portal_v17 import render_student_portal
from admin_portal_v3 import render_admin_portal

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="OmniStride",
    page_icon="🎯",
    layout="wide"
)

# ==========================================
# SUPABASE CONNECTION SETUP
# ==========================================
@st.cache_resource
def get_supabase_client() -> Client:
    """Initialize and cache the Supabase client using Streamlit secrets."""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error("⚠️ Failed to connect to Supabase. Please ensure Secrets are configured correctly.")
        st.stop()

db = get_supabase_client()

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# Practice Test Engine Session States
if "test_active" not in st.session_state:
    st.session_state.test_active = False
if "test_completed" not in st.session_state:
    st.session_state.test_completed = False
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "current_q_idx" not in st.session_state:
    st.session_state.current_q_idx = 0
if "test_questions" not in st.session_state:
    st.session_state.test_questions = []
if "start_time" not in st.session_state:
    st.session_state.start_time = 0
if "time_limit" not in st.session_state:
    st.session_state.time_limit = 0
if "test_module" not in st.session_state:
    st.session_state.test_module = ""

# ==========================================
# MAIN APPLICATION ROUTER
# ==========================================
if not st.session_state.logged_in:
    render_auth_page(db)
else:
    # Sidebar Navigation & Attribution
    st.sidebar.title(f"👋 Welcome, {st.session_state.user.get('name', 'User')}")
    st.sidebar.write(f"**Role:** {st.session_state.role.upper()}")
    st.sidebar.write(f"**Subject:** {st.session_state.user.get('subject', 'N/A')}")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.role = None
        st.session_state.test_active = False
        st.session_state.test_completed = False
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Curated by Dr. Joydip Chandra, BRSC**\n\n"
        "Copyright 2026 All rights reserved"
    )

    # Route based on role
    if st.session_state.role == "admin":
        render_admin_portal(db)
    else:
        render_student_portal(db)
