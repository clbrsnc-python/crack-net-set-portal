import streamlit as st
import hashlib
from supabase import create_client, Client

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Crack NET/SET Portal",
    page_icon="📚",
    layout="wide"
)

# ==========================================
# MASTER SUBJECT LIST
# (Centralized subject list used across the entire portal)
# ==========================================
SUBJECT_LIST = [
    "Bengali",
    "Chemical Sciences",
    "Commerce",
    "Computer Science & Applications",
    "Earth, Atmospheric, Ocean & Planetary Sciences",
    "Economics",
    "Education",
    "Electronic Science",
    "English",
    "General Paper",
    "Geography",
    "Hindi",
    "History",
    "Home Science",
    "Law",
    "Library & Information Science",
    "Life Sciences",
    "Mass Communication & Journalism",
    "Mathematical Sciences",
    "Philosophy",
    "Physical Sciences",
    "Political Science",
    "Psychology",
    "Management",
]

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
# HELPER FUNCTIONS
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

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# ==========================================
# AUTHENTICATION PORTAL (LOGIN / REGISTER / RESET)
# ==========================================
def render_auth_page():
    st.title("📚 Crack NET/SET Learning & Exam Portal")
    st.markdown("---")
    
    auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔒 Login", "📝 New Registration", "🔑 Forgot Password"])
    
    # ------------------------------------------
    # TAB 1: LOGIN
    # ------------------------------------------
    with auth_tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            email_input = st.text_input("Email Address").strip().lower()
            pass_input = st.text_input("Password", type="password").strip()
            login_submitted = st.form_submit_button("Sign In")
            
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

    # ------------------------------------------
    # TAB 2: NEW REGISTRATION
    # ------------------------------------------
    with auth_tab2:
        st.subheader("Create a New Account")
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
            reg_submitted = st.form_submit_button("Submit Registration")
            
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

    # ------------------------------------------
    # TAB 3: FORGOT PASSWORD
    # ------------------------------------------
    with auth_tab3:
        st.subheader("Reset Your Password")
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
                        reset_submitted = st.form_submit_button("Reset Password")
                        
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

# ==========================================
# MAIN APPLICATION LOGIC
# ==========================================
if not st.session_state.logged_in:
    render_auth_page()
