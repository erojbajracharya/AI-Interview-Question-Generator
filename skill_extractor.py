import spacy
from spacy.matcher import PhraseMatcher

def extract_skills(text: str) -> dict:
    """
    Extracts predefined hard and soft skills from the input resume text.
    
    Parameters:
        text (str): The text content of the resume.
        
    Returns:
        dict: A dictionary containing lists of matched hard and soft skills:
              {
                  "hard_skills": [...],
                  "soft_skills": [...]
              }
    """
    # Initialize a blank English spaCy model for fast tokenization
    nlp = spacy.blank("en")
    
    # Predefined skill dictionary
    skill_dictionary = {
        "hard_skills": [
            "Python", "Java", "C++", "MySQL", "SQL", "JavaScript", 
            "React", "Docker", "Git", "Machine Learning", "TensorFlow", 
            "Flask", "Django"
        ],
        "soft_skills": [
            "Communication", "Leadership", "Teamwork", "Problem Solving", 
            "Time Management"
        ]
    }
    
    # Initialize PhraseMatcher with LOWER attribute for case-insensitive matching
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    
    # Map lowercase skill names back to their canonical (original) names and categories
    canonical_skills = {}
    
    for category, skills in skill_dictionary.items():
        patterns = []
        for skill in skills:
            # Create a doc for the skill to get tokens
            pattern_doc = nlp.make_doc(skill)
            patterns.append(pattern_doc)
            # Store lowercase version mapping to canonical name and category
            canonical_skills[skill.lower()] = (skill, category)
        
        # Add the patterns under the category label
        matcher.add(category, patterns)
    
    # Preprocess text: replace hyphens with spaces to match variants like "problem-solving"
    normalized_text = text.replace("-", " ")
    
    # Process the text with spaCy
    doc = nlp(normalized_text)
    
    # Find all matches in the text
    matches = matcher(doc)
    
    # Initialize response structure
    results = {
        "hard_skills": [],
        "soft_skills": []
    }
    
    # Use sets to keep track of added skills and ignore duplicates
    seen_hard_skills = set()
    seen_soft_skills = set()
    
    # Iterate through matched spans
    for match_id, start, end in matches:
        span = doc[start:end]
        matched_text_lower = span.text.lower()
        
        if matched_text_lower in canonical_skills:
            canonical_name, category = canonical_skills[matched_text_lower]
            
            if category == "hard_skills" and canonical_name not in seen_hard_skills:
                seen_hard_skills.add(canonical_name)
                results["hard_skills"].append(canonical_name)
            elif category == "soft_skills" and canonical_name not in seen_soft_skills:
                seen_soft_skills.add(canonical_name)
                results["soft_skills"].append(canonical_name)
                
    return results

if __name__ == "__main__":
    # Test example
    print("--- Running Skill Extractor Test ---")
    
    # Dummy resume text for demonstration
    sample_resume = """
    John Doe
    Software Engineer
    
    Summary:
    A passionate Software Engineer with extensive experience building scalable web applications.
    Strong leadership and communication abilities, with a focus on problem-solving in fast-paced environments.
    
    Skills:
    - Programming Languages: python, JAVA, C++, javascript
    - Web Technologies: React, Django, Flask, HTML, CSS
    - Databases & Tools: MySQL, SQL, Docker, GIT, Terraform
    - AI & ML: Machine-Learning, TensorFlow
    - Soft Skills: Teamwork, Time Management
    """
    
    print("Extracting skills from sample resume...")
    extracted_skills = extract_skills(sample_resume)
    
    import json
    print("\nExtracted Skills (JSON format):")
    print(json.dumps(extracted_skills, indent=4))
