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
        f"You are an expert interviewer. Generate a list of exactly {num_questions} interview questions "
        f"for a {role['title']} position at the '{difficulty}' level.\n"
        f"Candidate's Profile:\n"
        f"- Extracted Hard Skills: {', '.join(skills_profile['hard_skills'])}\n"
        f"- Extracted Soft Skills: {', '.join(skills_profile['soft_skills'])}\n"
        f"- Experience: {skills_profile['experience_years']} years\n\n"
        f"Requirements:\n"
        f"- A mix of technical/hard skill questions and behavioral/soft skill questions.\n"
        f"Format: Return only the numbered list of {num_questions} questions, one per line. No introduction, no other text."
        f"evaluate score accurately based on the answer, if it is rubbish give 0 out of 10."
    )
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    lines = [line.strip() for line in response.text.split('\n') if line.strip()]
    questions = []
    for line in lines:
        # Strip leading numbers/dashes if any
        clean_line = re.sub(r'^\d+[\.\)\s-]+\s*', '', line)
        if clean_line:
            questions.append(clean_line)
        else:
            questions.append(line)
            
    return questions[:num_questions]
