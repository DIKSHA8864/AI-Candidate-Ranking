
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Project root: the folder containing app.py
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "ats.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)

HIRING_STAGES = [
    "Applied",
    "Screening",
    "Shortlisted",
    "Interview",
    "Offer",
    "Hired",
    "Rejected",
    "Withdrawn",
]


@contextmanager
def get_connection():
    """Open a database connection and manage its lifecycle."""
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    """Create all ATS tables if they do not already exist."""

    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                location TEXT,
                skills TEXT DEFAULT '',
                experience_years REAL DEFAULT 0,
                summary TEXT DEFAULT '',
                resume_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                department TEXT DEFAULT '',
                location TEXT DEFAULT '',
                employment_type TEXT DEFAULT 'Full-time',
                experience_required REAL DEFAULT 0,
                required_skills TEXT DEFAULT '',
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'Open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                stage TEXT NOT NULL DEFAULT 'Applied',
                ai_score REAL,
                recruiter_notes TEXT DEFAULT '',
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(candidate_id, job_id),
                FOREIGN KEY(candidate_id)
                    REFERENCES candidates(id) ON DELETE CASCADE,
                FOREIGN KEY(job_id)
                    REFERENCES jobs(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS stage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                from_stage TEXT,
                to_stage TEXT NOT NULL,
                notes TEXT DEFAULT '',
                changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(application_id)
                    REFERENCES applications(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                scheduled_at TEXT,
                interviewer TEXT DEFAULT '',
                feedback TEXT DEFAULT '',
                outcome TEXT DEFAULT 'Pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(application_id)
                    REFERENCES applications(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_applications_stage
            ON applications(stage);

            CREATE INDEX IF NOT EXISTS idx_applications_job
            ON applications(job_id);

            CREATE INDEX IF NOT EXISTS idx_applications_candidate
            ON applications(candidate_id);
        """)


def seed_demo_data():
    """Add sample records only when the database is empty."""

    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM candidates"
        ).fetchone()[0]

        if count > 0:
            return

        candidates = [
            (
                "Aarav Sharma",
                "aarav.demo@example.com",
                "9000000001",
                "Lucknow",
                "Python, SQL, Machine Learning",
                2,
                "Python developer with machine learning experience."
            ),
            (
                "Priya Singh",
                "priya.demo@example.com",
                "9000000002",
                "Noida",
                "Python, NLP, RAG, FastAPI",
                3,
                "AI engineer experienced in NLP and retrieval systems."
            ),
            (
                "Rahul Verma",
                "rahul.demo@example.com",
                "9000000003",
                "Gurgaon",
                "React, JavaScript, SQL",
                1,
                "Frontend developer with React and database skills."
            ),
        ]

        conn.executemany("""
            INSERT INTO candidates
            (name, email, phone, location, skills,
             experience_years, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, candidates)

        jobs = [
            (
                "AI Engineer",
                "Engineering",
                "Noida",
                "Full-time",
                1,
                "Python, NLP, RAG, Machine Learning",
                "Build AI-powered applications and retrieval systems."
            ),
            (
                "Frontend Developer",
                "Engineering",
                "Gurgaon",
                "Full-time",
                0,
                "React, JavaScript, HTML, CSS",
                "Develop responsive user interfaces."
            ),
        ]

        conn.executemany("""
            INSERT INTO jobs
            (title, department, location, employment_type,
             experience_required, required_skills, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, jobs)

        conn.execute("""
            INSERT INTO applications (candidate_id, job_id, stage)
            VALUES (1, 1, 'Screening')
        """)

        conn.execute("""
            INSERT INTO applications (candidate_id, job_id, stage)
            VALUES (2, 1, 'Interview')
        """)

        conn.execute("""
            INSERT INTO applications (candidate_id, job_id, stage)
            VALUES (3, 2, 'Applied')
        """)

        # Record initial stage history for demo applications.
        conn.execute("""
            INSERT INTO stage_history
            (application_id, from_stage, to_stage, notes)
            VALUES (1, 'Applied', 'Screening', 'Demo record')
        """)

        conn.execute("""
            INSERT INTO stage_history
            (application_id, from_stage, to_stage, notes)
            VALUES (2, 'Applied', 'Interview', 'Demo record')
        """)

        conn.execute("""
            INSERT INTO stage_history
            (application_id, from_stage, to_stage, notes)
            VALUES (3, NULL, 'Applied', 'Demo record')
        """)


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print(f"ATS database initialized: {DB_PATH}")
