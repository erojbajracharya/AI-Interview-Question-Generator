# final_report.py
import os

def grade_answers(questions, answers, role_info, difficulty):
    """Evaluate candidate answers using the Gemini API."""
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
        # Empty or whitespace response guard
        if not a or not a.strip():
            evaluations.append("Score: 0/10 | Feedback: Invalid response. No response provided. | Improve: Provide a meaningful, structured response answering the question.")
            continue

        prompt = (
            f"Role: {role_info['title']} ({difficulty})\n"
            f"Question: {q}\n"
            f"Answer: {a}\n\n"
            f"Evaluate answer. Format: Score: X/10 | Feedback: ... | Improve: ...\n"
            f"CRITICAL: If the answer is off-topic, gibberish, repetitive, a cop-out ('skip', 'idk', 'n/a'), or copies the question, score 0/10 and state why in Feedback (max 2 sentences)."
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        evaluations.append(response.text.strip())

    return evaluations
