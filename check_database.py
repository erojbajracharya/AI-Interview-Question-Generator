# check_database.py
import mysql.connector
from db_helper import DB_CONFIG

def check_stored_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("\n=== DATABASE STORAGE REPORT ===\n")
        
        # 1. Candidates
        cursor.execute("SELECT COUNT(*) FROM Candidates")
        candidates_count = cursor.fetchone()[0]
        print(f"Candidates registered: {candidates_count}")

        # 2. Skills
        cursor.execute("SELECT COUNT(*) FROM Skills")
        skills_count = cursor.fetchone()[0]
        print(f"Skills extracted:      {skills_count}")

        # 3. Sessions
        cursor.execute("SELECT COUNT(*) FROM InterviewSessions")
        sessions_count = cursor.fetchone()[0]
        print(f"Interview Sessions:    {sessions_count}")

        # 4. Questions
        cursor.execute("SELECT COUNT(*) FROM Questions")
        questions_count = cursor.fetchone()[0]
        print(f"Questions Generated:   {questions_count}")

        # 5. Responses
        cursor.execute("SELECT COUNT(*) FROM Responses")
        responses_count = cursor.fetchone()[0]
        print(f"Answers/Responses:     {responses_count}")

        # 6. Summaries
        cursor.execute("SELECT COUNT(*) FROM InterviewSummary")
        summaries_count = cursor.fetchone()[0]
        print(f"Evaluation Summaries:  {summaries_count}")

        # 7. Stored Questions Pool
        cursor.execute("SELECT COUNT(*) FROM StoredQuestions")
        stored_questions_count = cursor.fetchone()[0]
        print(f"Stored Questions (Pool): {stored_questions_count}")

        if candidates_count > 0:
            print("\n--- Recent Candidates ---")
            cursor.execute("SELECT candidate_id, full_name, email, experience_years FROM Candidates ORDER BY candidate_id DESC LIMIT 5")
            for cid, name, email, exp in cursor.fetchall():
                print(f"ID: {cid} | Name: {name} | Email: {email} | Exp: {exp} years")

        if sessions_count > 0:
            print("\n--- Recent Sessions & Scores ---")
            query = """
                SELECT s.session_id, c.full_name, s.job_role, s.difficulty, sum.overall_score
                FROM InterviewSessions s
                JOIN Candidates c ON s.candidate_id = c.candidate_id
                LEFT JOIN InterviewSummary sum ON s.session_id = sum.session_id
                ORDER BY s.session_id DESC LIMIT 5
            """
            cursor.execute(query)
            for sid, name, role, diff, score in cursor.fetchall():
                score_str = f"{score}/10" if score is not None else "In Progress"
                print(f"Session {sid} | Candidate: {name} | Role: {role} ({diff}) | Score: {score_str}")

        if stored_questions_count > 0:
            print("\n--- Recent Stored Questions in Pool (Sample) ---")
            cursor.execute("SELECT id, job_role, difficulty, question FROM StoredQuestions ORDER BY id DESC LIMIT 5")
            for qid, role, diff, q in cursor.fetchall():
                print(f"ID: {qid} | Role: {role} ({diff}) | Q: {q[:60]}...")

        print("\n================================")
        cursor.close()
        conn.close()
    except Exception as e:
         print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_stored_data()
