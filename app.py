# app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

import db_helper as DB_MODULE
import resume_parser as RESUME_MODULE
import resume_screener as SCREENER_MODULE
import question_generator as QUESTION_MODULE
import final_report as REPORT_MODULE
import api_rotator as API_ROTATOR
from job_roles import JOB_ROLES

app = Flask(__name__)
# Enable CORS so the React app running on port 5173 can query this backend on port 5000
CORS(app)

# Create a temporary directory inside the workspace for upload files
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize database tables on server start
DB_MODULE.initialize_database()

@app.route("/api/roles", methods=["GET"])
def get_roles():
    """Returns all available job roles."""
    roles_list = []
    for key, val in JOB_ROLES.items():
        roles_list.append({
            "key": key,
            "title": val["title"],
            "hard_skills": val["hard_skills"],
            "soft_skills": val["soft_skills"],
            "experience_requirements": val["experience_requirements"]
        })
    return jsonify({"success": True, "roles": roles_list})

@app.route("/api/screen", methods=["POST"])
def screen_resume():
    """Parses a resume PDF and runs simple linear regression screening."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded."}), 400
        
    file = request.files["file"]
    role_key = request.form.get("role_key") or None
    role_title = request.form.get("role_title") or None
    
    # Resolve role — use predefined title/thresholds if available
    role_info = JOB_ROLES.get(role_key) if role_key else None
    if not role_info and not role_title:
        return jsonify({"success": False, "error": "Must provide either a valid role_key or a role_title."}), 400
    
    if role_info:
        role_title = role_info["title"]
        # Use the actual role_info for screening
        role_dict_for_screening = role_info
    else:
        role_key = None  # no matching predefined role
        # For custom roles, use a skill-free dict so screening uses self-referenced resume skills
        role_dict_for_screening = {"title": role_title, "hard_skills": [], "soft_skills": []}
        
    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file."}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    
    try:
        # Save file locally inside the workspace temp folder
        file.save(file_path)
        
        # Parse resume content
        resume_data = RESUME_MODULE.parse_resume(file_path)
        
        # Determine difficulty based on experience years and role thresholds
        difficulty = QUESTION_MODULE.determine_difficulty(resume_data["experience_years"], role_key)
        
        resume_data.update({
            "difficulty": difficulty,
            "role_key": role_key or "custom",
            "role_title": role_title
        })
        
        # Save to Candidate database tables
        candidate_name = os.path.splitext(filename)[0].replace("_", " ").replace("Resume", "").strip() or "Candidate"
        email = f"{candidate_name.lower().replace(' ', '')}@example.com"
        
        candidate_id = DB_MODULE.save_candidate(
            full_name=candidate_name,
            email=email,
            experience_years=resume_data["experience_years"]
        )
        
        resume_data["candidate_id"] = candidate_id
        
        if candidate_id:
            DB_MODULE.save_skills(candidate_id, resume_data["hard_skills"], resume_data["soft_skills"])
            
        # Screen resume using simple linear regression (always dynamic: self-referenced skills)
        screening_result = SCREENER_MODULE.screen_resume(resume_data, role_key=role_key, role_dict=role_dict_for_screening)
        report_text = SCREENER_MODULE.format_screening_report(screening_result, role_title)
        
        response_data = {
            "success": True,
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "resume_data": {
                "experience_years": resume_data["experience_years"],
                "difficulty": difficulty,
                "hard_skills": resume_data["hard_skills"],
                "soft_skills": resume_data["soft_skills"],
                "role_key": resume_data["role_key"],
                "role_title": resume_data["role_title"]
            },
            "screening": {
                "match_score": screening_result["match_score"],
                "passed": screening_result["passed"],
                "report_text": report_text,
                "details": {
                    "hard_ratio": screening_result["details"]["hard_ratio"],
                    "soft_ratio": screening_result["details"]["soft_ratio"],
                    "exp_ratio": screening_result["details"]["exp_ratio"],
                    "hard_matched": screening_result["details"]["hard_matched"],
                    "hard_required": screening_result["details"]["hard_required"],
                    "soft_matched": screening_result["details"]["soft_matched"],
                    "soft_required": screening_result["details"]["soft_required"]
                }
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"[SCREENING ERROR] {e}")
        return jsonify({"success": False, "error": str(e)}), 500
        
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route("/api/interview/start", methods=["POST"])
def start_interview():
    """Generates questions using AI or loads previously saved questions from DB."""
    data = request.json or {}
    candidate_id = data.get("candidate_id")
    role_key = data.get("role_key") or None
    role_title = data.get("role_title") or None
    difficulty = data.get("difficulty")
    num_questions = int(data.get("num_questions", 5))
    source = data.get("source", "ai") # "ai" or "db"
    save_to_db = data.get("save_to_db", True)

    # Resolve role — use predefined title/thresholds if available, but never use hardcoded skill lists
    role_info = JOB_ROLES.get(role_key) if role_key else None
    if not role_info and not role_title:
        return jsonify({"success": False, "error": "Must provide either a valid role_key or a role_title."}), 400
    if role_info:
        role_title = role_info["title"]
    # role_info no longer used for skills — questions are always generated dynamically via role_title
    
    # Mock resume_data if we don't pass all details
    experience_years = float(data.get("experience_years", 0))
    hard_skills = data.get("hard_skills", [])
    soft_skills = data.get("soft_skills", [])
    
    resume_data = {
        "experience_years": experience_years,
        "hard_skills": hard_skills,
        "soft_skills": soft_skills,
        "role_key": role_key,
        "role_title": role_title,
        "difficulty": difficulty
    }

    questions_data = [] # Will contain objects: {"question_text": "...", "reference_answer": "..."}
    ai_success = False
    
    # Try AI Mode
    if source == "ai":
        try:
            raw_qs = QUESTION_MODULE.generate_questions(
                resume_data,
                role_key=role_key,
                difficulty=difficulty,
                num_questions=num_questions,
                role_title=role_title
            )
            if raw_qs:
                ai_success = True
                questions_data = [{"question_text": q, "reference_answer": None} for q in raw_qs]
        except Exception as e:
            print(f"[AI Start Error] {e}. Falling back to DB mode.")
            source = "db" # fallback to database

    # DB Mode
    if source == "db" or not questions_data:
        stored_qs = DB_MODULE.get_stored_questions(role_title, difficulty, limit=num_questions)
        questions_data = [
            {
                "question_text": q["question"],
                "reference_answer": q.get("answer") # Preserve reference answer!
            }
            for q in stored_qs
        ]
        
    if not questions_data:
        # Fallback: generate field-specific placeholder questions if both AI and DB failed
        placeholder_questions = [
            f"Tell me about your experience relevant to {role_title} and how it prepared you for this position.",
            f"What are the top challenges in {role_title} work, and how would you approach them?",
            f"Describe a project or task you've completed that is closely related to {role_title}.",
            f"Which tools, techniques, or processes do you rely on most when working in {role_title}?",
            f"How do you stay current with best practices and trends in {role_title}?"
        ]
        # Limit to the requested number of questions
        placeholder_questions = placeholder_questions[:num_questions]
        questions_data = [{"question_text": q, "reference_answer": None} for q in placeholder_questions]
    # No early return; continue processing with questions_data (whether from AI, DB, or placeholder)

    # Save generated AI questions to the reusable pool if requested
    if ai_success and save_to_db:
        for q_obj in questions_data:
            DB_MODULE.save_stored_question(
                job_role=role_title,
                difficulty=difficulty,
                topic="AI Generated",
                question=q_obj["question_text"],
                answer=None
            )

    # Save session records and questions to MySQL database
    session_id = None
    db_question_ids = []
    if candidate_id:
        session_id = DB_MODULE.create_session(candidate_id, role_title, difficulty)
        question_texts = [q["question_text"] for q in questions_data]
        db_question_ids = DB_MODULE.save_questions(question_texts, difficulty)
        
    # Return questions with DB question IDs mapped
    final_questions = []
    for idx, q_obj in enumerate(questions_data):
        final_questions.append({
            "question_id": db_question_ids[idx] if idx < len(db_question_ids) else None,
            "question_text": q_obj["question_text"],
            "reference_answer": q_obj["reference_answer"]
        })

    return jsonify({
        "success": True,
        "session_id": session_id,
        "questions": final_questions,
        "difficulty": difficulty
    })

@app.route("/api/interview/submit", methods=["POST"])
def submit_interview():
    """Grades all responses automatically, saves to DB and returns evaluation report."""
    data = request.json or {}
    session_id = data.get("session_id")
    questions = data.get("questions", []) # list of {"question_id": ..., "question_text": ..., "reference_answer": ...}
    answers = data.get("answers", []) # list of string responses
    role_key = data.get("role_key") or None
    role_title = data.get("role_title") or None
    difficulty = data.get("difficulty")
    hard_skills = data.get("hard_skills", [])

    # Resolve role — use predefined title if available, never use hardcoded skill lists
    predefined = JOB_ROLES.get(role_key) if role_key else None
    if predefined:
        role_title = predefined["title"]
    elif not role_title:
        return jsonify({"success": False, "error": "Must provide either a valid role_key or a role_title."}), 400
    # Always build a title-only role dict so grading is fully dynamic
    role_info = {"title": role_title, "hard_skills": [], "soft_skills": []}
    
    question_texts = [q["question_text"] for q in questions]
    question_ids = [q["question_id"] for q in questions]
    reference_answers = [q.get("reference_answer") for q in questions]

    try:
        # Grade candidate answers (utilizing automatic API key rotation)
        evaluations = REPORT_MODULE.grade_answers(
            questions=question_texts,
            answers=answers,
            role_info=role_info,
            difficulty=difficulty,
            reference_answers=reference_answers
        )

        # Calculate average score
        import re
        total_score = 0.0
        for eval_str in evaluations:
            match = re.search(r'Score[^\d]*(\d+(?:\.\d+)?)\s*/\s*10', eval_str, re.IGNORECASE)
            if match:
                try:
                    total_score += float(match.group(1))
                except ValueError:
                    total_score += 5.0
            else:
                # default to 5/10 if score can't be parsed
                total_score += 5.0
                
        avg_score = round(total_score / len(evaluations), 1) if evaluations else 0.0
        
        # Recommendations status
        if avg_score >= 8.0:
            status = "Highly Recommended!"
        elif avg_score >= 5.0:
            status = "Recommended with training"
        else:
            status = "Needs Improvement"

        # Save responses and summaries into MySQL
        if session_id:
            valid_qids = [qid for qid in question_ids if qid is not None]
            # Match lengths
            min_len = min(len(valid_qids), len(answers))
            DB_MODULE.save_responses(session_id, valid_qids[:min_len], answers[:min_len])
            
            skills_str = ", ".join(hard_skills)
            DB_MODULE.save_summary(
                session_id=session_id,
                overall_score=avg_score,
                strengths=f"Tuned to skills: {skills_str}" if skills_str else "Tuned to candidate profile",
                weaknesses=f"Level: {difficulty}",
                final_feedback=status
            )

        return jsonify({
            "success": True,
            "evaluations": evaluations,
            "overall_score": avg_score,
            "status": status,
            "feedback": status
        })
        
    except Exception as e:
        print(f"[SUBMIT ERROR] {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/history", methods=["GET"])
def get_history():
    """Retrieves list of past candidate sessions logs."""
    history = DB_MODULE.get_all_sessions()
    return jsonify({"success": True, "history": history})

@app.route("/api/history/<int:session_id>", methods=["GET"])
def get_session_detail(session_id):
    """Retrieves full details of a specific past session."""
    details = DB_MODULE.get_session_details(session_id)
    if not details:
        return jsonify({"success": False, "error": "Session details not found."}), 404
    return jsonify({"success": True, "details": details})


if __name__ == "__main__":
    print("Starting Flask Backend server on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
