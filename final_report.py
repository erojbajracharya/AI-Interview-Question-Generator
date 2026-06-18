# final_report.py
import re
import api_rotator

def grade_answers(questions, answers, role_info, difficulty, reference_answers=None, api_keys=None):
    """
    Evaluate candidate answers using the Gemini API with automatic API key rotation.
    Falls back to offline grading if no keys are valid or API fails entirely.
    """
    # Use built-in API keys from api_rotator (ignore api_keys parameter)
    rotator = api_rotator.get_rotator()
    rotator.reset()  # Start from the first key
    
    if rotator.is_offline:
        print("[REPORT] No API keys available. Falling back to offline heuristic grading.")
        return grade_answers_offline(questions, answers, role_info, difficulty, reference_answers=reference_answers)

    # We will try evaluating using the available keys
    from google import genai
    
    evaluations = []
    
    for idx, (q, a) in enumerate(zip(questions, answers)):
        # Empty or whitespace response guard
        if not a or not a.strip():
            evaluations.append("Score: 0/10 | Feedback: Invalid response. No response provided. | Improve: Provide a meaningful, structured response answering the question.")
            continue
            
        ref_ans = reference_answers[idx] if (reference_answers and idx < len(reference_answers)) else None
        
        # Try to grade this question, rotating keys if it fails
        success = False
        attempts = 0
        max_attempts = len(api_rotator.get_all_keys()) * 3
        
        while not success and attempts < max_attempts:
            current_key = rotator.get_current_key()
            try:
                client = genai.Client(api_key=current_key)

                prompt = f"""
                You are a senior interviewer evaluating a candidate.

                Role: {role_info['title']}
                Difficulty: {difficulty}

                Question:
                {q}

                Reference Answer:
                {ref_ans if ref_ans else "None"}

                Candidate Answer:
                {a}

                Evaluate:
                1. Relevance
                2. Technical accuracy
                3. Completeness
                4. Communication clarity
                5. Alignment with {difficulty}-level expectations

                Scoring:
                0-2 = Incorrect, irrelevant, skipped, or gibberish
                3-4 = Weak understanding
                5-6 = Basic competency
                7-8 = Strong answer
                9-10 = Expert-level answer with depth, reasoning, or practical insight

                Rules:
                - Compare against the reference answer when available.
                - Accept alternative correct approaches.
                - Prioritize correctness over confidence or length.
                - Penalize factual errors and missing critical concepts.
                - If the answer is empty, copied, off-topic, or meaningless, score 0/10.

                Return EXACTLY:
                Score: X/10 | Feedback: ... | Improve: ...

                Feedback and Improve must each be concise and actionable.
                """
                
                response = client.models.generate_content(
                    model='gemini-3-flash-preview',
                    contents=prompt
                )
                evaluations.append(response.text.strip())
                success = True
            except Exception as e:
                attempts += 1
                print(f"[REPORT ERROR] AI evaluation failed (attempt {attempts}): {e}")
                # Rotate to the next key
                rotator.mark_failed(rotator.get_current_key())
                if attempts < max_attempts:
                    rotator.rotate()
                    print(f"[REPORT] Rotating to next API key...")
                    import time
                    time.sleep(1)
                
        if not success:
            print("[REPORT WARNING] All API keys failed after multiple cycles for this question. Falling back to offline grading for this and subsequent questions.")
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
