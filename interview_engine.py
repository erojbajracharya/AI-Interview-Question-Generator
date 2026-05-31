import os
import json
from parser import extract_text_from_pdf
from skill_extractor import extract_skills
from experience_extractor import determine_experience
from question_generator import generate_questions
from evaluator import evaluate_answer
from aggregator import generate_overall_assessment

class AIInterviewEngine:
    """
    Orchestrates the entire AI Interview Question Generator workflow:
    1. Parses PDF resumes.
    2. Extracts candidate skills (hard and soft).
    3. Estimates experience levels.
    4. Generates custom interview questions via Gemini API.
    5. Evaluates candidate answers via Gemini API.
    6. Consolidates individual question evaluations into a final score report.
    """

    def process_candidate_resume(self, pdf_path: str) -> dict:
        """
        Parses a PDF resume to extract text, identify skills, and determine experience.

        Parameters:
            pdf_path (str): Path to the candidate's PDF resume.

        Returns:
            dict: Structured profile containing text, skills, and experience details.
        """
        print(f"[Engine] Parsing resume: {pdf_path}...")
        resume_text = extract_text_from_pdf(pdf_path)
        
        print("[Engine] Extracting candidate skills...")
        skills = extract_skills(resume_text)
        
        print("[Engine] Determining candidate experience level...")
        experience = determine_experience(resume_text)
        
        return {
            "resume_text": resume_text,
            "hard_skills": skills["hard_skills"],
            "soft_skills": skills["soft_skills"],
            "experience_years": experience["experience_years"],
            "experience_level": experience["experience_level"]
        }

    def generate_interview_questions(
        self, 
        profile: dict, 
        job_description: str, 
        difficulty_override: str = None,
        num_questions: int = 8
    ) -> list:
        """
        Generates custom interview questions for a candidate.

        Parameters:
            profile (dict): The candidate profile generated from process_candidate_resume.
            job_description (str): Target job requirements.
            difficulty_override (str): Force a difficulty tier ('Beginner', 'Intermediate', 'Expert').
                                        If None, uses the detected experience level.
            num_questions (int): Number of questions to generate.

        Returns:
            list: List of question dictionaries.
        """
        # Determine difficulty level (detected vs override)
        difficulty = difficulty_override if difficulty_override else profile["experience_level"]
        print(f"[Engine] Generating {num_questions} questions with difficulty: {difficulty}...")
        
        questions = generate_questions(
            hard_skills=profile["hard_skills"],
            soft_skills=profile["soft_skills"],
            job_description=job_description,
            difficulty_level=difficulty,
            num_questions=num_questions
        )
        return questions

    def evaluate_candidate_answer(self, question: str, answer: str) -> dict:
        """
        Evaluates a single answer given by the candidate.

        Parameters:
            question (str): The question asked.
            answer (str): The candidate's response.

        Returns:
            dict: Evaluation score, strengths, weaknesses, and suggestions.
        """
        print("[Engine] Evaluating response...")
        return evaluate_answer(question, answer)

    def generate_final_report(self, evaluations: list) -> dict:
        """
        Consolidates multiple single-question evaluations into a comprehensive final report.

        Parameters:
            evaluations (list): List of all question evaluations.

        Returns:
            dict: Overall score, tier, strengths, improvements list, and summary.
        """
        print("[Engine] Aggregating results and generating report...")
        return generate_overall_assessment(evaluations)


if __name__ == "__main__":
    # Integration test representing a complete mock interview session
    print("=== Testing Complete AI Interview Engine ===")
    
    engine = AIInterviewEngine()
    
    # 1. Parse and extract candidate profile from local pdf
    pdf_file = "Project Documentation.pdf"
    job_desc = (
        "Looking for a Python Software Engineer with experience in building data extraction pipelines, "
        "REST APIs using Flask or Django, and Docker containerization."
    )
    
    if os.path.exists(pdf_file):
        try:
            profile = engine.process_candidate_resume(pdf_file)
            print("\nCandidate Profile:")
            print(f"- Detected Level: {profile['experience_level']} ({profile['experience_years']} years)")
            print(f"- Hard Skills: {profile['hard_skills']}")
            print(f"- Soft Skills: {profile['soft_skills']}")
            
            # Show how question generation would be called
            print("\nAPI Question Generation Setup:")
            print(f"Would invoke generate_interview_questions for difficulty: {profile['experience_level']}")
            
        except Exception as e:
            print(f"Error during integration test: {e}")
    else:
        print(f"Test pdf file '{pdf_file}' not found. Please place a test PDF in the directory.")
