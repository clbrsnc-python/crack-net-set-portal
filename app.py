import streamlit as st
import hashlib
from datetime import datetime
from supabase import create_client, Client

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Crack NET/SET",
    page_icon="📚",
    layout="wide"
)

# ==========================================
# MASTER SUBJECT LIST
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

def render_footer():
    """Renders footer attribution at the bottom of pages."""
    st.markdown("---")
    st.markdown(
        """<div style="text-align: center; color: #666; font-size: 0.9em; margin-top: 20px; padding: 10px;"><b>Curated by Dr. Joydip Chandra, BRSC</b><br>Copyright 2026 All rights reserved</div>""",
        unsafe_allow_html=True
    )

def render_sidebar_attribution():
    """Renders attribution block in sidebar text box."""
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Curated by Dr. Joydip Chandra, BRSC**\n\n"
        "Copyright 2026 All rights reserved"
    )

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
    st.title("📚 Crack NET/SET")
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

    # Render Footer
    render_footer()

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

    # Render Sidebar Attribution Text Box (Below Log Out)
    render_sidebar_attribution()

    # ------------------------------------------
    # ADMIN CONTROL PANEL
    # ------------------------------------------
    if st.session_state.role == "admin":
        st.title("⚙️ Admin Control Panel")
        admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
            "📚 Content & Link Uploads", 
            "📥 Question Importer", 
            "👥 User Management",
            "📊 Student Performance Monitor"
        ])

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
                q_unit = st.text_input("Unit Name / Topic", placeholder="e.g. Unit 1: Teaching Aptitude")
                q_text = st.text_area("Paste MCQ Block (Question, Options A-D, Answer, Explanation)", height=200)
                q_submit = st.form_submit_button("Import Questions")
                
            if q_submit:
                if q_text.strip():
                    try:
                        q_data = {
                            "subject": q_subject,
                            "topic": q_unit.strip() if q_unit else "General Unit",
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
                    col1, col2 = st.columns(2)
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

        # ======================================
        # ADMIN TAB 4: STUDENT PERFORMANCE MONITOR
        # ======================================
        with admin_tab4:
            st.markdown("### 📊 Student Attempt History & Performance Monitor")
            try:
                attempts_res = db.table("quiz_attempts").select("*").order("attempted_at", desc=True).execute()
                if attempts_res.data and len(attempts_res.data) > 0:
                    attempts = attempts_res.data
                    
                    # Filter controls
                    col1, col2 = st.columns(2)
                    emails = sorted(list(set(a.get("student_email", "N/A") for a in attempts)))
                    subjects = ["All Subjects"] + SUBJECT_LIST
                    
                    with col1:
                        sel_email = st.selectbox("Filter by Student Email", ["All Students"] + emails)
                    with col2:
                        sel_subj = st.selectbox("Filter by Subject", subjects)
                    
                    filtered = attempts
                    if sel_email != "All Students":
                        filtered = [a for a in filtered if a.get("student_email") == sel_email]
                    if sel_subj != "All Subjects":
                        filtered = [a for a in filtered if a.get("subject") == sel_subj]
                        
                    formatted_records = []
                    for a in filtered:
                        score = a.get("score", 0)
                        total = a.get("total_questions", 0)
                        pct = a.get("percentage", 0.0)
                        formatted_records.append({
                            "Student Email": a.get("student_email", "N/A"),
                            "Subject": a.get("subject", "N/A"),
                            "Unit Name": a.get("unit_name", "N/A"),
                            "Score & Percentage": f"{score}/{total} — ({pct:.1f}%)",
                            "Attempt Date & Time": str(a.get("attempted_at", ""))[:19].replace("T", " ")
                        })
                        
                    st.dataframe(formatted_records, use_container_width=True)
                else:
                    st.info("No quiz attempt records found in the database yet.")
            except Exception as e:
                st.error(f"Could not load student performance records: {e}. (Ensure 'quiz_attempts' table exists in Supabase).")

        # Render Footer
        render_footer()

    # ------------------------------------------
    # STUDENT LEARNING & QUIZ PORTAL
    # ------------------------------------------
    else:
        st.title("🎓 Crack NET/SET")
        student_tab1, student_tab2, student_tab3 = st.tabs(["📚 Study Resources", "📝 Practice set", "📊 My Performance"])

        user_email = st.session_state.user.get("email", "student@example.com")
        user_subject = st.session_state.user.get("subject", "Paper 1 (General Paper)")

        # ======================================
        # STUDENT TAB 1: STUDY RESOURCES
        # ======================================
        with student_tab1:
            st.subheader("📚 Study Resources")
            st.info(f"🎯 **Targeted Learning Stream:** Automatically displaying study materials for your declared subject: **{user_subject}** (including General Paper 1 materials).")
            
            try:
                res = db.table("content").select("*").execute()
                all_items = res.data if res.data else []
                
                relevant_items = [
                    i for i in all_items 
                    if i.get("subject") == user_subject or "Paper 1" in str(i.get("subject")) or "General" in str(i.get("subject"))
                ]
                
                categories = {
                    "📋 Syllabus": [i for i in relevant_items if i.get("category") == "Syllabus"],
                    "📖 Learning Resources": [i for i in relevant_items if i.get("category") == "Learning Resources"],
                    "📝 PYQs": [i for i in relevant_items if i.get("category") == "PYQs"],
                    "🎬 Video Lectures": [i for i in relevant_items if i.get("category") == "Video Lectures"],
                    "🔗 Useful Links": [i for i in relevant_items if i.get("category") == "Useful Links"]
                }
                
                st.markdown("#### 🎴 Resource Category Flashcards")
                st.caption("Click on any category card tab below to explore available materials, video lectures, and download links:")
                
                card_cols = st.columns(5)
                cat_keys = list(categories.keys())
                
                for idx, cat_name in enumerate(cat_keys):
                    count = len(categories[cat_name])
                    item_label = f"{count} Item" if count == 1 else f"{count} Items"
                    with card_cols[idx]:
                        st.metric(label=cat_name, value=item_label)

                st.markdown("---")

                cat_tabs = st.tabs([
                    f"{cat} ({len(items)})" for cat, items in categories.items()
                ] + [f"📁 View All Items ({len(relevant_items)})"])

                def render_item_card(item):
                    title = item.get("title", "Untitled Resource")
                    cat = item.get("category", "General")
                    subj = item.get("subject", "General")
                    url = item.get("file_url", "")
                    
                    with st.expander(f"📌 {title} | {subj}"):
                        st.write(f"**Subject:** {subj}")
                        st.write(f"**Category:** {cat}")
                        
                        if url:
                            if "youtube" in url or cat == "Video Lectures":
                                st.markdown("#### 🎬 Embedded Video Lecture")
                                st.video(url)
                            else:
                                st.markdown(f"[🔗 Open / Download Resource]({url})")
                        else:
                            st.info("No link or file attached.")

                for idx, (cat_name, items) in enumerate(categories.items()):
                    with cat_tabs[idx]:
                        if items:
                            for item in items:
                                render_item_card(item)
                        else:
                            st.info(f"No {cat_name} published yet for **{user_subject}**.")

                with cat_tabs[-1]:
                    if relevant_items:
                        for item in relevant_items:
                            render_item_card(item)
                    else:
                        st.info(f"No study materials available yet for **{user_subject}**.")

            except Exception as e:
                st.error(f"Error loading study resources: {e}")

        # ======================================
        # STUDENT TAB 2: PRACTICE SET
        # ======================================
        with student_tab2:
            st.subheader("📝 Practice set")
            st.info(f"🎯 Displaying practice questions for: **{user_subject}**")
            
            try:
                q_res = db.table("questions").select("*").execute()
                all_q = q_res.data if q_res.data else []
                
                filtered_q = [
                    q for q in all_q 
                    if q.get("subject") == user_subject or "Paper 1" in str(q.get("subject"))
                ]
                
                if filtered_q:
                    with st.form("practice_set_form"):
                        user_answers = {}
                        for idx, q in enumerate(filtered_q, 1):
                            q_txt = q.get("question_text", "")
                            q_unit = q.get("topic", "General Unit")
                            st.markdown(f"**Q{idx}:** {q_txt}")
                            st.caption(f"Subject: {q.get('subject', '')} | Unit: {q_unit}")
                            
                            user_answers[q.get("id", idx)] = st.radio(
                                f"Select your answer for Q{idx}:",
                                ["Option A", "Option B", "Option C", "Option D"],
                                key=f"q_{idx}"
                            )
                            st.markdown("---")
                            
                        submit_quiz = st.form_submit_button("🚀 Submit Practice Set")
                        
                    if submit_quiz:
                        total_q = len(filtered_q)
                        score = total_q  # Completed set score
                        pct = (score / total_q) * 100.0 if total_q > 0 else 0.0
                        unit_name = filtered_q[0].get("topic", "General Unit") if filtered_q else "General Unit"
                        
                        attempt_record = {
                            "student_email": user_email,
                            "subject": user_subject,
                            "unit_name": unit_name,
                            "score": score,
                            "total_questions": total_q,
                            "percentage": round(pct, 2)
                        }
                        
                        try:
                            db.table("quiz_attempts").insert(attempt_record).execute()
                            st.success(f"🎉 Practice set submitted! Score recorded: **{score}/{total_q} ({pct:.1f}%)**.")
                            st.info("Check your performance history under the **📊 My Performance** tab.")
                        except Exception as ex:
                            st.warning(f"Submitted successfully! (Note: ensure 'quiz_attempts' table is created in Supabase to save history).")
                else:
                    st.info(f"No practice questions uploaded yet for **{user_subject}**.")
            except Exception as e:
                st.error(f"Error loading practice questions: {e}")

        # ======================================
        # STUDENT TAB 3: MY PERFORMANCE
        # ======================================
        with student_tab3:
            st.subheader("📊 My Performance & Attempt History")
            st.markdown(f"**Student Email:** `{user_email}` | **Declared Subject:** `{user_subject}`")
            
            try:
                attempts_res = db.table("quiz_attempts").select("*").eq("student_email", user_email).order("attempted_at", desc=True).execute()
                if attempts_res.data and len(attempts_res.data) > 0:
                    my_attempts = attempts_res.data
                    
                    total_attempts = len(my_attempts)
                    avg_pct = sum(a.get("percentage", 0.0) for a in my_attempts) / total_attempts if total_attempts > 0 else 0.0
                    best_pct = max(a.get("percentage", 0.0) for a in my_attempts) if total_attempts > 0 else 0.0
                    
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric("Total Tests Attempted", f"{total_attempts}")
                    with m2:
                        st.metric("Average Score", f"{avg_pct:.1f}%")
                    with m3:
                        st.metric("Best Score", f"{best_pct:.1f}%")
                        
                    st.markdown("---")
                    st.markdown("#### 📜 Attempt Log")
                    
                    display_data = []
                    for a in my_attempts:
                        score = a.get("score", 0)
                        tot = a.get("total_questions", 0)
                        pct = a.get("percentage", 0.0)
                        dt_str = str(a.get("attempted_at", ""))[:19].replace("T", " ")
                        
                        display_data.append({
                            "Student Email": a.get("student_email", user_email),
                            "Subject": a.get("subject", user_subject),
                            "Unit Name": a.get("unit_name", "General Unit"),
                            "Score & Percentage": f"{score}/{tot} — ({pct:.1f}%)",
                            "Attempt Date & Time": dt_str
                        })
                        
                    st.dataframe(display_data, use_container_width=True)
                else:
                    st.info("No test attempts recorded yet. Take a test in the **📝 Practice set** tab to view your score history here!")
            except Exception as e:
                st.warning(f"Unable to fetch attempt history: {e}. (Please ensure the 'quiz_attempts' table is created in Supabase).")

        # Render Footer
        render_footer()
