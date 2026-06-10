# final_report.py
import os
import re

def grade_answers(questions, answers, role_info, difficulty, reference_answers=None, api_keys=None):
    """
    Evaluate candidate answers using the Gemini API with API key rotation.
    Falls back to offline grading if no keys are valid or API fails entirely.
    """
    # Parse api_keys
    keys_list = []
    if api_keys:
        if isinstance(api_keys, str):
            keys_list = [k.strip() for k in api_keys.split(",") if k.strip()]
        elif isinstance(api_keys, list):
            keys_list = [k.strip() for k in api_keys if k.strip()]
    
    # Fallback to env var if no keys passed in list
    if not keys_list:
        env_key = os.environ.get("GEMINI_API_KEY")
        if env_key:
            keys_list = [env_key]
            
    if not keys_list:
        print("[REPORT] No API keys provided. Falling back to offline heuristic grading.")
        return grade_answers_offline(questions, answers, role_info, difficulty, reference_answers=reference_answers)

    # We will try evaluating using the available keys
    from google import genai
    
    evaluations = []
    key_idx = 0
    
    for idx, (q, a) in enumerate(zip(questions, answers)):
        # Empty or whitespace response guard
        if not a or not a.strip():
            evaluations.append("Score: 0/10 | Feedback: Invalid response. No response provided. | Improve: Provide a meaningful, structured response answering the question.")
            continue
            
        ref_ans = reference_answers[idx] if (reference_answers and idx < len(reference_answers)) else None
        
        # Try to grade this question, rotating keys if it fails
        success = False
        attempts = 0
        max_attempts = len(keys_list)
        
        while not success and attempts < max_attempts:
            current_key = keys_list[key_idx]
            try:
                client = genai.Client(api_key=current_key)
                
                # Build the prompt
                prompt = f"Role: {role_info['title']} ({difficulty})\nQuestion: {q}\n"
                if ref_ans:
                    prompt += f"Standard Reference Answer: {ref_ans}\n"
                prompt += f"Candidate Answer: {a}\n\n"
                
                prompt += (
                    "Evaluate the candidate's answer. Format your response exactly as: Score: X/10 | Feedback: ... | Improve: ...\n"
                )
                if ref_ans:
                    prompt += "CRITICAL: Compare the candidate's answer against the standard reference answer. Check if they capture the key points. Award points accordingly based on how accurate and complete it is relative to the reference.\n"
                prompt += (
                    "CRITICAL: If the answer is off-topic, gibberish, repetitive, a cop-out ('skip', 'idk', 'n/a'), or copies the question, score 0/10 and state why in Feedback (max 2 sentences)."
                )
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                evaluations.append(response.text.strip())
                success = True
            except Exception as e:
                print(f"[REPORT ERROR] AI evaluation failed with key index {key_idx} (Key ending in ...{current_key[-4:] if len(current_key) > 4 else ''}): {e}")
                # Rotate to the next key
                key_idx = (key_idx + 1) % len(keys_list)
                attempts += 1
                
        if not success:
            print("[REPORT WARNING] All API keys failed for this question. Falling back to offline grading for this and subsequent questions.")
            # Fallback to offline grading for the remaining questions
            remaining_qs = questions[idx:]
            remaining_as = answers[idx:]
            remaining_ref = reference_answers[idx:] if reference_answers else None
            offline_evals = grade_answers_offline(remaining_qs, remaining_as, role_info, difficulty, reference_answers=remaining_ref, was_fallback=True)
            evaluations.extend(offline_evals)
            break
            
    return evaluations


def grade_answers_offline(questions, answers, role_info, difficulty, reference_answers=None, was_fallback=False):
    """Heuristic offline grading system using keyword matching and reference answer comparison."""
    evaluations = []
    hard_skills = [s.lower() for s in role_info.get("hard_skills", [])]
    soft_skills = [s.lower() for s in role_info.get("soft_skills", [])]
    all_skills = hard_skills + soft_skills
    role_title = role_info.get("title", "Candidate Role")

    prefix = "(Offline Fallback) " if was_fallback else "(Offline Heuristic) "

    for idx, (q, a) in enumerate(zip(questions, answers)):
        if not a or not a.strip():
            evaluations.append(f"Score: 0/10 | Feedback: {prefix}No answer was provided. | Improve: Please make sure to write an answer to each question.")
            continue
        
        a_clean = a.strip().lower()
        if a_clean in ["skip", "idk", "n/a", "no idea", "i don't know", "skipped", "[skipped]"]:
            evaluations.append(f"Score: 0/10 | Feedback: {prefix}Question was skipped or not answered. | Improve: Try to answer the question using your general experience or theoretical knowledge.")
            continue

        words = a_clean.split()
        word_count = len(words)
        
        # Check for skill keyword occurrences
        matched_skills = [skill for skill in all_skills if skill in a_clean]
        
        # Check reference answer overlap if available
        ref_ans = reference_answers[idx] if (reference_answers and idx < len(reference_answers)) else None
        overlap_info = ""
        overlap_score_bonus = 0
        
        if ref_ans:
            ref_clean = ref_ans.lower()
            # simple stop words list to filter out common words
            stop_words = {"the", "a", "an", "and", "or", "but", "if", "then", "else", "to", "of", "in", "on", "at", "for", "with", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "as", "that", "this", "these", "those"}
            # extract content words of length > 3 from reference answer
            ref_words = set(re.findall(r'\b[a-z]{4,}\b', ref_clean)) - stop_words
            
            if ref_words:
                matched_ref_words = [w for w in ref_words if w in a_clean]
                match_ratio = len(matched_ref_words) / len(ref_words)
                
                # Award up to 4 points based on keyword match ratio from reference answer
                overlap_score_bonus = int(match_ratio * 4)
                if matched_ref_words:
                    overlap_info = f" Key concepts matched: {', '.join(matched_ref_words[:3])}."
        
        # Determine score and feedback based on length and relevance
        if word_count < 6:
            score = min(3 + overlap_score_bonus, 5)
            feedback = f"The response is too brief to adequately answer the question."
            improve = f"Provide a complete, detailed explanation. Try to cover topics like: {ref_ans[:60] if ref_ans else role_title}."
        elif word_count < 15:
            # Base of 4, + bonus from reference answer, max 7
            score = min(4 + overlap_score_bonus + (1 if matched_skills else 0), 7)
            feedback = f"The response is concise but relevant.{overlap_info}"
            if matched_skills and not overlap_info:
                feedback += f" Included terminology: {', '.join(matched_skills[:2])}."
            improve = f"Elaborate further by describing how you apply these skills in projects."
        else:
            # Base of 5, + bonus from reference answer (up to 4), + 1 for matched skills, max 9
            score = min(5 + overlap_score_bonus + (1 if matched_skills else 0), 9)
            feedback = f"The response is structured and relevant.{overlap_info}"
            if matched_skills and not overlap_info:
                feedback += f" Demonstrates familiarity with: {', '.join(matched_skills[:3])}."
            improve = f"To achieve a perfect score, provide a specific example of applying these concepts in your past experience."

        evaluations.append(f"Score: {score}/10 | Feedback: {prefix}{feedback} | Improve: {improve}")
        
    return evaluations
