import streamlit as st
import csv
import io
import hashlib
from supabase import Client

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



def render_admin_portal(db: Client):
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
            # ======================================
        # ADMIN TAB 3: USER MANAGEMENT & APPROVALS
        # ======================================
        with admin_tab3:
            st.markdown("### 👥 User Management & Registration Approvals")
            
            # --- SUB-TAB 1: PENDING REGISTRATION APPROVALS ---
            st.markdown("#### ⏳ Pending Student Registration Requests")
            try:
                pending_res = db.table("users").select("*").eq("status", "pending").execute()
                pending_users = pending_res.data if pending_res.data else []
                
                if pending_users:
                    st.info(f"There are **{len(pending_users)}** student registration request(s) awaiting your approval.")
                    for p_user in pending_users:
                        p_email = p_user.get("email", "")
                        p_name = p_user.get("name", "Student")
                        p_subject = p_user.get("subject", "N/A")
                        
                        with st.container():
                            st.markdown(f"""
                            <div style="background-color: #FFFFFF; padding: 15px 20px; border-radius: 10px; border-left: 5px solid #875e07; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                                <strong>👤 {p_name}</strong> ({p_email})<br>
                                <small>🎯 Subject: {p_subject}</small>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            c1, c2, c3 = st.columns([1, 1, 3])
                            with c1:
                                if st.button("✅ Approve", key=f"app_{p_email}"):
                                    db.table("users").update({"status": "approved"}).eq("email", p_email).execute()
                                    st.success(f"Approved {p_name} ({p_email})!")
                                    st.rerun()
                            with c2:
                                if st.button("❌ Reject", key=f"rej_{p_email}"):
                                    db.table("users").update({"status": "rejected"}).eq("email", p_email).execute()
                                    st.warning(f"Rejected {p_name} ({p_email}).")
                                    st.rerun()
                            st.markdown("---")
                else:
                    st.success("🎉 No pending registration requests at this time.")
            except Exception as e:
                st.error(f"Error fetching pending requests: {e}")
                
            st.markdown("---")
            
            # --- SUB-TAB 2: ADD SINGLE STUDENT MANUALLY ---
            st.markdown("#### ➕ Manually Add Single Student")
            with st.expander("Create Approved Student Account Manually"):
                with st.form("manual_user_form", clear_on_submit=True):
                    m_name = st.text_input("Full Name")
                    m_email = st.text_input("Email Address").strip().lower()
                    m_subject = st.selectbox("Target Subject", SUBJECT_LIST)
                    m_pass = st.text_input("Initial Password", type="password")
                    m_submit = st.form_submit_button("🚀 Add Student Account")
                    
                if m_submit:
                    if not m_name or not m_email or not m_pass:
                        st.warning("Please fill in Name, Email, and Password.")
                    else:
                        try:
                            chk = db.table("users").select("email").eq("email", m_email).execute()
                            if chk.data:
                                st.error("User with this email already exists.")
                            else:
                                new_u = {
                                    "name": m_name.strip(),
                                    "email": m_email,
                                    "subject": m_subject,
                                    "password": hash_text(m_pass),
                                    "role": "student",
                                    "status": "approved"
                                }
                                db.table("users").insert(new_u).execute()
                                st.success(f"✅ Added {m_name} ({m_email}) as Approved Student!")
                        except Exception as e:
                            st.error(f"Failed to add user: {e}")

            # --- SUB-TAB 3: BULK CSV STUDENT IMPORTER ---
            st.markdown("#### 📂 Bulk Import Students via CSV")
            with st.expander("Upload CSV File to Add Multiple Students"):
                st.caption("CSV columns required: `name`, `email`, `subject`, `password`")
                csv_file = st.file_uploader("Select CSV File", type=["csv"], key="user_csv_uploader")
                if csv_file is not None:
                    if st.button("🚀 Process & Import Students"):
                        try:
                            decoded = csv_file.getvalue().decode('utf-8')
                            reader = csv.DictReader(io.StringIO(decoded))
                            added_cnt = 0
                            skip_cnt = 0
                            for row in reader:
                                u_email = row.get("email", "").strip().lower()
                                u_name = row.get("name", "").strip()
                                u_subj = row.get("subject", "Paper 1 (General Paper)").strip()
                                u_pass = row.get("password", "Student@123").strip()
                                
                                if u_email and u_name:
                                    # Check existing
                                    chk = db.table("users").select("email").eq("email", u_email).execute()
                                    if not chk.data:
                                        rec = {
                                            "name": u_name,
                                            "email": u_email,
                                            "subject": u_subj,
                                            "password": hash_text(u_pass),
                                            "role": "student",
                                            "status": "approved"
                                        }
                                        db.table("users").insert(rec).execute()
                                        added_cnt += 1
                                    else:
                                        skip_cnt += 1
                            st.success(f"✅ Bulk Import Complete! Added {added_cnt} new student(s). Skipped {skip_cnt} existing.")
                        except Exception as e:
                            st.error(f"CSV import error: {e}")

            st.markdown("---")

            # --- SUB-TAB 4: ALL REGISTERED USERS & ROLE/STATUS MANAGEMENT ---
            st.markdown("#### 📋 Registered User Directory")
            try:
                users_res = db.table("users").select("id, name, email, subject, role, status").execute()
                if users_res.data:
                    st.dataframe(users_res.data, use_container_width=True)
                    
                    st.markdown("##### Update User Role or Status")
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        target_email = st.selectbox("Select User Email", [u["email"] for u in users_res.data])
                    with col2:
                        new_role = st.selectbox("Role", ["student", "admin"])
                    with col3:
                        new_status = st.selectbox("Status", ["approved", "pending", "rejected"])
                    
                    if st.button("Update User Profile"):
                        db.table("users").update({"role": new_role, "status": new_status}).eq("email", target_email).execute()
                        st.success(f"Updated {target_email}: Role={new_role}, Status={new_status}!")
                        st.rerun()
                else:
                    st.info("No registered users found.")
            except Exception as e:
                st.error(f"Failed to fetch users: {e}")

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
