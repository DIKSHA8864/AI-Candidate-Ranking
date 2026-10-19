
import streamlit as st
import pandas as pd

from ats.database import (
    init_db,
    seed_demo_data,
    get_connection,
    HIRING_STAGES,
)

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="TalentFlow ATS",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- DATABASE ----------------

init_db()
seed_demo_data()


def fetch_dataframe(query, params=()):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_count(query):
    with get_connection() as conn:
        return conn.execute(query).fetchone()[0]


# ---------------- STYLING ----------------

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f7f8fc;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
    }

    [data-testid="stSidebar"] * {
        color: #f9fafb;
    }

    .dashboard-subtitle {
        color: #64748b;
        font-size: 15px;
        margin-bottom: 22px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 18px;
        border-radius: 12px;
    }

    div[data-testid="stMetricLabel"] {
        color: #64748b;
    }

    .section-heading {
        font-size: 19px;
        font-weight: 650;
        color: #111827;
        margin-top: 15px;
        margin-bottom: 10px;
    }

    .dashboard-note {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 15px;
        color: #475569;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.markdown("# TalentFlow")
    st.caption("Applicant Tracking System")
    st.divider()

    page = st.radio(
        "MAIN MENU",
        [
            "Dashboard",
            "Candidates",
            "Jobs",
            "Applications",
        ],
        index=0,
    )

    st.divider()
    st.caption("Recruitment workspace")
    st.caption("Local development version")

# ---------------- PAGE HEADER ----------------

if page == "Dashboard":

    st.title("Recruitment Dashboard")
    st.markdown(
        '<div class="dashboard-subtitle">'
        "Welcome back! Here is an overview of your recruitment pipeline."
        "</div>",
        unsafe_allow_html=True,
    )

    # ---------------- METRICS ----------------

    total_candidates = get_count(
        "SELECT COUNT(*) FROM candidates"
    )

    active_jobs = get_count(
        "SELECT COUNT(*) FROM jobs WHERE status = 'Open'"
    )

    total_applications = get_count(
        "SELECT COUNT(*) FROM applications"
    )

    interview_count = get_count(
        "SELECT COUNT(*) FROM applications "
        "WHERE stage = 'Interview'"
    )

    offers_count = get_count(
        "SELECT COUNT(*) FROM applications WHERE stage = 'Offer'"
    )

    hired_count = get_count(
        "SELECT COUNT(*) FROM applications WHERE stage = 'Hired'"
    )

    metric_row_1 = st.columns(3)

    metric_row_1[0].metric(
        "Total Candidates",
        f"{total_candidates:,}",
    )

    metric_row_1[1].metric(
        "Active Job Openings",
        f"{active_jobs:,}",
    )

    metric_row_1[2].metric(
        "Total Applications",
        f"{total_applications:,}",
    )

    metric_row_2 = st.columns(3)

    metric_row_2[0].metric(
        "Interviews",
        f"{interview_count:,}",
    )

    metric_row_2[1].metric(
        "Offers Made",
        f"{offers_count:,}",
    )

    metric_row_2[2].metric(
        "Successful Hires",
        f"{hired_count:,}",
    )

    st.divider()

    # ---------------- PIPELINE ----------------

    st.markdown(
        '<div class="section-heading">Hiring Pipeline</div>',
        unsafe_allow_html=True,
    )

    pipeline_df = fetch_dataframe(
        """
        SELECT stage, COUNT(*) AS total
        FROM applications
        GROUP BY stage
        """
    )

    stage_counts = dict(
        zip(pipeline_df["stage"], pipeline_df["total"])
    )

    pipeline_cols = st.columns(6)

    for index, stage in enumerate(HIRING_STAGES[:6]):
        with pipeline_cols[index]:
            st.metric(
                label=stage,
                value=int(stage_counts.get(stage, 0)),
            )

    if pipeline_df.empty:
        st.info("No applications yet. Add candidates and applications to see your pipeline.")
    else:
        st.markdown("#### Applications by stage")

        chart_df = pipeline_df.set_index("stage")[["total"]]

        st.bar_chart(
            chart_df,
            color="#6366f1",
            height=260,
        )

    # ---------------- RECENT APPLICATIONS ----------------

    st.divider()

    left_col, right_col = st.columns(
        [1.7, 1],
        gap="large",
    )

    with left_col:
        st.markdown(
            '<div class="section-heading">Recent Applications</div>',
            unsafe_allow_html=True,
        )

        recent_df = fetch_dataframe(
            """
            SELECT
                a.id AS application_id,
                c.name AS candidate,
                j.title AS job,
                a.stage AS stage,
                a.ai_score AS ai_score,
                a.applied_at AS applied_at
            FROM applications a
            JOIN candidates c ON c.id = a.candidate_id
            JOIN jobs j ON j.id = a.job_id
            ORDER BY a.id DESC
            LIMIT 10
            """
        )

        if recent_df.empty:
            st.info("No applications available yet.")
        else:
            st.dataframe(
                recent_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "application_id": st.column_config.NumberColumn(
                        "Application ID"
                    ),
                    "candidate": st.column_config.TextColumn(
                        "Candidate"
                    ),
                    "job": st.column_config.TextColumn(
                        "Job"
                    ),
                    "stage": st.column_config.TextColumn(
                        "Hiring Stage"
                    ),
                    "ai_score": st.column_config.NumberColumn(
                        "AI Match Score",
                        format="%.1f",
                    ),
                    "applied_at": st.column_config.TextColumn(
                        "Applied On"
                    ),
                },
            )

    with right_col:
        st.markdown(
            '<div class="section-heading">Open Positions</div>',
            unsafe_allow_html=True,
        )

        jobs_df = fetch_dataframe(
            """
            SELECT
                j.id,
                j.title,
                j.department,
                j.location,
                COUNT(a.id) AS applicants
            FROM jobs j
            LEFT JOIN applications a ON a.job_id = j.id
            WHERE j.status = 'Open'
            GROUP BY j.id
            ORDER BY j.id DESC
            LIMIT 8
            """
        )

        if jobs_df.empty:
            st.info("No open positions. Create a job to get started.")
        else:
            for _, job in jobs_df.iterrows():
                st.markdown(
                    f"**{job['title']}**  \n"
                    f"{job['department'] or 'General'} · "
                    f"{job['location'] or 'Location not specified'}"
                )
                st.caption(
                    f"{int(job['applicants'])} application(s)"
                )
                st.divider()

    # ---------------- STAGE BREAKDOWN ----------------

    st.markdown(
        '<div class="section-heading">Application Status Breakdown</div>',
        unsafe_allow_html=True,
    )

    status_df = fetch_dataframe(
        """
        SELECT stage AS Status, COUNT(*) AS Applications
        FROM applications
        GROUP BY stage
        ORDER BY Applications DESC
        """
    )

    if not status_df.empty:
        st.dataframe(
            status_df,
            use_container_width=True,
            hide_index=True,
        )

