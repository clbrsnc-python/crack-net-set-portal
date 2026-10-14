import streamlit as st
import pandas as pd
from utils.db import upload_file_to_storage
from utils.txt_parser import parse_txt_questions

def render_admin_panel(db, subject_list):
    st.title("⚙️ Admin Control Panel")
    
    admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5 = st.tabs([
        "1️⃣ Upload PYQs", 
        "2️⃣ Upload Syllabus", 
        "3️⃣ Upload Resources", 
        "4️⃣ Question Importer", 
        "5️⃣ User Control Panel"
    ])

    # ------------------------------------------
    # 1. UPLOAD PYQ
    # ------------------------------------------
    with admin_tab1:
        st.subheader("Upload Past Year Question (PYQ) Paper")
        with st.form("pyq_form"):
            subj = st.selectbox("Select Subject", subject_list, key="pyq_subj")
            year = st.number_input("Exam Year", min_value=2000, max_value=2030, value=2023)
            title = st.text_input("Paper Title (e.g. NET SET June 2023 Paper II)")
            file = st.file_uploader("Upload PDF File", type=["pdf"], key="pyq_file")
            
            if st.form_submit_button("Upload PYQ Paper"):
                if file and title:
                    file_path = f"pyq/{subj}/{year}_{file.name}"
                    url = upload_file_to_storage(db, "net-set-materials", file.getvalue(), file_path)
                    if url:
                        db.table("learning_materials").insert({
                            "type": "pyq", "subject": subj, "year": year,
                            "title": title, "file_url": url, "format": "pdf"
                        }).execute()
                        st.success("✅ PYQ uploaded successfully!")

    # ------------------------------------------
    # 2. UPLOAD SYLLABUS
    # ------------------------------------------
    with admin_tab2:
        st.subheader("Upload Subject Syllabus")
        with st.form("syl_form"):
            subj = st.selectbox("Select Subject", subject_list, key="syl_subj")
            title = st.text_input("Syllabus Title", value=f"Official Syllabus — {subj}")
            file = st.file_uploader("Upload Syllabus PDF", type=["pdf"], key="syl_file")
            
            if st.form_submit_button("Upload Syllabus"):
                if file:
                    file_path = f"syllabus/{subj}/{file.name}"
                    url = upload_file_to_storage(db, "net-set-materials", file.getvalue(), file_path)
                    if url:
                        db.table("learning_materials").insert({
                            "type": "syllabus", "subject": subj,
                            "title": title, "file_url": url, "format": "pdf"
                        }).execute()
                        st.success("✅ Syllabus uploaded successfully!")

    # ------------------------------------------
    # 3. UPLOAD RESOURCES
    # ------------------------------------------
    with admin_tab3:
        st.subheader("Upload Learning Resource / Reference Material")
        subj = st.selectbox("Select Subject", subject_list, key="res_subj")
        res_type = st.radio("Resource Type", ["PDF Document", "External Web Link"])
        title = st.text_input("Resource Title")
        
        if res_type == "PDF Document":
            file = st.file_uploader("Upload PDF", type=["pdf"], key="res_file")
            if st.button("Submit PDF Resource"):
                if file and title:
                    file_path = f"resources/{subj}/{file.name}"
                    url = upload_file_to_storage(db, "net-set-materials", file.getvalue(), file_path)
                    db.table("learning_materials").insert({
                        "type": "resource", "subject": subj,
                        "title": title, "file_url": url, "format": "pdf"
                    }).execute()
                    st.success("✅ Resource uploaded!")
        else:
            link_url = st.text_input("Paste Web Link / URL")
            if st.button("Submit Link Resource"):
                if link_url and title:
                    db.table("learning_materials").insert({
                        "type": "resource", "subject": subj,
                        "title": title, "file_url": link_url, "format": "html"
                    }).execute()
                    st.success("✅ Web Resource link added!")

    # ------------------------------------------
    # 4. QUESTION IMPORTER
    # ------------------------------------------
    with admin_tab4:
        st.subheader("Mock Test Question Batch Importer")
        subj = st.selectbox("Target Subject", subject_list, key="q_subj")
        unit = st.selectbox("Target Unit", [f"Unit {i}" for i in range(1, 11)] + ["Full Syllabus"])
        
        txt_file = st.file_uploader("Upload Batch Questions (.txt File)", type=["txt"])
        if txt_file:
            content = txt_file.getvalue().decode("utf-8")
            parsed = parse_txt_questions(content, subj, unit)
            st.info(f"Parsed **{len(parsed)}** questions successfully from TXT.")
            
            if len(parsed) > 0:
                st.dataframe(pd.DataFrame(parsed)[['question_text', 'correct_option', 'explanation']])
                if st.button("💾 Import Questions into Database", type="primary"):
                    db.table("questions").insert(parsed).execute()
                    st.success(f"🎉 Successfully imported {len(parsed)} questions!")

    # ------------------------------------------
    # 5. USER AUTHORITY CONTROL PANEL
    # ------------------------------------------
    with admin_tab5:
        st.subheader("User Account & Access Authority Control")
        users_data = db.table("users").select("id, name, email, subject, role, status, created_at").execute().data
        
        if users_data:
            df_users = pd.DataFrame(users_data)
            
            selected_user_email = st.selectbox("Select User Account to Modify", df_users['email'])
            user_info = df_users[df_users['email'] == selected_user_email].iloc[0]
            
            c1, c2 = st.columns(2)
            with c1:
                new_status = st.radio("Access Status", ["active", "blocked"], index=0 if user_info['status'] == "active" else 1)
            with c2:
                new_role = st.radio("User Privilege Role", ["student", "admin"], index=0 if user_info['role'] == "student" else 1)
                
            if st.button("Apply Privilege / Access Change"):
                db.table("users").update({
                    "status": new_status,
                    "role": new_role
                }).eq("email", selected_user_email).execute()
                st.success(f"Updated {selected_user_email} (Status: {new_status}, Role: {new_role}).")
                st.rerun()

            st.divider()
            st.write("### All Registered Users")
            st.dataframe(df_users, use_container_width=True)