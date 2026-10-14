import streamlit as st
import pandas as pd
import time

def render_student_portal(db, user):
    st.title("📚 NET SET Student Portal")
    
    # 5 Main Student Components
    tab_res, tab_pyq, tab_syl, tab_test, tab_dash = st.tabs([
        "📖 Learning Resources", 
        "📝 PYQs", 
        "📋 Syllabus", 
        "⏱️ Ready to Test Yourself?", 
        "📊 Dashboard"
    ])

    user_subject = user["subject"]

    # ------------------------------------------
    # 1. LEARNING RESOURCES
    # ------------------------------------------
    with tab_res:
        st.header(f"Study Resources — {user_subject}")
        res_data = db.table("learning_materials") \
            .select("*") \
            .eq("subject", user_subject) \
            .eq("type", "resource") \
            .execute().data
            
        if res_data:
            for item in res_data:
                st.markdown(f"### 📄 {item['title']}")
                st.write(f"Format: `{item['format'].upper()}`")
                st.link_button("🔗 Open Resource", item['file_url'], type="primary")
                st.divider()
        else:
            st.info("No study resources uploaded yet for your subject.")

    # ------------------------------------------
    # 2. PYQ (PAST YEAR QUESTIONS)
    # ------------------------------------------
    with tab_pyq:
        st.header(f"Previous Year Question Papers — {user_subject}")
        pyqs = db.table("learning_materials") \
            .select("*") \
            .eq("subject", user_subject) \
            .eq("type", "pyq") \
            .execute().data
            
        if pyqs:
            years = sorted(list(set([p['year'] for p in pyqs if p['year']])), reverse=True)
            selected_year = st.selectbox("Select Paper Year", years)
            
            filtered = [p for p in pyqs if p['year'] == selected_year]
            for paper in filtered:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{paper['title']}** (Year: {paper['year']})")
                with col2:
                    st.link_button("📥 View PYQ Paper", paper['file_url'])
        else:
            st.info("No PYQ papers available yet.")

    # ------------------------------------------
    # 3. SYLLABUS
    # ------------------------------------------
    with tab_syl:
        st.header(f"Official Syllabus — {user_subject}")
        syl_data = db.table("learning_materials") \
            .select("*") \
            .eq("subject", user_subject) \
            .eq("type", "syllabus") \
            .execute().data
            
        if syl_data:
            for item in syl_data:
                st.subheader(item['title'])
                st.link_button("📄 View / Download Syllabus", item['file_url'])
        else:
            st.info("Syllabus document not uploaded yet.")

    # ------------------------------------------
    # 4. TIMED MCQ TEST ENGINE
    # ------------------------------------------
    with tab_test:
        st.header("⏱️ Ready to Test Yourself?")
        
        unit_options = [f"Unit {i}" for i in range(1, 11)] + ["Full Syllabus"]
        selected_unit = st.selectbox("Select Unit / Syllabus Scope", unit_options)
        
        num_questions = 100 if selected_unit == "Full Syllabus" else 20
        time_limit_mins = 120 if selected_unit == "Full Syllabus" else 30
        
        if "test_active" not in st.session_state:
            st.session_state.test_active = False
            st.session_state.test_questions = []
            st.session_state.start_time = None

        if not st.session_state.test_active:
            st.warning(f"**Test Rules**: {selected_unit} contains **{num_questions} Questions**. Time limit: **{time_limit_mins} minutes**.")
            if st.button("🚀 Start Test Now", type="primary"):
                q_query = db.table("questions").select("*").eq("subject", user_subject)
                if selected_unit != "Full Syllabus":
                    q_query = q_query.eq("unit", selected_unit)
                
                questions = q_query.limit(num_questions).execute().data
                
                if len(questions) == 0:
                    st.error("No questions found in the database for this unit yet.")
                else:
                    st.session_state.test_active = True
                    st.session_state.test_questions = questions
                    st.session_state.start_time = time.time()
                    st.rerun()

        else:
            elapsed = int(time.time() - st.session_state.start_time)
            total_seconds = time_limit_mins * 60
            remaining_seconds = max(0, total_seconds - elapsed)
            mins, secs = divmod(remaining_seconds, 60)
            
            st.metric("⏳ Time Remaining", f"{mins:02d}:{secs:02d}")
            if remaining_seconds <= 0:
                st.error("⏰ Time is up! Submitting test...")

            st.divider()

            with st.form("mcq_test_form"):
                user_ans = {}
                for idx, q in enumerate(st.session_state.test_questions, start=1):
                    st.markdown(f"**Q{idx}. {q['question_text']}**")
                    options = {
                        "A": q['option_a'],
                        "B": q['option_b'],
                        "C": q['option_c'],
                        "D": q['option_d']
                    }
                    choice = st.radio(
                        f"Select answer for Q{idx}:",
                        options=["A", "B", "C", "D"],
                        format_func=lambda opt: f"{opt}) {options[opt]}",
                        key=f"q_{q['id']}"
                    )
                    user_ans[q['id']] = choice
                    st.write("")

                submit_test = st.form_submit_button("🏁 Submit Test")

                if submit_test or remaining_seconds <= 0:
                    score = 0
                    detailed_report = []
                    
                    for q in st.session_state.test_questions:
                        given_opt = user_ans.get(q['id'])
                        is_correct = (given_opt == q['correct_option'])
                        if is_correct:
                            score += 1
                        
                        detailed_report.append({
                            "question": q['question_text'],
                            "given": given_opt,
                            "correct": q['correct_option'],
                            "is_correct": is_correct,
                            "explanation": q.get('explanation', 'None')
                        })

                    db.table("test_attempts").insert({
                        "user_id": user['id'],
                        "subject": user_subject,
                        "test_type": selected_unit,
                        "score": score,
                        "total_questions": len(st.session_state.test_questions),
                        "answers_json": detailed_report
                    }).execute()

                    st.session_state.test_active = False
                    st.session_state.last_report = {
                        "score": score,
                        "total": len(st.session_state.test_questions),
                        "details": detailed_report
                    }
                    st.rerun()

        if "last_report" in st.session_state and not st.session_state.test_active:
            report = st.session_state.last_report
            st.success(f"🎉 Test Completed! Score: **{report['score']} / {report['total']}**")
            
            st.subheader("💡 Solutions & Explanations for Incorrect Answers")
            for idx, item in enumerate(report['details'], start=1):
                if not item['is_correct']:
                    with st.expander(f"❌ Q{idx}: {item['question']}"):
                        st.write(f"Your Answer: **{item['given']}**")
                        st.write(f"Correct Answer: **{item['correct']}**")
                        st.info(f"**Explanation:** {item['explanation']}")

    # ------------------------------------------
    # 5. DASHBOARD
    # ------------------------------------------
    with tab_dash:
        st.header("📈 Previous Attempts & Performance")
        attempts = db.table("test_attempts") \
            .select("*") \
            .eq("user_id", user['id']) \
            .order("attempted_at", desc=True) \
            .execute().data
            
        if attempts:
            df = pd.DataFrame(attempts)
            df['Percentage'] = (df['score'] / df['total_questions']) * 100
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Tests Attempted", len(df))
            c2.metric("Average Score (%)", f"{df['Percentage'].mean():.1f}%")
            c3.metric("Highest Score (%)", f"{df['Percentage'].max():.1f}%")
            
            st.subheader("Test Log History")
            st.dataframe(
                df[['test_type', 'score', 'total_questions', 'Percentage', 'attempted_at']],
                column_config={
                    "test_type": "Test Scope",
                    "score": "Score",
                    "total_questions": "Total Marks",
                    "Percentage": st.column_config.NumberColumn("Score %", format="%.1f%%"),
                    "attempted_at": "Date & Time"
                },
                use_container_width=True
            )
        else:
            st.info("No test attempts recorded yet. Take your first test under 'Ready to Test Yourself?'!")