import streamlit as st
import requests
import pandas as pd

API = "http://127.0.0.1:8000"

st.set_page_config(page_title="StudyTrack", page_icon="📚", layout="wide")
st.title("StudyTrack 📚")

# ---------- Helpers ----------
def get_json(url: str, params: dict | None = None):
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)

def post_json(url: str, payload: dict):
    try:
        r = requests.post(url, json=payload, timeout=10)
        try:
            body = r.json()
        except Exception:
            body = {"detail": r.text}
        return r.status_code, body
    except Exception as e:
        return 0, {"detail": str(e)}

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["📌 Référentiels", "🗂 Sessions", "📊 Dashboard", "➕ Ajouter une session"])

# =======================
# TAB 1: Students + Subjects
# =======================
with tab1:
    colA, colB = st.columns(2)

    with colA:
        st.subheader("Students")
        if st.button("Load students", key="btn_load_students"):
            data, err = get_json(f"{API}/students")
            if err:
                st.error(err)
            else:
                st.dataframe(data, use_container_width=True)

    with colB:
        st.subheader("Subjects")
        if st.button("Load subjects", key="btn_load_subjects"):
            data, err = get_json(f"{API}/subjects")
            if err:
                st.error(err)
            else:
                st.dataframe(data, use_container_width=True)

# =======================
# TAB 2: Sessions (enriched + raw)
# =======================
with tab2:
    st.subheader("Sessions")

    col1, col2 = st.columns(2)

    # -------- ENRICHED --------
    with col1:
        st.markdown("### Sessions (enriched: noms étudiant + matière)")
        limit_enriched = st.slider("Nombre de sessions (enriched)", 1, 200, 50, key="limit_enriched")

        if st.button("Load sessions (enriched)", key="btn_load_sessions_enriched"):
            data, err = get_json(f"{API}/sessions-enriched", params={"limit": limit_enriched})
            if err:
                st.error(err)
            else:
                if not data:
                    st.info("Aucune session.")
                else:
                    df = pd.DataFrame(data)

                    # ---------- Filters ----------
                    st.markdown("#### 🔎 Filtres")
                    fcol1, fcol2, fcol3, fcol4 = st.columns([2, 2, 2, 3])

                    if "student" not in df.columns:
                        df["student"] = "Unknown student"
                    if "subject" not in df.columns:
                        df["subject"] = "Unknown subject"
                    if "tags" not in df.columns:
                        df["tags"] = [[] for _ in range(len(df))]

                    students_list = sorted([x for x in df["student"].dropna().unique().tolist() if str(x).strip() != ""])
                    subjects_list = sorted([x for x in df["subject"].dropna().unique().tolist() if str(x).strip() != ""])

                    all_tags = set()
                    for t in df["tags"]:
                        if isinstance(t, list):
                            for one in t:
                                if one is not None and str(one).strip():
                                    all_tags.add(str(one).strip())
                    tags_list = sorted(list(all_tags))

                    with fcol1:
                        student_filter = st.selectbox("Étudiant", ["Tous"] + students_list, key="f_student")
                    with fcol2:
                        subject_filter = st.selectbox("Matière", ["Toutes"] + subjects_list, key="f_subject")
                    with fcol3:
                        tag_filter = st.selectbox("Tag", ["Tous"] + tags_list, key="f_tag")
                    with fcol4:
                        q = st.text_input("Recherche (notes / type / mood)", "", key="f_search")

                    if student_filter != "Tous":
                        df = df[df["student"] == student_filter]
                    if subject_filter != "Toutes":
                        df = df[df["subject"] == subject_filter]
                    if tag_filter != "Tous":
                        df = df[df["tags"].apply(lambda x: isinstance(x, list) and tag_filter in x)]

                    if q.strip():
                        qq = q.strip().lower()
                        for col in ["notes", "type", "mood"]:
                            if col not in df.columns:
                                df[col] = ""
                        df = df[
                            df["notes"].astype(str).str.lower().str.contains(qq, na=False)
                            | df["type"].astype(str).str.lower().str.contains(qq, na=False)
                            | df["mood"].astype(str).str.lower().str.contains(qq, na=False)
                        ]

                    # ---------- Display ----------
                    st.caption(f"Résultats: {len(df)} session(s)")
                    st.dataframe(df, use_container_width=True)

                    # ✅ Export CSV (ENRICHED) - ici df existe
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="⬇️ Exporter (CSV)",
                        data=csv,
                        file_name="sessions_enriched.csv",
                        mime="text/csv",
                        key="dl_sessions_enriched_csv"
                    )

    # -------- RAW --------
    with col2:
        st.markdown("### Sessions (raw: IDs)")
        limit_raw = st.slider("Nombre de sessions (raw)", 1, 200, 50, key="limit_raw")

        if st.button("Load sessions (raw)", key="btn_load_sessions_raw"):
            data, err = get_json(f"{API}/sessions", params={"limit": limit_raw})
            if err:
                st.error(err)
            else:
                if not data:
                    st.info("Aucune session.")
                else:
                    df_raw = pd.DataFrame(data)
                    st.dataframe(df_raw, use_container_width=True)

                    # ✅ Export CSV (RAW) - ici df_raw existe
                    csv_raw = df_raw.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="⬇️ Exporter RAW (CSV)",
                        data=csv_raw,
                        file_name="sessions_raw.csv",
                        mime="text/csv",
                        key="dl_sessions_raw_csv"
                    )

