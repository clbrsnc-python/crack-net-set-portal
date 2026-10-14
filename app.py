import streamlit as st
import hashlib
import random
import time
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

UNITS_LIST = [f"Unit {i}" for i in range(1, 11)]

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
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; padding: 10px; color: #666; font-size: 0.9em;'>"
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
if "exam_state" not in st.session_state:
    st.session_state.exam_state = None

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
    # Sidebar
    st.sidebar.title(f"👋 Welcome, {st.session_state.user.get('name', 'User')}")
    st.sidebar.write(f"**Role:** {st.session_state.role.upper()}")
    st.sidebar.write(f"**Subject:** {st.session_state.user.get('subject', 'N/A')}")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.role = None
        st.session_state.exam_state = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.info("**Curated by Dr. Joydip Chandra, BRSC**\n\nCopyright 2026 All rights reserved")

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
            st.info("Add questions individually or in bulk block format.")
            
            import_mode = st.radio(
                "Select Import Mode",
                ["📝 Single Question Entry", "📦 Bulk MCQ Block Entry"],
                horizontal=True
            )
            
            if "Single Question" in import_mode:
                with st.form("single_q_form", clear_on_submit=True):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        s_subject = st.selectbox("Subject", SUBJECT_LIST)
                    with col_b:
                        s_unit = st.selectbox("Unit / Topic", UNITS_LIST)
                        
                    s_question = st.text_area("Question Text", placeholder="Enter the full question prompt here...")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        opt_a = st.text_input("Option A")
                        opt_b = st.text_input("Option B")
                    with c2:
                        opt_c = st.text_input("Option C")
                        opt_d = st.text_input("Option D")
                        
                    col_ans, col_exp = st.columns([1, 2])
                    with col_ans:
                        correct_opt = st.selectbox("Correct Option", ["A", "B", "C", "D"])
                    with col_exp:
                        explanation_text = st.text_input("Explanation / Solution Notes (Optional)")
                        
                    add_single_btn = st.form_submit_button("➕ Add Question to Database")
                    
                if add_single_btn:
                    if not s_question.strip() or not opt_a.strip() or not opt_b.strip() or not opt_c.strip() or not opt_d.strip():
                        st.warning("Please fill in question text and all four options.")
                    else:
                        try:
                            q_data = {
                                "subject": s_subject,
                                "topic": s_unit,
                                "question_text": s_question.strip(),
                                "option_a": opt_a.strip(),
                                "option_b": opt_b.strip(),
                                "option_c": opt_c.strip(),
                                "option_d": opt_d.strip(),
                                "correct_option": correct_opt,
                                "explanation": explanation_text.strip()
                            }
                            db.table("questions").insert(q_data).execute()
                            st.success(f"✅ Successfully added Question to **{s_subject}** ({s_unit})!")
                        except Exception as e:
                            st.error(f"Failed to add question: {e}")

            else:
                with st.form("bulk_q_form", clear_on_submit=True):
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        b_subject = st.selectbox("Target Subject", SUBJECT_LIST)
                    with col_b2:
                        b_unit = st.selectbox("Target Unit", UNITS_LIST)
                        
                    st.caption("Paste question blocks. Format example:\nQuestion text...\n(A) Option 1\n(B) Option 2\n(C) Option 3\n(D) Option 4\nAnswer: A\nExplanation: Solution notes...")
                    b_text = st.text_area("Paste MCQ Block", height=250)
                    bulk_btn = st.form_submit_button("🚀 Import Questions")
                    
                if bulk_btn:
                    if b_text.strip():
                        try:
                            q_data = {
                                "subject": b_subject,
                                "topic": b_unit,
                                "question_text": b_text.strip()
                            }
                            db.table("questions").insert(q_data).execute()
                            st.success(f"✅ Imported question block under **{b_subject}** ({b_unit})!")
                        except Exception as e:
                            st.error(f"Failed to import questions: {e}")
                    else:
                        st.warning("Please paste question text.")

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
            st.markdown("### 📊 Student Test Performance & Attempts")
            try:
                attempts_res = db.table("quiz_attempts").select("*").order("attempted_at", desc=True).execute()
                if attempts_res.data:
                    st.dataframe(attempts_res.data, use_container_width=True)
                else:
                    st.info("No student test attempts recorded yet.")
            except Exception as e:
                st.info("Performance table (`quiz_attempts`) will display here once student attempts are recorded.")

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
            
            selected_module = st.selectbox(
                "Select Unit / Exam Module",
                UNITS_LIST + ["Full Paper (100 Questions)"]
            )
            
            if st.button("🚀 Start Practice Test"):
                try:
                    q_res = db.table("questions").select("*").execute()
                    all_q = q_res.data if q_res.data else []
                    
                    # Filter questions for student's subject or Paper 1
                    subj_q = [
                        q for q in all_q 
                        if q.get("subject") == user_subject or "Paper 1" in str(q.get("subject"))
                    ]
                    
                    selected_questions = []
                    duration_sec = 1800 # default 30 mins
                    
                    if "Full Paper" in selected_module:
                        duration_sec = 7200 # 120 mins
                        # 10 questions per unit
                        for u_name in UNITS_LIST:
                            unit_pool = [q for q in subj_q if q.get("topic") == u_name]
                            if len(unit_pool) >= 10:
                                selected_questions.extend(random.sample(unit_pool, 10))
                            else:
                                selected_questions.extend(unit_pool)
                        random.shuffle(selected_questions)
                    else:
                        duration_sec = 1800 # 30 mins for 25 questions
                        unit_pool = [q for q in subj_q if q.get("topic") == selected_module]
                        if len(unit_pool) >= 25:
                            selected_questions = random.sample(unit_pool, 25)
                        else:
                            selected_questions = unit_pool
                            
                    if selected_questions:
                        st.session_state.exam_state = {
                            "module": selected_module,
                            "questions": selected_questions,
                            "user_answers": {},
                            "start_time": time.time(),
                            "duration_sec": duration_sec,
                            "current_idx": 0,
                            "submitted": False
                        }
                        st.rerun()
                    else:
                        st.warning(f"No questions available in database for **{selected_module}** ({user_subject}).")
                except Exception as e:
                    st.error(f"Error starting test: {e}")

            # Active Test Session Interface
            if st.session_state.exam_state and not st.session_state.exam_state.get("submitted"):
                exam = st.session_state.exam_state
                q_list = exam["questions"]
                curr_idx = exam["current_idx"]
                total_q = len(q_list)
                
                # Countdown Timer
                elapsed = int(time.time() - exam["start_time"])
                remaining = exam["duration_sec"] - elapsed
                
                if remaining <= 0:
                    st.session_state.exam_state["submitted"] = True
                    st.rerun()
                    
                mins, secs = divmod(remaining, 60)
                hrs, mins = divmod(mins, 60)
                timer_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                
                # Header row with timer
                col_h1, col_h2 = st.columns([3, 1])
                with col_h1:
                    st.markdown(f"### ⏳ Test in Progress: {exam['module']}")
                with col_h2:
                    st.error(f"⏱️ **Time Left:** `{timer_str}`")
                    
                st.markdown("---")
                
                # Current Question Display
                q = q_list[curr_idx]
                is_full_paper = "Full Paper" in exam["module"]
                
                unit_label = "" if is_full_paper else f" [{q.get('topic', '')}]"
                st.markdown(f"#### Question {curr_idx + 1} of {total_q}{unit_label}")
                
                q_text_disp = q.get("question_text", "")
                st.write(q_text_disp)
                
                # Radio choices A, B, C, D
                opts = {
                    "A": q.get("option_a") or "Option A",
                    "B": q.get("option_b") or "Option B",
                    "C": q.get("option_c") or "Option C",
                    "D": q.get("option_d") or "Option D"
                }
                
                curr_ans = exam["user_answers"].get(curr_idx, None)
                opt_labels = [f"({k}) {v}" for k, v in opts.items()]
                
                selected_opt = st.radio(
                    "Choose your answer:",
                    opt_labels,
                    index=list(opts.keys()).index(curr_ans) if curr_ans in opts else None,
                    key=f"q_radio_{curr_idx}"
                )
                
                if selected_opt:
                    chosen_key = selected_opt[1] # Extracts 'A', 'B', 'C', 'D'
                    st.session_state.exam_state["user_answers"][curr_idx] = chosen_key

                st.markdown("---")
                
                # Navigation Controls
                nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
                with nav_col1:
                    if st.button("⬅️ Previous") and curr_idx > 0:
                        st.session_state.exam_state["current_idx"] -= 1
                        st.rerun()
                with nav_col2:
                    if st.button("💾 Submit Answer & Next") and curr_idx < total_q - 1:
                        st.session_state.exam_state["current_idx"] += 1
                        st.rerun()
                with nav_col3:
                    if st.button("⏭️ Skip Question") and curr_idx < total_q - 1:
                        st.session_state.exam_state["current_idx"] += 1
                        st.rerun()
                with nav_col4:
                    if st.button("🏁 Finish & Submit Test"):
                        st.session_state.exam_state["submitted"] = True
                        st.rerun()

            # Submitted Test Results View
            elif st.session_state.exam_state and st.session_state.exam_state.get("submitted"):
                exam = st.session_state.exam_state
                q_list = exam["questions"]
                user_ans = exam["user_answers"]
                total_q = len(q_list)
                
                correct_count = 0
                for idx, q in enumerate(q_list):
                    c_opt = q.get("correct_option", "").strip().upper()
                    u_opt = user_ans.get(idx, "").strip().upper()
                    if c_opt and u_opt == c_opt:
                        correct_count += 1
                        
                score_marks = correct_count * 2
                total_marks = total_q * 2
                pct = round((correct_count / total_q) * 100, 2) if total_q > 0 else 0
                
                st.success(f"🎉 **Test Completed! Score:** `{score_marks} / {total_marks}` Marks ({pct}%)")
                
                # Log score to Supabase quiz_attempts
                try:
                    attempt_payload = {
                        "student_email": st.session_state.user.get("email"),
                        "subject": user_subject,
                        "unit_name": exam["module"],
                        "score": score_marks,
                        "total_questions": total_marks,
                        "percentage": pct,
                        "attempted_at": datetime.utcnow().isoformat()
                    }
                    db.table("quiz_attempts").insert(attempt_payload).execute()
                except Exception:
                    pass

                if st.button("🔄 Take Another Practice Test"):
                    st.session_state.exam_state = None
                    st.rerun()

        # ======================================
        # STUDENT TAB 3: MY PERFORMANCE
        # ======================================
        with student_tab3:
            st.subheader("📊 My Performance & Score History")
            u_email = st.session_state.user.get("email")
            
            try:
                p_res = db.table("quiz_attempts").select("*").eq("student_email", u_email).order("attempted_at", desc=True).execute()
                attempts = p_res.data if p_res.data else []
                
                if attempts:
                    t_count = len(attempts)
                    avg_pct = round(sum(a.get("percentage", 0) for a in attempts) / t_count, 1)
                    best_pct = max(a.get("percentage", 0) for a in attempts)
                    
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric("Total Tests Attempted", f"{t_count}")
                    with m2:
                        st.metric("Average Score", f"{avg_pct}%")
                    with m3:
                        st.metric("Best Score", f"{best_pct}%")
                        
                    st.markdown("---")
                    st.markdown("#### 📜 Attempt History Log")
                    st.dataframe(attempts, use_container_width=True)
                else:
                    st.info("No practice test attempts recorded yet. Take a practice test to view your performance history!")
            except Exception as e:
                st.info("Your practice test results will be automatically logged here once you complete a test.")

    render_footer()
