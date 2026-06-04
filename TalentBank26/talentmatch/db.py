import contextlib
import os
import sqlite3

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "talentmatch.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('candidate', 'employer', 'university')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            full_name TEXT DEFAULT '',
            title TEXT DEFAULT '',
            about TEXT DEFAULT '',
            skills TEXT DEFAULT '[]',
            certifications TEXT DEFAULT '[]',
            accomplishments TEXT DEFAULT '[]',
            questionnaire_data TEXT DEFAULT '{}',
            questionnaire_completed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employer_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            company TEXT DEFAULT '',
            description TEXT DEFAULT '',
            required_skills TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employer_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            employer_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected')),
            match_score REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            FOREIGN KEY (employer_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS university_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            university_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            alert_type TEXT DEFAULT 'info',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (university_id) REFERENCES users(id)
        );
    """)
    with contextlib.suppress(BaseException):
        cursor.execute(
            "ALTER TABLE candidates ADD COLUMN questionnaire_data TEXT DEFAULT '{}'"
        )
    with contextlib.suppress(BaseException):
        cursor.execute(
            "ALTER TABLE candidates ADD COLUMN questionnaire_completed INTEGER DEFAULT 0"
        )
    conn.commit()
    conn.close()
