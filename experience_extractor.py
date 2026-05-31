import re

def determine_experience(text: str) -> dict:
    """
    Analyzes resume text using regular expressions to detect the candidate's
    years of experience and categorizes their experience level.

    Categories:
    - Beginner: 0-1 years (less than 2 years)
    - Intermediate: 2-4 years (less than 5 years)
    - Expert: 5+ years

    Parameters:
        text (str): The text content of the resume.

    Returns:
        dict: A dictionary containing the detected years of experience and level:
              {
                  "experience_years": x,
                  "experience_level": "Level"
              }
    """
    # Regex to find numbers followed by "year(s)", "yr(s)", optionally with a "+" sign
    # Matches patterns like "5+ years", "3 years of experience", "1.5 yrs", etc.
    pattern = r'\b(\d+(?:\.\d+)?)\+?\s*(?:yr|year)s?\b'
    
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    years = 0.0
    if matches:
        years_list = []
        for match in matches:
            try:
                val = float(match)
                # Exclude unreasonably large numbers (e.g. matching a calendar year like 2021)
                if val < 50:
                    years_list.append(val)
            except ValueError:
                continue
        if years_list:
            years = max(years_list)
            
    # Format years as integer if it's a whole number, otherwise keep as float
    display_years = int(years) if years.is_integer() else years

    # Categorize experience level based on the requirements
    if years < 2:
        level = "Beginner"
    elif years < 5:
        level = "Intermediate"
    else:
        level = "Expert"

    return {
        "experience_years": display_years,
        "experience_level": level
    }

if __name__ == "__main__":
    # Test cases
    test_cases = [
        "I am a developer with 5+ years of experience in Python.",
        "Experienced software engineer with 3.5 yrs in the field.",
        "Fresh graduate with 1 year of internship experience.",
        "Over 10 years of leadership in IT projects.",
        "No explicit experience mentioned here.",
        "Worked from 2018 to 2023, totaling 5 years of professional experience."
    ]
    
    print("--- Running Experience Extractor Test ---")
    for idx, tc in enumerate(test_cases, 1):
        result = determine_experience(tc)
        print(f"\nTest {idx}: \"{tc}\"")
        print(f"Result: {result}")
