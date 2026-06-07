# question_generator.py
import os
import re
from job_roles import JOB_ROLES

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
    """Generates interview questions based on skills, role, and difficulty level using Gemini API."""
    role = JOB_ROLES.get(role_key)
    if not role:
        return []
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Gemini API key is required. Please set the GEMINI_API_KEY environment variable.")
    
    from google import genai
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
