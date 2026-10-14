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
# FOOTER / ATTRIBUTION HELPER
# ==========================================
FOOTER_HTML = '''
<div style="text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid #e6e6e6; color: #555555; font-size: 0.9em;">
    <strong>Curated by Dr. Joydip Chandra, BRSC</strong><br>
    Copyright 2026 All rights reserved
</div>
'''

def render_footer():
    st.markdown(FOOTER_HTML, unsafe_allow_html=True)

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

    # Sidebar Attribution Text Box
    st.sidebar.markdown("---")
    st.sidebar.info("**Curated by Dr. Joydip Chandra, BRSC**\n\nCopyright 2026 All rights reserved")

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
                q_unit = st.selectbox("Unit / Topic Name", [f"Unit {i}" for i in range(1, 11)] + ["General"])
                
                st.markdown("#### Single / Bulk MCQ Entry")
                q_text = st.text_area("Question Text", placeholder="Enter the question statement...")
                col_a, col_b = st.columns(2)
                with col_a:
                    opt_a = st.text_input("Option A")
                    opt_b = st.text_input("Option B")
                with col_b:
                    opt_c = st.text_input("Option C")
                    opt_d = st.text_input("Option D")
                    
                correct_opt = st.selectbox("Correct Option", ["A", "B", "C", "D"])
                q_explanation = st.text_area("Solution Notes / Explanation (Optional)", placeholder="Optional solution notes...")
                
                q_submit = st.form_submit_button("Import Question")
                
            if q_submit:
                if q_text.strip() and opt_a.strip() and opt_b.strip():
                    try:
                        q_data = {
                            "subject": q_subject,
                            "topic": q_unit,
                            "question_text": q_text.strip(),
                            "option_a": opt_a.strip(),
                            "option_b": opt_b.strip(),
                            "option_c": opt_c.strip(),
                            "option_d": opt_d.strip(),
                            "correct_option": correct_opt,
                            "explanation": q_explanation.strip() if q_explanation else ""
                        }
                        db.table("questions").insert(q_data).execute()
                        st.success(f"✅ Question imported successfully under **{q_subject} ({q_unit})**!")
                    except Exception as e:
                        st.error(f"Failed to import question: {e}")
                else:
                    st.warning("Please enter question text and options.")

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
            st.markdown("### 📊 Student Performance Monitor")
            st.caption("View and analyze test scores and attempt histories across all registered students.")
            try:
                attempts_res = db.table("quiz_attempts").select("*").order("attempted_at", desc=True).execute()
                if attempts_res.data:
                    st.dataframe(attempts_res.data, use_container_width=True)
                else:
                    st.info("No test attempts logged yet.")
            except Exception as e:
                st.error(f"Could not load attempt histories: {e}")

        render_footer()

    # ------------------------------------------
    # STUDENT LEARNING & QUIZ PORTAL
    # ------------------------------------------
    else:
        st.title("🎓 Crack NET/SET")
        student_tab1, student_tab2, student_tab3 = st.tabs([
            "📚 Study Resources", 
            "📝 Practice set", 
            "📊 My Performance"
        ])

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
        # STUDENT TAB 2: PRACTICE SET (TIMED EXAM ENGINE)
        # ======================================
        with student_tab2:
            st.subheader("📝 Practice set")
            user_subject = st.session_state.user.get("subject", "Paper 1 (General Paper)")
            st.info(f"🎯 Target Subject: **{user_subject}**")

            test_module = st.selectbox(
                "Select Test Module / Unit",
                [f"Unit {i}" for i in range(1, 11)] + ["Full Paper"]
            )

            is_full_paper = (test_module == "Full Paper")
            question_count = 100 if is_full_paper else 25
            time_limit_mins = 120 if is_full_paper else 30

            st.caption(f"⏱️ **Time Limit:** {time_limit_mins} Minutes | ❓ **Questions:** {question_count} | 🎯 **Marks:** {question_count * 2} Marks (2 Marks each, No Negative Marking)")

            if "quiz_active" not in st.session_state:
                st.session_state.quiz_active = False

            if not st.session_state.quiz_active:
                if st.button(f"🚀 Start {test_module} Test ({question_count} Questions)", type="primary"):
                    try:
                        q_res = db.table("questions").select("*").eq("subject", user_subject).execute()
                        all_q = q_res.data if q_res.data else []
                        
                        selected_questions = []
                        if is_full_paper:
                            for unit_num in range(1, 11):
                                unit_tag = f"Unit {unit_num}"
                                unit_qs = [q for q in all_q if q.get("topic") == unit_tag]
                                if len(unit_qs) >= 10:
                                    selected_questions.extend(random.sample(unit_qs, 10))
                                else:
                                    selected_questions.extend(unit_qs)
                            random.shuffle(selected_questions)
                        else:
                            unit_qs = [q for q in all_q if q.get("topic") == test_module]
                            if len(unit_qs) >= 25:
                                selected_questions = random.sample(unit_qs, 25)
                            else:
                                selected_questions = unit_qs
                                
                        if len(selected_questions) == 0:
                            st.warning(f"No practice questions found for **{test_module}** under **{user_subject}**. Please contact your admin.")
                        else:
                            st.session_state.quiz_active = True
                            st.session_state.quiz_questions = selected_questions
                            st.session_state.quiz_module = test_module
                            st.session_state.quiz_user_answers = {}
                            st.session_state.quiz_start_time = time.time()
                            st.session_state.quiz_time_limit_sec = time_limit_mins * 60
                            st.session_state.quiz_current_idx = 0
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error starting test: {e}")
            else:
                questions = st.session_state.quiz_questions
                total_q = len(questions)
                curr_idx = st.session_state.quiz_current_idx
                curr_q = questions[curr_idx]

                elapsed = time.time() - st.session_state.quiz_start_time
                remaining_sec = max(0, int(st.session_state.quiz_time_limit_sec - elapsed))
                
                mins_left, secs_left = divmod(remaining_sec, 60)
                hrs_left, mins_left = divmod(mins_left, 60)
                time_str = f"{hrs_left:02d}:{mins_left:02d}:{secs_left:02d}"

                col_head1, col_head2 = st.columns([3, 1])
                with col_head1:
                    st.markdown(f"### Question {curr_idx + 1} of {total_q}")
                with col_head2:
                    st.metric("⏳ Time Remaining", time_str)

                if remaining_sec <= 0:
                    st.error("⏰ Time's Up! Auto-submitting your test...")
                    st.session_state.quiz_submitted = True

                q_text = curr_q.get("question_text", "")
                st.markdown(f"#### {q_text}")

                opts = [
                    ("A", curr_q.get("option_a", "")),
                    ("B", curr_q.get("option_b", "")),
                    ("C", curr_q.get("option_c", "")),
                    ("D", curr_q.get("option_d", ""))
                ]
                opts = [o for o in opts if o[1]]

                selected_ans = st.radio(
                    "Choose Option:",
                    options=[f"{letter}: {text}" for letter, text in opts],
                    key=f"q_radio_{curr_idx}",
                    index=None
                )

                if selected_ans:
                    user_letter = selected_ans.split(":")[0]
                    st.session_state.quiz_user_answers[curr_idx] = user_letter

                nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
                with nav_col1:
                    if curr_idx > 0:
                        if st.button("⬅️ Previous Question"):
                            st.session_state.quiz_current_idx -= 1
                            st.rerun()
                with nav_col2:
                    if curr_idx < total_q - 1:
                        if st.button("💾 Next Question"):
                            st.session_state.quiz_current_idx += 1
                            st.rerun()
                with nav_col3:
                    if curr_idx < total_q - 1:
                        if st.button("⏭️ Skip Question"):
                            st.session_state.quiz_current_idx += 1
                            st.rerun()
                with nav_col4:
                    if st.button("🏁 Submit Test Early", type="primary"):
                        st.session_state.quiz_finish_confirmed = True

                if st.session_state.get("quiz_finish_confirmed"):
                    st.warning("Are you sure you want to complete and submit your test now?")
                    conf_col1, conf_col2 = st.columns(2)
                    with conf_col1:
                        if st.button("YES, Submit Test"):
                            score = 0
                            for idx, q in enumerate(questions):
                                u_ans = st.session_state.quiz_user_answers.get(idx, "")
                                if u_ans and u_ans == q.get("correct_option"):
                                    score += 2

                            total_possible = total_q * 2
                            pct = round((score / total_possible) * 100, 2) if total_possible > 0 else 0

                            try:
                                attempt_data = {
                                    "student_email": st.session_state.user.get("email"),
                                    "subject": user_subject,
                                    "unit_name": st.session_state.quiz_module,
                                    "score": score,
                                    "total_questions": total_q,
                                    "percentage": pct,
                                    "attempted_at": datetime.utcnow().isoformat()
                                }
                                db.table("quiz_attempts").insert(attempt_data).execute()
                            except Exception as e:
                                st.error(f"Failed to log score: {e}")

                            st.session_state.quiz_score = score
                            st.session_state.quiz_pct = pct
                            st.session_state.quiz_completed = True
                            st.session_state.quiz_active = False
                            st.rerun()
                    with conf_col2:
                        if st.button("NO, Continue Test"):
                            st.session_state.quiz_finish_confirmed = False
                            st.rerun()

            if st.session_state.get("quiz_completed"):
                st.balloons()
                st.success(f"🎉 **Test Complete!** You scored **{st.session_state.quiz_score}** out of **{len(st.session_state.quiz_questions) * 2}** Marks ({st.session_state.quiz_pct}%).")
                if st.button("🔄 Take Another Test"):
                    st.session_state.quiz_completed = False
                    st.rerun()

        # ======================================
        # STUDENT TAB 3: MY PERFORMANCE
        # ======================================
        with student_tab3:
            st.subheader("📊 My Performance & Test History")
            student_email = st.session_state.user.get("email")
            st.info(f"Log of test attempts for **{student_email}**")

            try:
                hist_res = db.table("quiz_attempts").select("*").eq("student_email", student_email).order("attempted_at", desc=True).execute()
                attempts = hist_res.data if hist_res.data else []

                if attempts:
                    tot_attempts = len(attempts)
                    avg_score = round(sum(a.get("percentage", 0) for a in attempts) / tot_attempts, 2)
                    best_score = max(a.get("percentage", 0) for a in attempts)

                    m_col1, m_col2, m_col3 = st.columns(3)
                    with m_col1:
                        st.metric("Total Tests Attempted", tot_attempts)
                    with m_col2:
                        st.metric("Average Score %", f"{avg_score}%")
                    with m_col3:
                        st.metric("Best Score %", f"{best_score}%")

                    st.markdown("---")
                    st.markdown("#### 📜 Attempt Log")
                    for a in attempts:
                        s_unit = a.get("unit_name", "General")
                        s_subj = a.get("subject", "")
                        s_score = a.get("score", 0)
                        s_tot = a.get("total_questions", 0) * 2
                        s_pct = a.get("percentage", 0)
                        s_date = a.get("attempted_at", "")[:19].replace("T", " ")

                        with st.expander(f"📝 {s_subj} - {s_unit} | Score: {s_score}/{s_tot} ({s_pct}%) - {s_date}"):
                            st.write(f"**Subject:** {s_subj}")
                            st.write(f"**Unit Name:** {s_unit}")
                            st.write(f"**Score:** {s_score} / {s_tot} ({s_pct}%)")
                            st.write(f"**Attempted At:** {s_date} UTC")
                else:
                    st.info("No test history found. Complete a test in the Practice set tab to see your scores here!")
            except Exception as e:
                st.error(f"Failed to fetch performance history: {e}")

        render_footer()
