
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
    st.title("Candidates")
    st.write(
        "Candidate management will be implemented in Step 4. "
        "The database is already connected."
    )

    st.metric(
        "Total Candidates",
        get_count("SELECT COUNT(*) FROM candidates"),
    )

elif page == "Jobs":
    st.title("Job Management")
    st.write(
        "Job creation and editing will be implemented in a later step."
    )

    st.metric(
        "Total Jobs",
        get_count("SELECT COUNT(*) FROM jobs"),
    )

elif page == "Applications":
    st.title("Application Tracking")
    st.write(
        "Application management and hiring-stage updates will be "
        "implemented in a later step."
    )

    st.metric(
        "Total Applications",
        get_count("SELECT COUNT(*) FROM applications"),
    )
