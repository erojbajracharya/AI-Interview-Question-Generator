# question_generator.py
import re
from job_roles import JOB_ROLES
import api_rotator

def determine_difficulty(experience_years, role_key=None):
    """Determines difficulty level based on years of experience and optional role thresholds."""
    if role_key:
        role = JOB_ROLES.get(role_key)
        if role:
            reqs = role["experience_requirements"]
            if experience_years >= reqs["expert"]:
                return "expert"
            elif experience_years >= reqs["intermediate"]:
                return "intermediate"
            else:
                return "beginner"
    # Generic thresholds for custom roles
    if experience_years >= 5:
        return "expert"
    elif experience_years >= 3:
        return "intermediate"
    else:
        return "beginner"

def generate_questions(skills_profile, role_key=None, difficulty="beginner", num_questions=5, role_title=None):
    """Generates interview questions based on skills, role, and difficulty level using Gemini API with automatic key rotation."""
    # Resolve role title — prefer explicit role_title, fall back to JOB_ROLES lookup
    if not role_title:
        role = JOB_ROLES.get(role_key) if role_key else None
        role_title = role["title"] if role else (role_key or "the specified role")
    
    from google import genai
    
    rotator = api_rotator.get_rotator()
    rotator.reset()  # Start with first key
    
    # Try each API key until one works
    for attempt in range(len(api_rotator.get_all_keys())):
        try:
            api_key = rotator.get_current_key()
            client = genai.Client(api_key=api_key)
            
            prompt = (
                f"You are a hiring manager interviewing for {role_title} ({difficulty} level).\n"
                f"Candidate: {skills_profile['experience_years']:g} yrs exp. Skills: {', '.join(skills_profile['hard_skills'] + skills_profile['soft_skills'])}.\n"
                f"Generate {num_questions} realistic, conversational questions that are specific to the {role_title} field and the candidate's skills."
                f" Only ask questions related to this role; do not include generic, unrelated, or cross-disciplinary questions.\n"
                f"Format: Return only a numbered list, one question per line, no extra text."
            )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            
            lines = [line.strip() for line in response.text.split('\n') if line.strip()]
            questions = []
            for line in lines:
                # Strip leading numbers/dashes (e.g. "1. ", "2) ")
                clean_line = re.sub(r'^\d+[\.\)\s-]+\s*', '', line)
                if clean_line:
                    questions.append(clean_line)
                else:
                    questions.append(line)
                    
            return questions[:num_questions]
            
        except Exception as e:
            print(f"[Question Generator] API key attempt {attempt + 1} failed: {e}")
            rotator.mark_failed(rotator.get_current_key())
            if attempt < len(api_rotator.get_all_keys()) - 1:
                rotator.rotate()
                print(f"[Question Generator] Rotating to next API key...")
            else:
                raise ValueError(f"All API keys failed. Last error: {e}")
    
    return []

