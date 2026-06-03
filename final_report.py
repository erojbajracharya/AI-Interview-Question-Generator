# final_report.py
import os
import sys
import re
from job_roles import JOB_ROLES
import resume_parser
import question_generator

# ANSI color codes for premium console output
class Style:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(title):
    print(f"\n{Style.HEADER}{Style.BOLD}{'=' * 60}")
    print(f" {title.center(58)}")
    print(f"{'=' * 60}{Style.END}\n")

def check_dependencies():
    """Ensure all required libraries are installed."""
    try:
        import PyPDF2
        import spacy
        from google import genai
    except ImportError:
        print(f"{Style.YELLOW}Missing dependencies. Installing requirements...{Style.END}")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf2", "spacy", "google-genai"])
        # Download default small spacy model
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])

def is_slop_answer(answer, question):
    """Detects if an answer is gibberish, cop-out, copy of the question, or invalid."""
    if not answer or not answer.strip():
        return True, "No response provided."
    
    clean_ans = answer.strip().lower()
    # Remove punctuation for matching
    clean_ans_alphanum = re.sub(r'[^a-z0-9\s]', '', clean_ans).strip()
    
    # 1. Check for basic length / empty
    if len(clean_ans_alphanum) < 3:
        return True, "Response is too short or empty."
        
    # 2. Check for common cop-out phrases
    cop_outs = {
        "i dont know", "i do not know", "idk", "no idea", "no clue", "skip", 
        "na", "n/a", "pass", "not sure", "dont know", "dunno", "none", "nothing", 
        "test", "hello", "hi", "hey", "test answer", "gibberish", "slop"
    }
    if clean_ans_alphanum in cop_outs:
        return True, f"Response appears to be a cop-out ('{answer}')."
        
    # 3. Check for copying the question
    clean_q = re.sub(r'[^a-z0-9\s]', '', question.lower()).strip()
    words_ans = set(clean_ans_alphanum.split())
    words_q = set(clean_q.split())
    
    if len(words_ans) > 0:
        overlap = words_ans.intersection(words_q)
        # If the answer is entirely made of words from the question, and contains no new substantial words
        if len(overlap) / len(words_ans) > 0.8 and len(words_ans) > 2:
            return True, "Response just repeats or copies the interview question."

    # 4. Check for repetition (e.g., "bla bla bla bla bla")
    words_list = clean_ans_alphanum.split()
    if len(words_list) >= 4:
        unique_ratio = len(set(words_list)) / len(words_list)
        if unique_ratio < 0.35:
            return True, "Response contains excessive repetitive words."
            
    # 5. Check for gibberish (e.g., "asdfasdfasdf", "qwertyuiop")
    vowels = set("aeiou")
    vowel_count = sum(1 for char in clean_ans_alphanum if char in vowels)
    total_chars = sum(1 for char in clean_ans_alphanum if char.isalpha())
    if total_chars > 5:
        vowel_ratio = vowel_count / total_chars
        if vowel_ratio < 0.12 or vowel_ratio > 0.80:
            return True, "Response appears to be gibberish or nonsense characters."
            
        # Check if there are any common English words or question word overlaps
        common_words = {
            "the", "a", "and", "to", "in", "is", "you", "that", "it", "he", "was", "for", 
            "on", "are", "as", "with", "his", "they", "i", "at", "be", "this", "have", "from", 
            "or", "one", "had", "by", "word", "but", "not", "what", "all", "were", "we", "when", 
            "your", "can", "said", "there", "use", "an", "each", "which", "she", "do", "how", 
            "their", "if", "will", "up", "other", "about", "out", "many", "then", "them", "these", 
            "so", "some", "her", "would", "make", "like", "him", "into", "time", "has", "look", 
            "two", "more", "write", "go", "see", "number", "no", "way", "could", "people", "my", 
            "than", "first", "water", "been", "call", "who", "oil", "its", "now", "find", "long", 
            "down", "day", "did", "get", "come", "made", "may", "part", "project", "work", "job", 
            "experience", "team", "code", "learn", "using", "used", "with", "about", "manage"
        }
        if not words_ans.intersection(common_words) and not words_ans.intersection(words_q):
            return True, "Response does not contain any recognizable English words."

    return False, ""

def grade_answers(questions, answers, role_info, difficulty):
    """Evaluates answers using Gemini if available, otherwise fallback NLP heuristic."""
    api_key = os.environ.get("GEMINI_API_KEY")
    evaluations = []
    
    for q, a in zip(questions, answers):
        # First, run local slop detection
        is_slop, reason = is_slop_answer(a, q)
        if is_slop:
            evaluations.append(f"Score: 0/10 | Feedback: Invalid response. {reason} | Improve: Provide a meaningful, structured response answering the question.")
            continue
            
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                
                prompt = (
                    f"Evaluate this response to an interview question.\n"
                    f"Job Role: {role_info['title']}\n"
                    f"Difficulty: {difficulty}\n"
                    f"Question: {q}\n"
                    f"Candidate's Answer: {a}\n\n"
                    f"Provide: \n"
                    f"1. Score (out of 10)\n"
                    f"2. Brief Feedback (max 2 sentences)\n"
                    f"3. Key improvement point\n"
                    f"Format: Score: X/10 | Feedback: ... | Improve: ...\n"
                    f"CRITICAL: If the answer is completely off-topic, gibberish, filler text, repetitive nonsense, a cop-out (e.g., 'I don't know', 'skip'), or simply copies/paraphrases the question without answering it, you MUST assign a score of 0/10 and state in the feedback that the answer is non-responsive or invalid."
                )
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                evaluations.append(response.text.strip())
                continue
            except Exception:
                pass

        # Simple template heuristic fallback evaluation
        word_count = len(a.split())
        if word_count < 5:
            score = 2
            feedback = "Too brief. Try to structure your answer using the STAR method."
            improve = "Elaborate with specific details."
        elif word_count < 15:
            score = 5
            feedback = "A reasonable start, but lacks depth and specific examples."
            improve = "Use quantitative metrics or concrete projects to prove your point."
        else:
            score = 8
            feedback = "Good response covering key aspects of the question."
            improve = "Polishing communication delivery and structure."
        evaluations.append(f"Score: {score}/10 | Feedback: {feedback} | Improve: {improve}")
        
    return evaluations