# =======================
# TAB 3: Dashboard
# =======================
with tab3:
    st.subheader("Dashboard 📊")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Temps par matière", key="btn_time_by_subject"):
            data, err = get_json(f"{API}/analytics/time-by-subject")
            if err:
                st.error(err)
            else:
                df = pd.DataFrame(data)
                if df.empty:
                    st.info("Pas de données.")
                else:
                    df = df.set_index("subject")
                    st.bar_chart(df["totalMinutes"])

    with col2:
        if st.button("Temps par période", key="btn_time_by_period"):
            data, err = get_json(f"{API}/analytics/time-by-period")
            if err:
                st.error(err)
            else:
                df = pd.DataFrame(data)
                if df.empty:
                    st.info("Pas de données.")
                else:
                    df = df.set_index("period")
                    st.bar_chart(df["totalMinutes"])

    with col3:
        if st.button("Difficulté par matière", key="btn_diff_by_subject"):
            data, err = get_json(f"{API}/analytics/difficulty-by-subject")
            if err:
                st.error(err)
            else:
                df = pd.DataFrame(data)
                if df.empty:
                    st.info("Pas de données.")
                else:
                    df = df.set_index("subject")
                    st.bar_chart(df["avgDifficulty"])

# =======================
# TAB 4: Create session
# =======================
with tab4:
    st.subheader("Create a session")

    # Petite aide: récupérer les IDs rapidement
    with st.expander("📌 Aide: récupérer studentId et subjectId"):
        colA, colB = st.columns(2)
        with colA:
            if st.button("Voir students", key="btn_help_students"):
                data, err = get_json(f"{API}/students")
                if err:
                    st.error(err)
                else:
                    st.json(data)
        with colB:
            if st.button("Voir subjects", key="btn_help_subjects"):
                data, err = get_json(f"{API}/subjects")
                if err:
                    st.error(err)
                else:
                    st.json(data)

    student_id = st.text_input("studentId (copy from /students)", key="student_id")
    subject_id = st.text_input("subjectId (copy from /subjects)", key="subject_id")

    started_at = st.text_input("startedAt (ISO)", "2026-01-13T19:00:00", key="started_at")
    duration = st.number_input("durationMin", 1, 600, 60, key="duration")
    difficulty = st.slider("difficulty", 1, 5, 3, key="difficulty")

    mood = st.selectbox("mood", ["Motivé", "Neutre", "Fatigué", "Stressé", "Content"], key="mood")
    period = st.selectbox("period", ["matin", "apres_midi", "soir", "nuit"], key="period")
    type_ = st.selectbox("type", ["cours", "exercices", "resume", "quiz"], key="type")

    tags_text = st.text_input("tags (séparés par des virgules, optionnel)", "", key="tags")
    notes = st.text_area("notes", "", key="notes")

    if st.button("Create session", key="btn_create_session"):
        tags = [t.strip() for t in tags_text.split(",") if t.strip()]
        payload = {
            "studentId": student_id.strip(),
            "subjectId": subject_id.strip(),
            "startedAt": started_at.strip(),
            "durationMin": int(duration),
            "difficulty": int(difficulty),
            "mood": mood,
            "period": period,
            "type": type_,
            "tags": tags,
            "notes": notes
        }
        status, body = post_json(f"{API}/sessions", payload)

        st.write("Status:", status)
        if status in (200, 201):
            st.success("Session créée ✅")
        else:
            st.error("Erreur lors de la création ❌")
        st.json(body)
