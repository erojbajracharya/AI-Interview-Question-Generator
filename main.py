import os
import sys
sys.dont_write_bytecode = True
import json
from interview_engine import AIInterviewEngine

def run_interview_flow():
    # 1. Initialize the consolidated Interview Engine
    engine = AIInterviewEngine()

    # 2. Prompt the user for the resume file path
    resume_pdf_path = input("Enter the path to the candidate PDF resume: ").strip()
    if not resume_pdf_path:
        print("Error: Resume path cannot be empty.")
        return

    job_description = (
        "We are looking for a Python Software Engineer with skills in SQL databases "
        "and experience in containerized environments (Docker)."
    )

    print("=== Step 1: Parsing and Analyzing Resume ===")
    if not os.path.exists(resume_pdf_path):
        print(f"Error: The file '{resume_pdf_path}' does not exist.")
        return
    if not resume_pdf_path.lower().endswith('.pdf'):
        print(f"Error: The file '{resume_pdf_path}' is not a PDF.")
        return

    # Extract text, skills, and experience in one OOP call
    candidate_profile = engine.process_candidate_resume(resume_pdf_path)
    print(f"Detected Experience Level: {candidate_profile['experience_level']}")
    print(f"Detected Hard Skills: {candidate_profile['hard_skills']}")
    print(f"Detected Soft Skills: {candidate_profile['soft_skills']}\n")

    # 3. Ask how many questions to generate (minimum 2)
    try:
        num_questions_input = input("How many questions would you like to be generated for your interview? (default: 2): ")
        num_questions = int(num_questions_input) if num_questions_input.strip() else 2
    except ValueError:
        print("Invalid input. Defaulting to 2 questions.")
        num_questions = 2

    if num_questions < 2:
        print("Minimum number of questions is 2. Setting to 2.")
        num_questions = 2

    # 4. Generate Questions (requires GEMINI_API_KEY env variable)
    print("\n=== Step 2: Generating Interview Questions ===")
    if "GEMINI_API_KEY" not in os.environ:
        print("Skipping AI generation: GEMINI_API_KEY environment variable is not set.")
        print("Set it using: $env:GEMINI_API_KEY='your_key' (PowerShell) or export GEMINI_API_KEY='your_key' (Bash).\n")
        return

    try:
        questions = engine.generate_interview_questions(
            profile=candidate_profile, 
            job_description=job_description,
            num_questions=num_questions
        )
        print(f"Successfully generated {len(questions)} custom questions.\n")
    except Exception as e:
        print(f"Failed to generate questions: {e}")
        return

    # 5. Interactive interview loop and evaluation
    print("=== Step 3: Interactive Interview Session ===")
    evaluations = []
    
    for idx, q_item in enumerate(questions, 1):
        question_text = q_item.get("question", "No question text available.")
        question_type = q_item.get("type", "unknown")
        
        print(f"\n[Question {idx} of {len(questions)} ({question_type.capitalize()})]")
        print(f"Question: {question_text}")
        
        # Prompt user to input their answer
        candidate_answer = input("Your Answer: ")
        
        print("\nEvaluating your answer via Gemini API...")
        try:
            evaluation = engine.evaluate_candidate_answer(question_text, candidate_answer)
            evaluations.append(evaluation)
            
            print(f"Evaluation Score: {evaluation['score']}/10")
            print(f"Strengths: {evaluation['strengths']}")
            print(f"Weaknesses: {evaluation['weaknesses']}")
            print(f"Suggestions: {evaluation['suggestions']}")
        except Exception as e:
            print(f"Error evaluating answer: {e}")

    # 6. Ask user if they want the final assessment report
    if evaluations:
        generate_report = input("\nWould you like to generate the Final Assessment Report? (yes/no): ").strip().lower()
        if generate_report in ("yes", "y"):
            print("\n=== Step 4: Generating Final Assessment Report ===")
            report = engine.generate_final_report(evaluations)
            print(json.dumps(report, indent=4))
        else:
            print("\nFinal Assessment Report skipped. Thank you for the interview!")
    else:
        print("\nNo evaluations generated to aggregate.")

if __name__ == "__main__":
    run_interview_flow()
