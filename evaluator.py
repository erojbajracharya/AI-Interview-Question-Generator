import os
import json
from google import genai
from google.genai import types

def evaluate_answer(question: str, candidate_answer: str) -> dict:
    """
    Evaluates a candidate's answer to a specific interview question using the Gemini API.

    Evaluation criteria:
    - Technical Accuracy
    - Completeness
    - Communication Quality

    Parameters:
        question (str): The interview question asked.
        candidate_answer (str): The candidate's response to the question.

    Returns:
        dict: A dictionary containing the score (1-10), strengths, weaknesses, and suggestions:
              {
                  "score": int,
                  "strengths": [...],
                  "weaknesses": [...],
                  "suggestions": [...]
              }
    """
    # 1. Retrieve Gemini API Key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "API Key Error: The 'GEMINI_API_KEY' environment variable is not set. "
            "Please set the environment variable and try again."
        )

    # 2. Construct the structured evaluation prompt
    prompt = f"""
You are an expert technical interviewer and evaluator. Evaluate the candidate's response to the following question.

Question:
{question}

Candidate's Answer:
{candidate_answer}

Evaluate the response based on these three criteria:
1. Technical Accuracy: Is the content technically correct?
2. Completeness: Does the response fully answer all parts of the question?
3. Communication Quality: Is the response clear, structured, and easy to understand?

Instructions:
1. Determine an overall score from 1 to 10 (integer).
2. Detail the strengths of the candidate's response.
3. Detail the weaknesses or missing parts of the candidate's response.
4. Provide constructive suggestions for how the candidate can improve this response.
5. The response must be formatted as a valid JSON object with the exact keys:
   - "score": (integer)
   - "strengths": (array of strings)
   - "weaknesses": (array of strings)
   - "suggestions": (array of strings)
"""

    try:
        # 3. Initialize the Google GenAI SDK client
        client = genai.Client(api_key=api_key)

        # 4. Generate structured content using the default gemini-2.5-flash model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        # 5. Parse and handle exceptions
        if not response.text:
            raise ValueError("Empty response received from the Gemini API.")

        evaluation = json.loads(response.text)

        # Validate response keys
        required_keys = ["score", "strengths", "weaknesses", "suggestions"]
        for key in required_keys:
            if key not in evaluation:
                raise ValueError(f"Required key '{key}' was missing in the evaluator response.")

        # Ensure score is within range 1 to 10
        score = evaluation.get("score", 1)
        if not isinstance(score, int):
            try:
                evaluation["score"] = int(score)
            except ValueError:
                evaluation["score"] = 1
        evaluation["score"] = max(1, min(10, evaluation["score"]))

        return evaluation

    except json.JSONDecodeError as e:
        print(f"Failed to parse Gemini response as JSON: {e}")
        return {
            "score": 1,
            "strengths": [],
            "weaknesses": ["Failed to decode evaluator response."],
            "suggestions": ["Please verify the input format and retry."]
        }
    except Exception as e:
        print(f"Error evaluating answer via Gemini API: {e}")
        raise

if __name__ == "__main__":
    # Test example
    print("--- Running Evaluator Test ---")
    
    # Dummy data
    test_question = "What is the difference between a list and a tuple in Python, and when would you use each?"
    test_answer = (
        "A list is mutable, which means you can change its elements after creation. A tuple is immutable, "
        "meaning it cannot be changed. Lists are created with square brackets, while tuples use parentheses. "
        "Usually, lists are used for collections of items that might change, but I am not sure when we need tuples "
        "except maybe for keys in dictionaries."
    )

    # Set a dummy key if not present, to show error handling message
    if "GEMINI_API_KEY" not in os.environ:
        print("\nWARNING: GEMINI_API_KEY environment variable is not set.")
        print("Set the environment variable to test the actual API call.\n")
        
        # Testing local error handling flow
        try:
            evaluate_answer(test_question, test_answer)
        except ValueError as e:
            print(f"Successfully caught missing key error: {e}")
    else:
        print("API Key found. Attempting to evaluate the answer...")
        try:
            evaluation_result = evaluate_answer(test_question, test_answer)
            print("\nEvaluation Results:")
            print(json.dumps(evaluation_result, indent=4))
        except Exception as e:
            print(f"Failed to evaluate answer: {e}")
