# final_report.py
import os
import re
from job_roles import JOB_ROLES

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
    """Evaluate answers using Gemini. No local fallback is performed — GEMINI_API_KEY is required."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required for automated evaluation.")

    try:
        from google import genai
    except Exception as e:
        raise ImportError("google.genai package is required for evaluation. Install the official GenAI SDK.") from e

    client = genai.Client(api_key=api_key)
    evaluations = []

    for q, a in zip(questions, answers):
        is_slop, reason = is_slop_answer(a, q)
        if is_slop:
            evaluations.append(f"Score: 0/10 | Feedback: Invalid response. {reason} | Improve: Provide a meaningful, structured response answering the question.")
            continue

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

    return evaluations
