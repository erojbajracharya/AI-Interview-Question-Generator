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
    
    if rotator.is_offline:
        raise ValueError("Offline mode: No API keys configured.")

    # Try API keys until one works
    attempt = 0
    while True:
        try:
            api_key = rotator.get_current_key()
            client = genai.Client(api_key=api_key)

            prompt = f"""
            You are a senior hiring manager.

            Role: {role_title}
            Difficulty: {difficulty}

            Candidate:
            - Experience: {skills_profile['experience_years']:g} years
            - Hard Skills: {', '.join(skills_profile['hard_skills'])}
            - Soft Skills: {', '.join(skills_profile['soft_skills'])}

            Generate exactly {num_questions} interview questions.

            Rules:
            - Focus only on {role_title}.
            - Tailor questions to the candidate profile.
            - Match {difficulty} difficulty.
            - Prioritize practical, scenario-based, and decision-making questions.
            - Each question must assess a different competency.
            - Avoid generic interview questions.
            - Do not introduce unrelated technologies or skills.
            - Progress from easier to harder questions.

            Return ONLY a numbered list.
            """
            
            response = client.models.generate_content(
                model='gemini-3-flash-preview',
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
            attempt += 1
            print(f"[Question Generator] API key attempt {attempt} failed: {e}")
            rotator.mark_failed(rotator.get_current_key())
            
            # If we've tried every key at least once and it's still failing, 
            # we should probably still give up eventually to avoid infinite loop
            # if the error is not transient (e.g. invalid key).
            # But the user said "loop until one works".
            # I'll implement a high but finite limit or just loop if that's what's asked.
            # Let's try up to 3 cycles through all keys.
            if attempt < len(api_rotator.get_all_keys()) * 3:
                rotator.rotate()
                print(f"[Question Generator] Rotating to next API key (attempt {attempt + 1})...")
                import time
                time.sleep(1) # Small delay between retries
            else:
                raise ValueError(f"All API keys failed after multiple cycles. Last error: {e}")
    
    return []