else:
    # Sidebar
    st.sidebar.title(f"👋 Welcome, {st.session_state.user.get('name', 'User')}")
    st.sidebar.write(f"**Role:** {st.session_state.role.upper()}")
    st.sidebar.write(f"**Subject:** {st.session_state.user.get('subject', 'N/A')}")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

    # ------------------------------------------
    # ADMIN CONTROL PANEL
    # ------------------------------------------
    if st.session_state.role == "admin":
        st.title("⚙️ Admin Control Panel")
        admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📚 Content & Link Uploads", "📥 Question Importer", "👥 User Management"])

        # ======================================
        # ADMIN TAB 1: CONTENT & LINK UPLOADS
        # ======================================
        with admin_tab1:
            st.markdown("### 📚 Upload Resources, Notes & External Links")
            
            # Dynamic radio selector OUTSIDE st.form for instant re-render
            resource_type = st.radio(
                "Select Resource Type",
                ["📄 File Upload (PDF, TXT, DOCX)", "🔗 External Link (YouTube, Drive, Web Link)"],
                horizontal=True
            )
            
            with st.form("content_upload_form", clear_on_submit=True):
                title = st.text_input("Resource / Link Title", placeholder="e.g. Paper 1 Unit 1 Complete Notes / Video Lecture")
                subject = st.selectbox("Select Subject", SUBJECT_LIST)
                category = st.selectbox(
                    "Select Resource Category",
                    ["Syllabus", "Learning Resources", "PYQs", "Video Lectures", "Useful Links"]
                )
                
                uploaded_file = None
                link_input = ""
                
                if "File Upload" in resource_type:
                    uploaded_file = st.file_uploader("Upload Document File", type=["pdf", "txt", "docx"])
                else:
                    link_input = st.text_input("Paste Link (YouTube URL, Google Drive, Website Link)", placeholder="https://...")
                
                submit_btn = st.form_submit_button("🚀 Save & Publish Resource")

            if submit_btn:
                if not title.strip():
                    st.warning("Please enter a title for the resource.")
                elif "File Upload" in resource_type and not uploaded_file:
                    st.warning("Please select a file to upload.")
                elif "External Link" in resource_type and not link_input.strip():
                    st.warning("Please enter a valid URL / link.")
                else:
                    with st.spinner("Publishing resource..."):
                        try:
                            final_url = ""
                            
                            if "File Upload" in resource_type and uploaded_file:
                                file_bytes = uploaded_file.read()
                                file_path = f"{category}/{uploaded_file.name}"
                                db.storage.from_("net-set-materials").upload(
                                    file_path, 
                                    file_bytes, 
                                    file_options={"content-type": uploaded_file.type, "upsert": "true"}
                                )
                                final_url = db.storage.from_("net-set-materials").get_public_url(file_path)
                            else:
                                final_url = link_input.strip()
                            
                            content_data = {
                                "title": title.strip(),
                                "subject": subject,
                                "category": category,
                                "file_url": final_url
                            }
                            db.table("content").insert(content_data).execute()
                            st.success(f"✅ Successfully published **'{title}'** under **{category}** ({subject})!")
                        except Exception as e:
                            st.error(f"❌ Failed to publish: {e}")

        # ======================================
        # ADMIN TAB 2: QUESTION IMPORTER
        # ======================================
        with admin_tab2:
            st.markdown("### 📥 Question Importer")
            st.info("Parse and import multiple-choice questions (MCQs) into the database.")
            
            with st.form("question_import_form", clear_on_submit=True):
                q_subject = st.selectbox("Subject for Questions", SUBJECT_LIST)
                q_topic = st.text_input("Topic / Unit Name", placeholder="e.g. Teaching Aptitude")
                q_text = st.text_area("Paste MCQ Block (Question, Options A-D, Answer, Explanation)", height=200)
                q_submit = st.form_submit_button("Import Questions")
                
            if q_submit:
                if q_text.strip():
                    try:
                        q_data = {
                            "subject": q_subject,
                            "topic": q_topic,
                            "question_text": q_text.strip()
                        }
                        db.table("questions").insert(q_data).execute()
                        st.success("✅ Questions imported successfully!")
                    except Exception as e:
                        st.error(f"Failed to import questions: {e}")
                else:
                    st.warning("Please enter question text.")

        # ======================================
        # ADMIN TAB 3: USER MANAGEMENT
        # ======================================
        with admin_tab3:
            st.markdown("### 👥 Manage Registered Users")
            try:
                users_res = db.table("users").select("id, name, email, subject, role").execute()
                if users_res.data:
                    st.dataframe(users_res.data, use_container_width=True)
                    st.markdown("#### Promote/Change User Role")
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        target_email = st.selectbox("Select User Email", [u["email"] for u in users_res.data])
                    with col2:
                        new_role = st.selectbox("Select New Role", ["student", "admin"])
                    
                    if st.button("Update User Role"):
                        db.table("users").update({"role": new_role}).eq("email", target_email).execute()
                        st.success(f"Updated {target_email} role to {new_role}!")
                        st.rerun()
                else:
                    st.info("No registered users found.")
            except Exception as e:
                st.error(f"Failed to fetch users: {e}")

    # ------------------------------------------
    # STUDENT LEARNING & QUIZ PORTAL
    # ------------------------------------------
    else:
        st.title("🎓 Student Learning Portal")
        student_tab1, student_tab2 = st.tabs(["📚 Study Resources & Links", "📝 Practice Quizzes"])

        # ======================================
        # STUDENT TAB 1: STUDY RESOURCES & LINKS
        # ======================================
        with student_tab1:
            st.subheader("📚 Learning Resources, PYQs & Video/Web Links")
            
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                cat_filter = st.selectbox("Filter by Category", ["All Categories", "Syllabus", "Learning Resources", "PYQs", "Video Lectures", "Useful Links"])
            with filter_col2:
                subj_filter = st.selectbox("Filter by Subject", ["All Subjects"] + SUBJECT_LIST)
            
            try:
                query = db.table("content").select("*")
                if cat_filter != "All Categories":
                    query = query.eq("category", cat_filter)
                if subj_filter != "All Subjects":
                    query = query.eq("subject", subj_filter)
                    
                res = query.execute()
                
                if res.data and len(res.data) > 0:
                    for item in res.data:
                        title = item.get('title', 'Untitled Resource')
                        cat = item.get('category', 'General')
                        subj = item.get('subject', 'General')
                        url = item.get('file_url', '')
                        
                        with st.expander(f"📌 {title} ({cat})"):
                            st.write(f"**Subject:** {subj}")
                            st.write(f"**Category:** {cat}")
                            
                            if url:
                                if "youtube.com" in url or "youtu.be" in url:
                                    st.markdown("#### 🎬 Embedded Video Lecture")
                                    st.video(url)
                                else:
                                    st.markdown(f"[🔗 Open / Download Resource]({url})")
                            else:
                                st.info("No link attached.")
                else:
                    st.info("No materials found for the selected category/subject.")
            except Exception as e:
                st.error(f"Error fetching study resources: {e}")

        # ======================================
        # STUDENT TAB 2: PRACTICE QUIZZES
        # ======================================
        with student_tab2:
            st.subheader("📝 Practice Questions & MCQs")
            try:
                q_res = db.table("questions").select("*").execute()
                if q_res.data and len(q_res.data) > 0:
                    for idx, q in enumerate(q_res.data, 1):
                        st.markdown(f"**Q{idx}:** {q.get('question_text', '')}")
                        st.caption(f"Subject: {q.get('subject', '')} | Topic: {q.get('topic', '')}")
                        st.markdown("---")
                else:
                    st.info("No practice questions available yet.")
            except Exception as e:
                st.error(f"Error loading practice questions: {e}")
