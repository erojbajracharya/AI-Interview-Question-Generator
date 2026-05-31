import os
import os
import json
from google import genai
from google.genai import types

def generate_questions(
    hard_skills: list,
    soft_skills: list,
    job_description: str,
    difficulty_level: str,
    num_questions: int = 8
) -> list:
    """
    Generates personalized interview questions based on candidate skills,
    job description, and target difficulty level using the new Gemini API (google-genai SDK).

    Parameters:
        hard_skills (list): List of detected technical skills.
        soft_skills (list): List of detected soft skills.
        job_description (str): Target job description text.
        difficulty_level (str): 'Beginner', 'Intermediate', or 'Expert'.
        num_questions (int): The total number of questions to generate.

    Returns:
        list: A Python list of dictionaries representing the questions:
              [
                  {"type": "technical", "question": "..."},
                  {"type": "behavioral", "question": "..."}
              ]
    """
    # 1. Retrieve Gemini API Key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "API Key Error: The 'GEMINI_API_KEY' environment variable is not set. "
            "Please set the environment variable and try again."
        )

    # 2. Define valid difficulty levels and validate input
    valid_levels = ["Beginner", "Intermediate", "Expert"]
    if difficulty_level not in valid_levels:
        raise ValueError(
            f"Invalid difficulty level '{difficulty_level}'. "
            f"Must be one of {valid_levels}."
        )

    if num_questions < 1:
        raise ValueError("num_questions must be at least 1.")

    # Dynamic partition: roughly 60% technical and 40% behavioral questions
    tech_count = max(1, round(num_questions * 0.6))
    behavioral_count = max(1, num_questions - tech_count)

    # 3. Construct prompt engineering instructions
    prompt = f"""
You are an expert interviewer. Generate exactly {num_questions} highly personalized interview questions for a candidate.

Target Job Description:
{job_description}

Candidate's Hard Skills:
{", ".join(hard_skills) if hard_skills else "General technical skills"}

Candidate's Soft Skills:
{", ".join(soft_skills) if soft_skills else "General interpersonal skills"}

Target Difficulty Level: {difficulty_level}

Instructions:
1. Generate exactly {tech_count} technical (hard skill) questions assessing the candidate's specific hard skills in the context of the job description. The complexity of these questions should align with the "{difficulty_level}" difficulty level.
2. Generate exactly {behavioral_count} behavioral (soft skill) questions assessing how the candidate's soft skills apply to challenges in the job description.
3. The response must be formatted as a valid JSON array of objects. Each object in the array must contain:
   - "type": (string) either "technical" or "behavioral"
   - "question": (string) the generated question text
"""

    try:
        # 4. Initialize the generative client using Google GenAI SDK
        client = genai.Client(api_key=api_key)

        # 5. Request generation with JSON config using the default gemini-2.5-flash model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        # 6. Parse response and handle parsing exceptions
        if not response.text:
            raise ValueError("Empty response received from the Gemini API.")

        questions = json.loads(response.text)

        # Basic validation of structure
        if not isinstance(questions, list):
            raise ValueError("Expected a list of questions, but received a different format.")

        return questions

    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse Gemini response as JSON: {e}. "
            "Please verify the Gemini API response format."
        )
    except Exception as e:
        print(f"Error generating questions via Gemini API: {e}")
        raise

if __name__ == "__main__":
    # Test example
    print("--- Running Question Generator Test ---")
    
    # Dummy data
    test_hard_skills = ["Python", "Docker", "SQL", "Git"]
    test_soft_skills = ["Communication", "Problem Solving"]
    test_job_description = (
        "We are looking for a Junior Python Developer who can maintain our database "
        "pipelines, build microservices with Docker, and work collaboratively in a Git-based workflow."
    )
    test_difficulty = "Beginner"

    # Set a dummy key if not present, to show error handling message
    if "GEMINI_API_KEY" not in os.environ:
        print("\nWARNING: GEMINI_API_KEY environment variable is not set.")
        print("Set the environment variable to test the actual API call.\n")
        
        # Testing local error handling flow
        try:
            generate_questions(test_hard_skills, test_soft_skills, test_job_description, test_difficulty)
        except ValueError as e:
            print(f"Successfully caught missing key error: {e}")
    else:
        print("API Key found. Attempting to generate questions...")
        try:
            questions_list = generate_questions(
                test_hard_skills,
                test_soft_skills,
                test_job_description,
                test_difficulty
            )
            print("\nGenerated Questions:")
            print(json.dumps(questions_list, indent=4))
        except Exception as e:
            print(f"Failed to generate questions: {e}")
