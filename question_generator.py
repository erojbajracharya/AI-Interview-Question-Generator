# question_generator.py
import os
import re
from job_roles import JOB_ROLES
import api_rotator

def determine_difficulty(experience_years, role_key):
    """Determines difficulty level based on years of experience and role thresholds."""
    role = JOB_ROLES.get(role_key)
    if not role:
        return "beginner"
    
    reqs = role["experience_requirements"]
    if experience_years >= reqs["expert"]:
        return "expert"
    elif experience_years >= reqs["intermediate"]:
        return "intermediate"
    else:
        return "beginner"

def generate_questions(skills_profile, role_key, difficulty, num_questions=5):
    """Generates interview questions based on skills, role, and difficulty level using Gemini API with automatic key rotation."""
    role = JOB_ROLES.get(role_key)
    if not role:
        return []
    
    from google import genai
    
    rotator = api_rotator.get_rotator()
    rotator.reset()  # Start with first key
    
    # Try each API key until one works
    for attempt in range(len(api_rotator.get_all_keys())):
        try:
            api_key = rotator.get_current_key()
            client = genai.Client(api_key=api_key)
            
            prompt = (
                f"You are a hiring manager interviewing for {role['title']} ({difficulty} level).\n"
                f"Candidate: {skills_profile['experience_years']:g} yrs exp. Skills: {', '.join(skills_profile['hard_skills'] + skills_profile['soft_skills'])}.\n"
                f"Generate {num_questions} realistic, conversational questions (mix of technical and behavioral scenarios) as in a live interview simulation.\n"
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
