import streamlit as st
import hashlib
import time
import random
import csv
import io
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

UNIT_LIST = [f"Unit {i}" for i in range(1, 11)]

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
    """Renders mandatory copyright & attribution footer across all pages."""
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 10px; font-size: 0.9em;'>"
        "<strong>Curated by Dr. Joydip Chandra, BRSC</strong><br>"
        "Copyright 2026 All rights reserved"
        "</div>",
        unsafe_allow_html=True
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

# Practice Test Engine Session States
if "test_active" not in st.session_state:
    st.session_state.test_active = False
if "test_questions" not in st.session_state:
    st.session_state.test_questions = []
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "current_q_idx" not in st.session_state:
    st.session_state.current_q_idx = 0
if "start_time" not in st.session_state:
    st.session_state.start_time = 0
if "time_limit" not in st.session_state:
    st.session_state.time_limit = 0
if "test_module" not in st.session_state:
    st.session_state.test_module = ""
if "test_completed" not in st.session_state:
    st.session_state.test_completed = False
if "last_score" not in st.session_state:
    st.session_state.last_score = {}

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

    render_footer()

# ==========================================
# MAIN APPLICATION LOGIC
# ==========================================
if not st.session_state.logged_in:
    render_auth_page()
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
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Curated by Dr. Joydip Chandra, BRSC**\n\n"
        "Copyright 2026 All rights reserved"
    )

    # ------------------------------------------
    # ADMIN CONTROL PANEL
    # ------------------------------------------
    if st.session_state.role == "admin":
        st.title("⚙️ Admin Control Panel")
        admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
            "📚 Content Uploads", 
            "📥 Question Importer", 
            "👥 User Management",
            "📊 Student Performance Monitor"
        ])

        # ======================================
        # ADMIN TAB 1: CONTENT & LINK UPLOADS
        # ======================================
        with admin_tab1:
            st.markdown("### 📚 Upload Resources, Notes & External Links")
            
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
            import_mode = st.radio("Select Import Mode", ["Single Question Entry", "Bulk CSV / Text Importer"], horizontal=True)
            
            if import_mode == "Single Question Entry":
                with st.form("single_q_form", clear_on_submit=True):
                    sq_subject = st.selectbox("Subject", SUBJECT_LIST)
                    sq_unit = st.selectbox("Unit / Topic", UNIT_LIST)
                    sq_text = st.text_area("Question Text", placeholder="Enter full question text...")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        opt_a = st.text_input("Option A")
                        opt_b = st.text_input("Option B")
                    with col_b:
                        opt_c = st.text_input("Option C")
                        opt_d = st.text_input("Option D")
                    
                    correct_opt = st.selectbox("Correct Option Key", ["A", "B", "C", "D"])
                    explanation_txt = st.text_area("Explanation / Solution Notes (Optional)", placeholder="Optional solution breakdown...")
                    sq_submit = st.form_submit_button("➕ Add Question to Database")
                    
                if sq_submit:
                    if not sq_text.strip() or not opt_a.strip() or not opt_b.strip():
                        st.warning("Please provide question text and at least Options A and B.")
                    else:
                        try:
                            q_row = {
                                "subject": sq_subject,
                                "unit": sq_unit,
                                "question_text": sq_text.strip(),
                                "option_a": opt_a.strip(),
                                "option_b": opt_b.strip(),
                                "option_c": opt_c.strip(),
                                "option_d": opt_d.strip(),
                                "correct_option": correct_opt,
                                "explanation": explanation_txt.strip() if explanation_txt else ""
                            }
                            db.table("questions").insert(q_row).execute()
                            st.success("✅ Question added successfully to database!")
                        except Exception as e:
                            st.error(f"Failed to add question: {e}")
                            
            else:
                st.info("Paste CSV text below with columns: `subject,unit,question_text,option_a,option_b,option_c,option_d,correct_option,explanation`")
                with st.form("bulk_q_form", clear_on_submit=True):
                    default_subject = st.selectbox("Default Subject (if not in CSV)", SUBJECT_LIST)
                    default_unit = st.selectbox("Default Unit (if not in CSV)", UNIT_LIST)
                    bulk_csv = st.text_area("Paste CSV Data Block", height=220)
                    bulk_submit = st.form_submit_button("🚀 Import Bulk Questions")
                    
                if bulk_submit:
                    if bulk_csv.strip():
                        try:
                            f = io.StringIO(bulk_csv.strip())
                            reader = csv.DictReader(f)
                            records = []
                            for row in reader:
                                r_lower = {k.strip().lower(): v for k, v in row.items() if k}
                                
                                q_txt = r_lower.get("question_text") or r_lower.get("question") or r_lower.get("q_text") or ""
                                op_a = r_lower.get("option_a") or r_lower.get("option a") or r_lower.get("a") or ""
                                op_b = r_lower.get("option_b") or r_lower.get("option b") or r_lower.get("b") or ""
                                op_c = r_lower.get("option_c") or r_lower.get("option c") or r_lower.get("c") or ""
                                op_d = r_lower.get("option_d") or r_lower.get("option d") or r_lower.get("d") or ""
                                
                                key_raw = r_lower.get("correct_option") or r_lower.get("correct answer") or r_lower.get("answer") or "A"
                                key_clean = str(key_raw).strip().upper()
                                if "A" in key_clean: key_clean = "A"
                                elif "B" in key_clean: key_clean = "B"
                                elif "C" in key_clean: key_clean = "C"
                                elif "D" in key_clean: key_clean = "D"
                                else: key_clean = "A"
                                
                                subj = r_lower.get("subject") or default_subject
                                u_val = r_lower.get("unit") or r_lower.get("topic") or default_unit
                                exp_val = r_lower.get("explanation") or r_lower.get("solution") or ""
                                
                                if q_txt:
                                    records.append({
                                        "subject": subj,
                                        "unit": u_val,
                                        "question_text": q_txt,
                                        "option_a": op_a,
                                        "option_b": op_b,
                                        "option_c": op_c,
                                        "option_d": op_d,
                                        "correct_option": key_clean,
                                        "explanation": exp_val
                                    })
                            
                            if records:
                                db.table("questions").insert(records).execute()
                                st.success(f"✅ Successfully imported {len(records)} questions into database!")
                            else:
                                st.warning("No valid questions parsed from the pasted CSV.")
                        except Exception as e:
                            st.error(f"Failed to process CSV block: {e}")
                    else:
                        st.warning("Please paste CSV data.")

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
            st.markdown("### 📊 Student Performance & Test Attempt Monitor")
            try:
                attempts_res = db.table("quiz_attempts").select("*").order("attempted_at", desc=True).execute()
                attempts_data = attempts_res.data if attempts_res.data else []
                if attempts_data:
                    st.dataframe(attempts_data, use_container_width=True)
                else:
                    st.info("No test attempts recorded in database yet.")
            except Exception as e:
                st.error(f"Error fetching test attempt records: {e}")

        render_footer()

    # ------------------------------------------
    # STUDENT LEARNING & QUIZ PORTAL
    # ------------------------------------------
    else:
        st.title("🎓 Crack NET/SET")
        student_tab1, student_tab2, student_tab3 = st.tabs(["📚 Study Resources", "📝 Practice set", "📊 My Performance"])

        # ======================================
        # STUDENT TAB 1: STUDY RESOURCES
        # ======================================
        with student_tab1:
            st.subheader("📚 Study Resources")
            user_subject = st.session_state.user.get("subject", "Paper 1 (General Paper)")
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
            user_subject = st.session_state.user.get("subject", "Paper 1 (General Paper)")
            
            if not st.session_state.test_active and not st.session_state.test_completed:
                st.info(f"🎯 **Targeted Practice:** Select a Unit Test or Full Paper Mock Test for **{user_subject}**.")
                
                module_options = UNIT_LIST + ["Full Paper (100 Questions - 120 Mins)"]
                selected_mod = st.selectbox("Select Test Module", module_options)
                
                if "Full Paper" in selected_mod:
                    st.write("📋 **Test Rules:** 100 Questions (10 Questions drawn from each of the 10 Units). Time limit: **120 Minutes**. 2 Marks per question (Total: 200 Marks). No negative marking.")
                else:
                    st.write(f"📋 **Test Rules:** 25 Questions for **{selected_mod}**. Time limit: **30 Minutes**. 2 Marks per question (Total: 50 Marks). No negative marking.")
                
                if st.button("🚀 Start Practice Test", use_container_width=True):
                    with st.spinner("Preparing question paper..."):
                        try:
                            q_res = db.table("questions").select("*").execute()
                            all_qs = q_res.data if q_res.data else []
                            subj_qs = [
                                q for q in all_qs 
                                if q.get("subject") == user_subject or "Paper 1" in str(q.get("subject"))
                            ]
                            
                            selected_qs = []
                            if "Full Paper" in selected_mod:
                                for u_name in UNIT_LIST:
                                    u_pool = [q for q in subj_qs if q.get("unit") == u_name or q.get("topic") == u_name]
                                    if len(u_pool) >= 10:
                                        selected_qs.extend(random.sample(u_pool, 10))
                                    else:
                                        selected_qs.extend(u_pool)
                                random.shuffle(selected_qs)
                                st.session_state.time_limit = 120 * 60
                            else:
                                u_pool = [q for q in subj_qs if q.get("unit") == selected_mod or q.get("topic") == selected_mod]
                                if u_pool:
                                    selected_qs = random.sample(u_pool, min(25, len(u_pool)))
                                st.session_state.time_limit = 30 * 60
                            
                            if selected_qs:
                                st.session_state.test_questions = selected_qs
                                st.session_state.start_time = time.time()
                                st.session_state.user_answers = {}
                                st.session_state.current_q_idx = 0
                                st.session_state.test_module = selected_mod
                                st.session_state.test_active = True
                                st.rerun()
                            else:
                                st.warning(f"No questions available in database for **{selected_mod}**.")
                        except Exception as e:
                            st.error(f"Error initializing test: {e}")

            elif st.session_state.test_active:
                elapsed = time.time() - st.session_state.start_time
                remaining = max(0, int(st.session_state.time_limit - elapsed))
                
                mins, secs = divmod(remaining, 60)
                hrs, mins = divmod(mins, 60)
                time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                
                header_col, timer_col = st.columns([3, 1])
                with header_col:
                    st.markdown(f"### 📝 {st.session_state.test_module}")
                with timer_col:
                    st.metric("⏳ Time Remaining", time_str)
                
                if remaining <= 0:
                    st.warning("⏱️ Time is up! Auto-submitting your test...")
                    total_q = len(st.session_state.test_questions)
                    correct_cnt = 0
                    for idx, q in enumerate(st.session_state.test_questions):
                        if st.session_state.user_answers.get(idx) == q.get("correct_option"):
                            correct_cnt += 1
                    score_val = correct_cnt * 2
                    max_score = total_q * 2
                    pct = (score_val / max_score * 100) if max_score > 0 else 0.0
                    
                    try:
                        db.table("quiz_attempts").insert({
                            "student_email": st.session_state.user.get("email"),
                            "subject": user_subject,
                            "unit_name": st.session_state.test_module,
                            "score": f"{score_val}/{max_score}",
                            "total_questions": total_q,
                            "percentage": round(pct, 2)
                        }).execute()
                    except Exception as e:
                        pass
                        
                    st.session_state.last_score = {
                        "score": score_val,
                        "max_score": max_score,
                        "pct": pct,
                        "correct_cnt": correct_cnt,
                        "total_q": total_q
                    }
                    st.session_state.test_active = False
                    st.session_state.test_completed = True
                    st.rerun()
                
                total_qs = len(st.session_state.test_questions)
                curr_idx = st.session_state.current_q_idx
                q_data = st.session_state.test_questions[curr_idx]
                
                st.markdown("---")
                if "Full Paper" in st.session_state.test_module:
                    st.markdown(f"#### Question {curr_idx + 1} of {total_qs}")
                else:
                    unit_label = q_data.get("unit") or q_data.get("topic") or st.session_state.test_module
                    st.markdown(f"#### Question {curr_idx + 1} of {total_qs} (`{unit_label}`)")
                
                st.write(f"**{q_data.get('question_text')}**")
                
                opts = {
                    "A": q_data.get("option_a", ""),
                    "B": q_data.get("option_b", ""),
                    "C": q_data.get("option_c", ""),
                    "D": q_data.get("option_d", "")
                }
                
                curr_ans = st.session_state.user_answers.get(curr_idx, None)
                sel_opt = st.radio(
                    "Select Answer:",
                    options=["A", "B", "C", "D"],
                    format_func=lambda k: f"{k}) {opts[k]}",
                    index=["A", "B", "C", "D"].index(curr_ans) if curr_ans in ["A", "B", "C", "D"] else 0,
                    key=f"q_radio_{curr_idx}"
                )
                
                st.session_state.user_answers[curr_idx] = sel_opt
                
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    if st.button("⬅️ Previous", disabled=(curr_idx == 0)):
                        st.session_state.current_q_idx -= 1
                        st.rerun()
                with c2:
                    if st.button("⏭️ Skip"):
                        if curr_idx < total_qs - 1:
                            st.session_state.current_q_idx += 1
                            st.rerun()
                with c3:
                    if st.button("💾 Save & Next", disabled=(curr_idx == total_qs - 1)):
                        st.session_state.current_q_idx += 1
                        st.rerun()
                with c4:
                    if st.button("🏁 Submit Test", type="primary"):
                        total_q = len(st.session_state.test_questions)
                        correct_cnt = 0
                        for idx, q in enumerate(st.session_state.test_questions):
                            if st.session_state.user_answers.get(idx) == q.get("correct_option"):
                                correct_cnt += 1
                        score_val = correct_cnt * 2
                        max_score = total_q * 2
                        pct = (score_val / max_score * 100) if max_score > 0 else 0.0
                        
                        try:
                            db.table("quiz_attempts").insert({
                                "student_email": st.session_state.user.get("email"),
                                "subject": user_subject,
                                "unit_name": st.session_state.test_module,
                                "score": f"{score_val}/{max_score}",
                                "total_questions": total_q,
                                "percentage": round(pct, 2)
                            }).execute()
                        except Exception as e:
                            st.error(f"Error logging result: {e}")
                            
                        st.session_state.last_score = {
                            "score": score_val,
                            "max_score": max_score,
                            "pct": pct,
                            "correct_cnt": correct_cnt,
                            "total_q": total_q
                        }
                        st.session_state.test_active = False
                        st.session_state.test_completed = True
                        st.rerun()

                st.markdown("---")
                st.markdown("##### 🧭 Question Palette Navigation")
                p_cols = st.columns(10)
                for i in range(total_qs):
                    is_ans = i in st.session_state.user_answers
                    is_curr = i == curr_idx
                    lbl = f"🔵{i+1}" if is_curr else (f"🟢{i+1}" if is_ans else f"⚪{i+1}")
                    with p_cols[i % 10]:
                        if st.button(lbl, key=f"p_btn_{i}"):
                            st.session_state.current_q_idx = i
                            st.rerun()

            elif st.session_state.test_completed:
                res = st.session_state.last_score
                st.success("🎉 Test Submitted Successfully!")
                
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Total Score", f"{res.get('score')}/{res.get('max_score')}")
                with m2:
                    st.metric("Percentage", f"{res.get('pct'):.2f}%")
                with m3:
                    st.metric("Correct Answers", f"{res.get('correct_cnt')}/{res.get('total_q')}")
                
                st.markdown("---")
                st.subheader("📖 Detailed Question Review & Answer Keys")
                
                for idx, q in enumerate(st.session_state.test_questions, 1):
                    user_ans = st.session_state.user_answers.get(idx - 1, "Unattempted")
                    correct_key = q.get("correct_option")
                    is_correct = user_ans == correct_key
                    
                    status_icon = "✅ Correct" if is_correct else ("❌ Incorrect" if user_ans != "Unattempted" else "⚪ Unattempted")
                    with st.expander(f"Q{idx}: {q.get('question_text')} [{status_icon}]"):
                        st.write(f"**A:** {q.get('option_a')}")
                        st.write(f"**B:** {q.get('option_b')}")
                        st.write(f"**C:** {q.get('option_c')}")
                        st.write(f"**D:** {q.get('option_d')}")
                        st.write(f"**Your Answer:** {user_ans}")
                        st.write(f"**Correct Key:** {correct_key}")
                        exp = q.get("explanation")
                        if exp and str(exp).strip():
                            st.info(f"💡 **Explanation / Notes:** {exp}")

                if st.button("🔄 Take Another Practice Test", type="primary"):
                    st.session_state.test_completed = False
                    st.session_state.test_questions = []
                    st.session_state.user_answers = {}
                    st.rerun()

        # ======================================
        # STUDENT TAB 3: MY PERFORMANCE
        # ======================================
        with student_tab3:
            st.subheader("📊 My Performance & Attempt History")
            student_email = st.session_state.user.get("email")
            
            try:
                att_res = db.table("quiz_attempts").select("*").eq("student_email", student_email).order("attempted_at", desc=True).execute()
                attempts = att_res.data if att_res.data else []
                
                if attempts:
                    total_tests = len(attempts)
                    avg_pct = sum(float(a.get("percentage", 0)) for a in attempts) / total_tests
                    best_pct = max(float(a.get("percentage", 0)) for a in attempts)
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Total Tests Attempted", total_tests)
                    with c2:
                        st.metric("Average Score %", f"{avg_pct:.1f}%")
                    with c3:
                        st.metric("Best Score %", f"{best_pct:.1f}%")
                    
                    st.markdown("---")
                    st.dataframe(attempts, use_container_width=True)
                else:
                    st.info("You haven't attempted any practice tests yet. Go to the **Practice set** tab to take your first test!")
            except Exception as e:
                st.error(f"Error loading performance history: {e}")

        render_footer()