def main():
    check_dependencies()
    print_header("AI INTERVIEW SIMULATOR & RESUME PARSER")
    
    # 1. Resume Upload / Input
    print(f"{Style.BOLD}Step 1: Resume Upload{Style.END}")
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1].strip('"').strip("'")
        print(f"Using resume: {pdf_path}")
    else:
        pdf_path = input("Enter the absolute path to your resume PDF: ").strip('"').strip("'")
    
    if not os.path.exists(pdf_path):
        print(f"{Style.RED}Error: File not found. Please verify the path.{Style.END}")
        return
        
    print(f"\n{Style.CYAN}Parsing resume...{Style.END}")
    profile = resume_parser.parse_resume(pdf_path)
    
    print(f"{Style.GREEN}✓ Extraction Complete!{Style.END}")
    print(f"Estimated Experience: {Style.BOLD}{profile['experience_years']} years{Style.END}")
    print(f"Extracted Hard Skills: {Style.BOLD}{', '.join(profile['hard_skills']) or 'None detected'}{Style.END}")
    print(f"Extracted Soft Skills: {Style.BOLD}{', '.join(profile['soft_skills']) or 'None detected'}{Style.END}")
    
    # 2. Select Job Role
    print_header("Step 2: Job Role Selection")
    print("Available Roles:")
    roles_list = list(JOB_ROLES.keys())
    for idx, r_key in enumerate(roles_list, 1):
        print(f"  [{idx}] {JOB_ROLES[r_key]['title']}")
        
    role_choice = input(f"\nSelect job role (1-{len(roles_list)}): ").strip()
    try:
        role_idx = int(role_choice) - 1
        selected_role_key = roles_list[role_idx]
    except (ValueError, IndexError):
        print(f"{Style.YELLOW}Invalid selection. Defaulting to Software Engineer.{Style.END}")
        selected_role_key = "software_engineer"
        
    role_info = JOB_ROLES[selected_role_key]
    
    # 3. Determine Difficulty Level
    difficulty = question_generator.determine_difficulty(profile['experience_years'], selected_role_key)
    print(f"\n{Style.CYAN}Analyzing requirements for {Style.BOLD}{role_info['title']}{Style.END} role...")
    print(f"AI Determined Difficulty Level: {Style.GREEN}{Style.BOLD}{difficulty.upper()}{Style.END}")
    
    # 4. Generate Interview Questions
    num_q_choice = input(f"\nHow many questions would you like to be asked? (default: 5): ").strip()
    try:
        num_questions = int(num_q_choice)
        if num_questions <= 0:
            num_questions = 5
    except ValueError:
        num_questions = 5

    print(f"\n{Style.CYAN}Generating {num_questions} interview questions based on level and profile...{Style.END}")
    questions = question_generator.generate_questions(profile, selected_role_key, difficulty, num_questions=num_questions)
    
    # 5. Interview Simulation
    print_header("Step 3: Interview Simulation")
    print(f"You will be asked {len(questions)} questions. Type your answer and press Enter.")
    
    answers = []
    for idx, q in enumerate(questions, 1):
        print(f"\n{Style.BOLD}Question {idx}: {q}{Style.END}")
        answer = input(f"{Style.BLUE}Your Answer: {Style.END}").strip()
        answers.append(answer if answer else "No answer provided.")
        
    # 6. Final Report Generation
    print_header("Step 4: Generating Final Report")
    print(f"{Style.CYAN}Evaluating responses...{Style.END}")
    evaluations = grade_answers(questions, answers, role_info, difficulty)
    
    print_header("OFFICIAL INTERVIEW PERFORMANCE REPORT")
    print(f"Job Role: {Style.BOLD}{role_info['title']}{Style.END}")
    print(f"Target Level: {Style.BOLD}{difficulty.upper()}{Style.END}")
    print(f"Candidate Experience: {Style.BOLD}{profile['experience_years']} years{Style.END}")
    print("-" * 60)
    
    total_score = 0
    for idx, (q, a, eval_str) in enumerate(zip(questions, answers, evaluations), 1):
        print(f"\n{Style.BOLD}Q{idx}: {q}{Style.END}")
        print(f"Your Answer: {a}")
        print(f"{Style.GREEN}Evaluation: {eval_str}{Style.END}")
        
        # Parse score if in fallback or standard format
        score = 0
        if "Score:" in eval_str:
            try:
                score = float(eval_str.split("Score:")[1].split("/10")[0].strip())
            except Exception:
                score = 5
        total_score += score
        
    avg_score = total_score / len(questions)
    print("\n" + "=" * 60)
    print(f"{Style.BOLD}OVERALL SCORE: {avg_score:.1f}/10{Style.END}")
    
    if avg_score >= 8:
        print(f"{Style.GREEN}{Style.BOLD}Status: Highly Recommended for hire!{Style.END}")
    elif avg_score >= 5:
        print(f"{Style.YELLOW}{Style.BOLD}Status: Recommended with some training.{Style.END}")
    else:
        print(f"{Style.RED}{Style.BOLD}Status: Needs improvement.{Style.END}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
