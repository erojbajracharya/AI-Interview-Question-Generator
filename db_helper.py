# db_helper.py
"""
MySQL Database Helper for the AI Interview Question Generator.
Provides functions to save and retrieve data for each stage of the
interview workflow: candidate → skills → session → questions → responses → summary.

Requirements:
    pip install mysql-connector-python
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime


# ── Database connection settings ─────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",        # ← Set your MySQL root password here
    "database": "ai_interview_db"
}

_db_initialized = False  # Track whether we've already checked/created the DB


def initialize_database():
    """Create the database and all tables if they do not already exist."""
    global _db_initialized
    if _db_initialized:
        return True

    try:
        # Step 1 – Connect to MySQL server (no database selected)
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()

        # Step 2 – Create the database
        cursor.execute("CREATE DATABASE IF NOT EXISTS ai_interview_db")
        cursor.execute("USE ai_interview_db")

        # Step 3 – Create all tables
        table_statements = [
            """
            CREATE TABLE IF NOT EXISTS Candidates (
                candidate_id    INT AUTO_INCREMENT PRIMARY KEY,
                full_name       VARCHAR(100)  NOT NULL,
                email           VARCHAR(100)  UNIQUE,
                phone           VARCHAR(20),
                education       VARCHAR(255),
                experience_years INT DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Skills (
                skill_id      INT AUTO_INCREMENT PRIMARY KEY,
                candidate_id  INT NOT NULL,
                skill_name    VARCHAR(100) NOT NULL,
                skill_type    ENUM('Hard Skill', 'Soft Skill') NOT NULL,
                FOREIGN KEY (candidate_id) REFERENCES Candidates(candidate_id)
                    ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS InterviewSessions (
                session_id      INT AUTO_INCREMENT PRIMARY KEY,
                candidate_id    INT NOT NULL,
                job_role        VARCHAR(100) NOT NULL,
                difficulty      ENUM('Easy', 'Medium', 'Hard') NOT NULL,
                interview_date  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES Candidates(candidate_id)
                    ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Questions (
                question_id     INT AUTO_INCREMENT PRIMARY KEY,
                question_text   TEXT NOT NULL,
                difficulty      ENUM('Easy', 'Medium', 'Hard') NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Responses (
                response_id   INT AUTO_INCREMENT PRIMARY KEY,
                session_id    INT NOT NULL,
                question_id   INT NOT NULL,
                answer_text   TEXT NOT NULL,
                FOREIGN KEY (session_id)  REFERENCES InterviewSessions(session_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES Questions(question_id)
                    ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS InterviewSummary (
                summary_id      INT AUTO_INCREMENT PRIMARY KEY,
                session_id      INT NOT NULL UNIQUE,
                overall_score   DECIMAL(5,2),
                strengths       TEXT,
                weaknesses      TEXT,
                final_feedback  TEXT,
                FOREIGN KEY (session_id) REFERENCES InterviewSessions(session_id)
                    ON DELETE CASCADE
            )
            """
        ]

        for stmt in table_statements:
            cursor.execute(stmt)

        conn.commit()
        cursor.close()
        conn.close()

        _db_initialized = True
        print("[DB] Database 'ai_interview_db' is ready (created if it did not exist).")
        return True

    except Error as e:
        print(f"[DB ERROR] Could not initialize database: {e}")
        return False


def get_connection():
    """Create and return a MySQL database connection, auto-creating the DB if needed."""
    initialize_database()
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] Could not connect to MySQL: {e}")
        return None


# ── 1. Candidates ────────────────────────────────────────────────────────────

def save_candidate(full_name, email=None, phone=None, education=None, experience_years=0):
    """Insert a new candidate or retrieve existing one if email duplicates, and return candidate_id."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO Candidates (full_name, email, phone, education, experience_years)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (full_name, email, phone, education, experience_years))
        conn.commit()
        candidate_id = cursor.lastrowid
        print(f"[DB] Candidate saved  →  candidate_id = {candidate_id}")
        return candidate_id
    except Error as e:
        if e.errno == 1062 and email:  # Duplicate entry error code
            try:
                sql_select = "SELECT candidate_id FROM Candidates WHERE email = %s"
                cursor.execute(sql_select, (email,))
                result = cursor.fetchone()
                if result:
                    candidate_id = result[0]
                    print(f"[DB] Existing candidate found with email '{email}'  →  candidate_id = {candidate_id}")
                    return candidate_id
            except Error as select_error:
                print(f"[DB ERROR] Failed to fetch existing candidate: {select_error}")
        print(f"[DB ERROR] save_candidate: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_candidate(candidate_id):
    """Retrieve a candidate record by ID."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Candidates WHERE candidate_id = %s", (candidate_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"[DB ERROR] get_candidate: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


# ── 2. Skills ────────────────────────────────────────────────────────────────

def save_skills(candidate_id, hard_skills, soft_skills):
    """
    Bulk-insert extracted skills for a candidate. Deletes old skills first to avoid duplication.

    Parameters:
        candidate_id : int
        hard_skills  : list[str]  – e.g. ["python", "sql", "docker"]
        soft_skills  : list[str]  – e.g. ["teamwork", "communication"]
    """
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        # Delete existing skills for candidate to clean up duplicates
        cursor.execute("DELETE FROM Skills WHERE candidate_id = %s", (candidate_id,))
        
        sql = "INSERT INTO Skills (candidate_id, skill_name, skill_type) VALUES (%s, %s, %s)"

        rows = []
        for skill in hard_skills:
            rows.append((candidate_id, skill, "Hard Skill"))
        for skill in soft_skills:
            rows.append((candidate_id, skill, "Soft Skill"))

        if rows:
            cursor.executemany(sql, rows)
        conn.commit()
        print(f"[DB] {len(rows)} skills saved for candidate_id = {candidate_id}")
    except Error as e:
        print(f"[DB ERROR] save_skills: {e}")
    finally:
        cursor.close()
        conn.close()


def get_skills(candidate_id):
    """Retrieve all skills for a candidate."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Skills WHERE candidate_id = %s", (candidate_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] get_skills: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ── 3. Interview Sessions ───────────────────────────────────────────────────

def create_session(candidate_id, job_role, difficulty):
    """Start a new interview session and return the session_id."""
    # Map project difficulty levels to the ENUM values in the DB
    difficulty_map = {
        "beginner": "Easy",
        "intermediate": "Medium",
        "expert": "Hard",
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
    }
    db_difficulty = difficulty_map.get(difficulty.lower(), "Medium")

    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO InterviewSessions (candidate_id, job_role, difficulty, interview_date)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (candidate_id, job_role, db_difficulty, datetime.now()))
        conn.commit()
        session_id = cursor.lastrowid
        print(f"[DB] Interview session created  →  session_id = {session_id}")
        return session_id
    except Error as e:
        print(f"[DB ERROR] create_session: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_session(session_id):
    """Retrieve a session record by ID."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM InterviewSessions WHERE session_id = %s", (session_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"[DB ERROR] get_session: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


# ── 4. Questions ─────────────────────────────────────────────────────────────

def save_questions(question_texts, difficulty):
    """
    Bulk-insert generated questions and return a list of question_ids.

    Parameters:
        question_texts : list[str]  – the generated question strings
        difficulty     : str        – "Easy", "Medium", or "Hard"
    Returns:
        list[int] – corresponding question_ids
    """
    # Map project difficulty levels to the ENUM values in the DB
    difficulty_map = {
        "beginner": "Easy",
        "intermediate": "Medium",
        "expert": "Hard",
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
    }
    db_difficulty = difficulty_map.get(difficulty.lower(), "Medium")

    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO Questions (question_text, difficulty) VALUES (%s, %s)"

        question_ids = []
        for text in question_texts:
            cursor.execute(sql, (text, db_difficulty))
            question_ids.append(cursor.lastrowid)

        conn.commit()
        print(f"[DB] {len(question_ids)} questions saved")
        return question_ids
    except Error as e:
        print(f"[DB ERROR] save_questions: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ── 5. Responses ─────────────────────────────────────────────────────────────

def save_responses(session_id, question_ids, answer_texts):
    """
    Bulk-insert candidate responses for a session.

    Parameters:
        session_id   : int
        question_ids : list[int]
        answer_texts : list[str]
    """
    conn = get_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO Responses (session_id, question_id, answer_text)
            VALUES (%s, %s, %s)
        """
        rows = [(session_id, qid, ans) for qid, ans in zip(question_ids, answer_texts)]
        cursor.executemany(sql, rows)
        conn.commit()
        print(f"[DB] {len(rows)} responses saved for session_id = {session_id}")
    except Error as e:
        print(f"[DB ERROR] save_responses: {e}")
    finally:
        cursor.close()
        conn.close()


# ── 6. Interview Summary ────────────────────────────────────────────────────

def save_summary(session_id, overall_score, strengths, weaknesses, final_feedback):
    """Insert the final interview evaluation summary for a session."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO InterviewSummary (session_id, overall_score, strengths, weaknesses, final_feedback)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (session_id, overall_score, strengths, weaknesses, final_feedback))
        conn.commit()
        summary_id = cursor.lastrowid
        print(f"[DB] Summary saved  →  summary_id = {summary_id}")
        return summary_id
    except Error as e:
        print(f"[DB ERROR] save_summary: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_summary(session_id):
    """Retrieve the interview summary for a given session."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM InterviewSummary WHERE session_id = %s", (session_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"[DB ERROR] get_summary: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


# ── Full Workflow Demo ───────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  DB Helper – Quick Integration Test")
    print("=" * 60)

    # 1. Save a test candidate
    cid = save_candidate(
        full_name="Navaraj Thapa",
        email="navaraj@example.com",
        phone="9841000000",
        education="Bachelor in Computer Science",
        experience_years=3
    )

    if cid:
        # 2. Save skills
        save_skills(cid, ["python", "sql", "docker"], ["teamwork", "communication"])

        # 3. Create session
        sid = create_session(cid, "Software Engineer", "Intermediate")

        if sid:
            # 4. Save questions
            sample_qs = [
                "Explain the difference between a list and a tuple in Python.",
                "How do you handle version control in a team environment?"
            ]
            qids = save_questions(sample_qs, "intermediate")

            # 5. Save responses
            sample_answers = [
                "A list is mutable while a tuple is immutable.",
                "We use Git with feature branches and pull requests."
            ]
            save_responses(sid, qids, sample_answers)

            # 6. Save summary
            save_summary(
                session_id=sid,
                overall_score=7.5,
                strengths="Good grasp of Python fundamentals",
                weaknesses="Needs deeper understanding of CI/CD pipelines",
                final_feedback="Recommended with additional training on DevOps."
            )

    print("\n✓ Integration test complete.")