# ---------------- OTHER NAVIGATION PAGES ----------------

elif page == "Candidates":
    st.title("Candidate Management")
    st.caption("Add, search, update, and manage candidate profiles.")

    # ---------- ADD CANDIDATE ----------
    with st.expander("➕ Add New Candidate", expanded=False):
        with st.form("add_candidate_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Full Name *")
                email = st.text_input("Email")
                phone = st.text_input("Phone")

            with col2:
                location = st.text_input("Location")
                experience = st.number_input(
                    "Experience (years)",
                    min_value=0.0,
                    max_value=60.0,
                    value=0.0,
                    step=0.5,
                )
                skills = st.text_input(
                    "Skills",
                    placeholder="Python, SQL, Machine Learning",
                )

            summary = st.text_area("Professional Summary")

            submitted = st.form_submit_button(
                "Add Candidate",
                type="primary",
            )

            if submitted:
                if not name.strip():
                    st.error("Full name is required.")
                else:
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                """
                                INSERT INTO candidates
                                (name, email, phone, location, skills,
                                 experience_years, summary)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    name.strip(),
                                    email.strip() or None,
                                    phone.strip(),
                                    location.strip(),
                                    skills.strip(),
                                    experience,
                                    summary.strip(),
                                ),
                            )

                        st.success("Candidate added successfully.")
                        st.rerun()

                    except Exception as exc:
                        st.error(
                            "Could not add candidate. "
                            "Check whether the email already exists. "
                            f"Details: {exc}"
                        )

    st.divider()

    # ---------- SEARCH AND LIST ----------
    st.subheader("All Candidates")

    search = st.text_input(
        "Search candidates",
        placeholder="Search by name, email, location, or skills",
    )

    candidates_df = fetch_dataframe(
        """
        SELECT id, name, email, phone, location, skills,
               experience_years, summary, created_at
        FROM candidates
        WHERE name LIKE ?
           OR COALESCE(email, '') LIKE ?
           OR COALESCE(location, '') LIKE ?
           OR COALESCE(skills, '') LIKE ?
        ORDER BY id DESC
        """,
        tuple([f"%{search}%"] * 4),
    )

    st.metric("Matching Candidates", len(candidates_df))

    if candidates_df.empty:
        st.info("No candidates found. Add a candidate above.")
    else:
        st.dataframe(
            candidates_df,
            width="stretch",
            hide_index=True,
        )

        # ---------- EDIT OR DELETE ----------
        st.divider()
        st.subheader("Edit or Delete a Candidate")

        candidate_options = {
            f"{row['name']} (ID: {row['id']})": int(row["id"])
            for _, row in candidates_df.iterrows()
        }

        selected_label = st.selectbox(
            "Select candidate",
            list(candidate_options.keys()),
        )
        selected_id = candidate_options[selected_label]

        selected_df = fetch_dataframe(
            "SELECT * FROM candidates WHERE id = ?",
            (selected_id,),
        )
        candidate = selected_df.iloc[0]

        with st.form("edit_candidate_form"):
            col1, col2 = st.columns(2)

            with col1:
                edit_name = st.text_input(
                    "Full Name *",
                    value=str(candidate["name"] or ""),
                )
                edit_email = st.text_input(
                    "Email",
                    value=str(candidate["email"] or ""),
                )
                edit_phone = st.text_input(
                    "Phone",
                    value=str(candidate["phone"] or ""),
                )

            with col2:
                edit_location = st.text_input(
                    "Location",
                    value=str(candidate["location"] or ""),
                )
                edit_experience = st.number_input(
                    "Experience (years)",
                    min_value=0.0,
                    max_value=60.0,
                    value=float(candidate["experience_years"] or 0),
                    step=0.5,
                )
                edit_skills = st.text_input(
                    "Skills",
                    value=str(candidate["skills"] or ""),
                )

            edit_summary = st.text_area(
                "Professional Summary",
                value=str(candidate["summary"] or ""),
            )

            save_changes = st.form_submit_button(
                "Save Changes",
                type="primary",
            )

            if save_changes:
                if not edit_name.strip():
                    st.error("Full name is required.")
                else:
                    try:
                        with get_connection() as conn:
                            conn.execute(
                                """
                                UPDATE candidates
                                SET name = ?, email = ?, phone = ?,
                                    location = ?, skills = ?,
                                    experience_years = ?, summary = ?
                                WHERE id = ?
                                """,
                                (
                                    edit_name.strip(),
                                    edit_email.strip() or None,
                                    edit_phone.strip(),
                                    edit_location.strip(),
                                    edit_skills.strip(),
                                    edit_experience,
                                    edit_summary.strip(),
                                    selected_id,
                                ),
                            )

                        st.success("Candidate updated successfully.")
                        st.rerun()

                    except Exception as exc:
                        st.error(
                            "Could not update candidate. "
                            f"Check for duplicate emails. Details: {exc}"
                        )

        with st.expander("Delete Candidate"):
            st.warning(
                "Deleting a candidate also deletes their linked "
                "applications and interview history from this database."
            )

            confirm_delete = st.checkbox(
                f"I confirm deletion of {candidate['name']}",
                key=f"confirm_delete_{selected_id}",
            )

            if st.button(
                "Delete Selected Candidate",
                type="secondary",
                disabled=not confirm_delete,
            ):
                try:
                    with get_connection() as conn:
                        conn.execute(
                            "DELETE FROM candidates WHERE id = ?",
                            (selected_id,),
                        )

                    st.success("Candidate and linked records deleted.")
                    st.rerun()

                except Exception as exc:
                    st.error(f"Could not delete candidate: {exc}")


elif page == "Jobs":
    st.title("Job Management")
    st.caption("Create, edit, search, and manage job openings.")

    # ---------- CREATE JOB ----------
    with st.expander("➕ Create New Job", expanded=False):
        with st.form("create_job_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                title = st.text_input("Job Title *")
                department = st.text_input("Department")
                location = st.text_input("Location")

            with col2:
                employment_type = st.selectbox(
                    "Employment Type",
                    ["Full-time", "Part-time", "Contract", "Internship"],
                )

                experience_required = st.number_input(
                    "Required Experience",
                    min_value=0.0,
                    max_value=50.0,
                    value=0.0,
                    step=0.5,
                )

                status = st.selectbox(
                    "Status",
                    ["Open", "Closed"],
                )

            required_skills = st.text_input(
                "Required Skills",
                placeholder="Python, SQL, FastAPI, NLP",
            )

            description = st.text_area("Job Description *")

            create_job = st.form_submit_button(
                "Create Job",
                type="primary",
            )

            if create_job:
                if not title.strip() or not description.strip():
                    st.error("Job title and description are required.")
                else:
                    with get_connection() as conn:
                        conn.execute(
                            """
                            INSERT INTO jobs
                            (
                                title,
                                department,
                                location,
                                employment_type,
                                experience_required,
                                required_skills,
                                description,
                                status
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                title.strip(),
                                department.strip(),
                                location.strip(),
                                employment_type,
                                experience_required,
                                required_skills.strip(),
                                description.strip(),
                                status,
                            ),
                        )

                    st.success("Job created successfully.")
                    st.rerun()

    st.divider()

    # ---------- SEARCH ----------
    st.subheader("All Job Openings")

    search_job = st.text_input(
        "Search jobs",
        placeholder="Search by title, department, location, or skills",
    )

    jobs_df = fetch_dataframe(
        """
        SELECT
            j.id,
            j.title,
            j.department,
            j.location,
            j.employment_type,
            j.experience_required,
            j.required_skills,
            j.status,
            COUNT(a.id) AS applications
        FROM jobs j
        LEFT JOIN applications a
            ON a.job_id = j.id
        WHERE j.title LIKE ?
           OR COALESCE(j.department,'') LIKE ?
           OR COALESCE(j.location,'') LIKE ?
           OR COALESCE(j.required_skills,'') LIKE ?
        GROUP BY j.id
        ORDER BY j.id DESC
        """,
        tuple([f"%{search_job}%"] * 4),
    )

    col1, col2, col3 = st.columns(3)

    total_jobs = get_count("SELECT COUNT(*) FROM jobs")
    open_jobs = get_count(
        "SELECT COUNT(*) FROM jobs WHERE status='Open'"
    )

    col1.metric("Total Jobs", total_jobs)
    col2.metric("Open Jobs", open_jobs)
    col3.metric("Closed Jobs", total_jobs - open_jobs)

    if jobs_df.empty:
        st.info("No jobs available.")
    else:
        st.dataframe(
            jobs_df,
            width="stretch",
            hide_index=True,
        )

        st.divider()

        # ---------- EDIT JOB ----------
        st.subheader("Edit Job")

        options = {
            f"{row['title']} (ID {row['id']})": int(row["id"])
            for _, row in jobs_df.iterrows()
        }

        selected = st.selectbox(
            "Select Job",
            list(options.keys()),
        )

        job_id = options[selected]

        selected_job = fetch_dataframe(
            "SELECT * FROM jobs WHERE id=?",
            (job_id,),
        ).iloc[0]

        with st.form("edit_job_form"):
            edit_title = st.text_input(
                "Job Title",
                value=str(selected_job["title"]),
            )

            edit_department = st.text_input(
                "Department",
                value=str(selected_job["department"] or ""),
            )

            edit_location = st.text_input(
                "Location",
                value=str(selected_job["location"] or ""),
            )

            edit_type = st.selectbox(
                "Employment Type",
                ["Full-time", "Part-time", "Contract", "Internship"],
                index=["Full-time","Part-time","Contract","Internship"].index(
                    selected_job["employment_type"]
                ),
            )

            edit_experience = st.number_input(
                "Required Experience",
                value=float(selected_job["experience_required"]),
                step=0.5,
            )

            edit_skills = st.text_input(
                "Required Skills",
                value=str(selected_job["required_skills"] or ""),
            )

            edit_description = st.text_area(
                "Job Description",
                value=str(selected_job["description"] or ""),
            )

            edit_status = st.selectbox(
                "Status",
                ["Open", "Closed"],
                index=0 if selected_job["status"] == "Open" else 1,
            )

            save_job = st.form_submit_button(
                "Save Changes",
                type="primary",
            )

            if save_job:
                with get_connection() as conn:
                    conn.execute(
                        """
                        UPDATE jobs
                        SET title=?,
                            department=?,
                            location=?,
                            employment_type=?,
                            experience_required=?,
                            required_skills=?,
                            description=?,
                            status=?
                        WHERE id=?
                        """,
                        (
                            edit_title,
                            edit_department,
                            edit_location,
                            edit_type,
                            edit_experience,
                            edit_skills,
                            edit_description,
                            edit_status,
                            job_id,
                        ),
                    )

                st.success("Job updated successfully.")
                st.rerun()


