import streamlit as st
import random
import time
import re
from supabase import Client

# ==========================================
# MASTER SUBJECT & UNIT LISTS
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
# MATCHING & SANITIZATION HELPERS
# ==========================================
def get_clean_str(val) -> str:
    """Sanitizes Supabase string values, handling None and nulls cleanly."""
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ["none", "null", "nan"]:
        return ""
    return s

def is_subject_match(q: dict, target_subject: str) -> bool:
    """Flexible subject matching with clean null handling."""
    if not target_subject:
        return True
    
    q_subj = get_clean_str(q.get("subject")).lower()
    t_subj = get_clean_str(target_subject).lower()
    
    if not q_subj:
        return True
    if q_subj == t_subj:
        return True
    if "paper 1" in q_subj or "general" in q_subj:
        return True
    if t_subj in q_subj or q_subj in t_subj:
        return True
    main_target = t_subj.split("(")[0].strip()
    if main_target and main_target in q_subj:
        return True
    return False

def is_unit_match(q: dict, u_idx: int) -> bool:
    """Robust regex matching for Unit 1 through Unit 10."""
    u_str = f"Unit {u_idx}"
    u_str_dash = f"Unit-{u_idx}"
    u_str_nodpace = f"Unit{u_idx}"
    u_str_zero = f"Unit 0{u_idx}"
    
    val_unit = get_clean_str(q.get("unit"))
    val_topic = get_clean_str(q.get("topic"))
    val_unit_num = get_clean_str(q.get("unit_number")) or get_clean_str(q.get("unit_no")) or get_clean_str(q.get("unit_id"))
    
    if val_unit_num == str(u_idx) or val_unit_num == f"0{u_idx}":
        return True

    text = (val_unit + " " + val_topic).strip().lower()
    if not text:
        return False

    if val_unit.lower() in [u_str.lower(), u_str_dash.lower(), u_str_nodpace.lower(), u_str_zero.lower(), str(u_idx)]:
        return True
    if val_topic.lower() in [u_str.lower(), u_str_dash.lower(), u_str_nodpace.lower(), u_str_zero.lower(), str(u_idx)]:
        return True

    pattern = rf"\bunit\s*[-:_]*\s*0*{u_idx}\b"
    if re.search(pattern, text, re.IGNORECASE):
        return True
        
    if f"unit {u_idx}" in text or f"unit-{u_idx}" in text or f"unit{u_idx}" in text or f"unit 0{u_idx}" in text:
        return True
        
    return False

def get_option_val(q: dict, opt_key: str) -> str:
    """Extracts option value supporting multiple CSV schema column keys."""
    key = opt_key.lower()
    possible_keys = [
        f"option_{key}", f"option{key}", f"opt_{key}", f"opt{key}", key,
        f"option_{opt_key}", f"option{opt_key}", f"opt_{opt_key}", f"opt{opt_key}", opt_key
    ]
    for k in possible_keys:
        val = q.get(k)
        if val is not None and str(val).strip() != "":
            return str(val).strip()
    return ""

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
# STUDENT PORTAL RENDERER
# ==========================================
def render_student_portal(db: Client):
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
                        q_res = db.table("questions").select("*").range(0, 4999).execute()
                        all_qs = q_res.data if q_res.data else []
                        subj_qs = [q for q in all_qs if is_subject_match(q, user_subject)]
                        if not subj_qs:
                            subj_qs = all_qs

                        selected_qs = []
                        if "Full Paper" in selected_mod:
                            used_ids = set()
                            unit_selected = []
                            
                            for u_idx in range(1, 11):
                                u_pool = [q for q in subj_qs if is_unit_match(q, u_idx) and id(q) not in used_ids]
                                if len(u_pool) >= 10:
                                    chosen = random.sample(u_pool, 10)
                                else:
                                    chosen = u_pool
                                for q in chosen:
                                    used_ids.add(id(q))
                                    unit_selected.append(q)
                                    
                            selected_qs.extend(unit_selected)
                            
                            if len(selected_qs) < 100:
                                needed = 100 - len(selected_qs)
                                rem_subj = [q for q in subj_qs if id(q) not in used_ids]
                                if rem_subj:
                                    add_from_subj = random.sample(rem_subj, min(needed, len(rem_subj)))
                                    for q in add_from_subj:
                                        used_ids.add(id(q))
                                        selected_qs.append(q)
                                        
                            if len(selected_qs) < 100:
                                needed = 100 - len(selected_qs)
                                rem_all = [q for q in all_qs if id(q) not in used_ids]
                                if rem_all:
                                    add_from_all = random.sample(rem_all, min(needed, len(rem_all)))
                                    selected_qs.extend(add_from_all)
                                    
                            random.shuffle(selected_qs)
                            st.session_state.time_limit = 120 * 60
                        else:
                            u_match = re.search(r'\d+', selected_mod)
                            u_idx = int(u_match.group(0)) if u_match else 0
                            if u_idx > 0:
                                u_pool = [q for q in subj_qs if is_unit_match(q, u_idx)]
                            else:
                                u_pool = [q for q in subj_qs if q.get("unit") == selected_mod or q.get("topic") == selected_mod]
                                
                            if len(u_pool) < 25:
                                rem_pool = [q for q in subj_qs if id(q) not in [id(item) for item in u_pool]]
                                needed = 25 - len(u_pool)
                                if rem_pool:
                                    u_pool.extend(random.sample(rem_pool, min(needed, len(rem_pool))))
                                    
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
                    c_key = get_clean_str(q.get("correct_option")).upper()
                    if st.session_state.user_answers.get(idx) == c_key:
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
                except Exception:
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
                unit_label = get_clean_str(q_data.get("unit")) or get_clean_str(q_data.get("topic")) or st.session_state.test_module
                st.markdown(f"#### Question {curr_idx + 1} of {total_qs} (`{unit_label}`)")
            
            st.write(f"**{q_data.get('question_text', 'Question text unavailable')}**")
            
            opts = {
                "A": get_option_val(q_data, "A"),
                "B": get_option_val(q_data, "B"),
                "C": get_option_val(q_data, "C"),
                "D": get_option_val(q_data, "D")
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
                        c_key = get_clean_str(q.get("correct_option")).upper()
                        if st.session_state.user_answers.get(idx) == c_key:
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
                correct_key = get_clean_str(q.get("correct_option")).upper()
                is_correct = user_ans == correct_key
                
                status_icon = "✅ Correct" if is_correct else ("❌ Incorrect" if user_ans != "Unattempted" else "⚪ Unattempted")
                with st.expander(f"Q{idx}: {q.get('question_text')} [{status_icon}]"):
                    st.write(f"**A:** {get_option_val(q, 'A')}")
                    st.write(f"**B:** {get_option_val(q, 'B')}")
                    st.write(f"**C:** {get_option_val(q, 'C')}")
                    st.write(f"**D:** {get_option_val(q, 'D')}")
                    st.write(f"**Your Answer:** {user_ans}")
                    st.write(f"**Correct Key:** {correct_key}")
                    exp = q.get("explanation")
                    if exp and get_clean_str(exp):
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