elif page == "Applications":
    st.title("Application Tracking")
    st.caption("Manage applications, hiring stages, and recruiter notes.")

    # ---------- CREATE APPLICATION ----------
    with st.expander("➕ Create Application", expanded=False):
        candidates = fetch_dataframe(
            "SELECT id, name, email FROM candidates ORDER BY name"
        )
        open_jobs = fetch_dataframe(
            """
            SELECT id, title, department, location
            FROM jobs
            WHERE status = 'Open'
            ORDER BY title
            """
        )

        if candidates.empty:
            st.info("Add a candidate before creating an application.")
        elif open_jobs.empty:
            st.info("Create an open job before creating an application.")
        else:
            candidate_options = {
                f"{row['name']} (ID: {row['id']})": int(row["id"])
                for _, row in candidates.iterrows()
            }
            job_options = {
                f"{row['title']} — {row['location'] or 'Location not specified'} (ID: {row['id']})":
                    int(row["id"])
                for _, row in open_jobs.iterrows()
            }

            with st.form("create_application_form"):
                selected_candidate = st.selectbox(
                    "Candidate",
                    list(candidate_options.keys()),
                )
                selected_job = st.selectbox(
                    "Open Job",
                    list(job_options.keys()),
                )
                initial_notes = st.text_area("Recruiter Notes (optional)")

                create_application = st.form_submit_button(
                    "Create Application",
                    type="primary",
                )

                if create_application:
                    candidate_id = candidate_options[selected_candidate]
                    job_id = job_options[selected_job]

                    try:
                        with get_connection() as conn:
                            cursor = conn.execute(
                                """
                                INSERT INTO applications
                                    (candidate_id, job_id, stage, recruiter_notes)
                                VALUES (?, ?, 'Applied', ?)
                                """,
                                (
                                    candidate_id,
                                    job_id,
                                    initial_notes.strip(),
                                ),
                            )
                            application_id = cursor.lastrowid

                            conn.execute(
                                """
                                INSERT INTO stage_history
                                    (application_id, from_stage, to_stage, notes)
                                VALUES (?, NULL, 'Applied', ?)
                                """,
                                (
                                    application_id,
                                    initial_notes.strip() or "Application created",
                                ),
                            )

                        st.success("Application created successfully.")
                        st.rerun()

                    except Exception as exc:
                        if "UNIQUE constraint failed" in str(exc):
                            st.error(
                                "This candidate has already applied "
                                "for this job."
                            )
                        else:
                            st.error(f"Could not create application: {exc}")

    st.divider()

    # ---------- APPLICATION LIST ----------
    st.subheader("All Applications")

    search_application = st.text_input(
        "Search applications",
        placeholder="Search by candidate, email, or job title",
        key="application_search",
    )

    applications_df = fetch_dataframe(
        """
        SELECT
            a.id AS application_id,
            c.name AS candidate,
            c.email AS email,
            j.title AS job,
            a.stage AS stage,
            a.ai_score AS ai_score,
            a.recruiter_notes AS recruiter_notes,
            a.applied_at AS applied_at,
            a.updated_at AS updated_at
        FROM applications a
        JOIN candidates c ON c.id = a.candidate_id
        JOIN jobs j ON j.id = a.job_id
        WHERE c.name LIKE ?
           OR COALESCE(c.email, '') LIKE ?
           OR j.title LIKE ?
        ORDER BY a.id DESC
        """,
        tuple([f"%{search_application}%"] * 3),
    )

    total_applications = len(applications_df)
    interview_total = (
        int((applications_df["stage"] == "Interview").sum())
        if total_applications else 0
    )
    offer_total = (
        int((applications_df["stage"] == "Offer").sum())
        if total_applications else 0
    )
    hired_total = (
        int((applications_df["stage"] == "Hired").sum())
        if total_applications else 0
    )

    metric_cols = st.columns(4)
    metric_cols[0].metric("Applications", total_applications)
    metric_cols[1].metric("Interviews", interview_total)
    metric_cols[2].metric("Offers", offer_total)
    metric_cols[3].metric("Hired", hired_total)

    if applications_df.empty:
        st.info("No applications found. Create one above.")
    else:
        st.dataframe(
            applications_df,
            width="stretch",
            hide_index=True,
            column_config={
                "application_id": st.column_config.NumberColumn("Application ID"),
                "candidate": st.column_config.TextColumn("Candidate"),
                "email": st.column_config.TextColumn("Email"),
                "job": st.column_config.TextColumn("Job"),
                "stage": st.column_config.TextColumn("Hiring Stage"),
                "ai_score": st.column_config.NumberColumn(
                    "AI Match Score",
                    format="%.1f",
                ),
                "recruiter_notes": st.column_config.TextColumn("Recruiter Notes"),
                "applied_at": st.column_config.TextColumn("Applied On"),
                "updated_at": st.column_config.TextColumn("Last Updated"),
            },
        )

        st.divider()

        # ---------- UPDATE STAGE AND NOTES ----------
        st.subheader("Update Application")

        application_options = {
            f"#{int(row['application_id'])} — {row['candidate']} / {row['job']}":
                int(row["application_id"])
            for _, row in applications_df.iterrows()
        }

        selected_application_label = st.selectbox(
            "Select application",
            list(application_options.keys()),
        )
        application_id = application_options[selected_application_label]

        application = fetch_dataframe(
            "SELECT * FROM applications WHERE id = ?",
            (application_id,),
        ).iloc[0]

        current_stage = str(application["stage"])
        stage_options = list(HIRING_STAGES)

        if current_stage not in stage_options:
            stage_options.append(current_stage)

        stage_index = stage_options.index(current_stage)

        with st.form("update_application_form"):
            new_stage = st.selectbox(
                "Hiring Stage",
                stage_options,
                index=stage_index,
            )

            new_notes = st.text_area(
                "Recruiter Notes",
                value=str(application["recruiter_notes"] or ""),
                help="Record interview feedback or recruitment updates.",
            )

            update_application = st.form_submit_button(
                "Save Application Changes",
                type="primary",
            )

            if update_application:
                try:
                    with get_connection() as conn:
                        if new_stage != current_stage:
                            conn.execute(
                                """
                                INSERT INTO stage_history
                                    (application_id, from_stage, to_stage, notes)
                                VALUES (?, ?, ?, ?)
                                """,
                                (
                                    application_id,
                                    current_stage,
                                    new_stage,
                                    new_notes.strip(),
                                ),
                            )

                        conn.execute(
                            """
                            UPDATE applications
                            SET stage = ?,
                                recruiter_notes = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                            """,
                            (
                                new_stage,
                                new_notes.strip(),
                                application_id,
                            ),
                        )

                    st.success("Application updated successfully.")
                    st.rerun()

                except Exception as exc:
                    st.error(f"Could not update application: {exc}")

        # ---------- STAGE HISTORY ----------
        with st.expander("View Hiring Stage History"):
            history_df = fetch_dataframe(
                """
                SELECT from_stage, to_stage, notes, changed_at
                FROM stage_history
                WHERE application_id = ?
                ORDER BY id DESC
                """,
                (application_id,),
            )

            if history_df.empty:
                st.info("No stage history recorded yet.")
            else:
                st.dataframe(
                    history_df,
                    width="stretch",
                    hide_index=True,
                )

