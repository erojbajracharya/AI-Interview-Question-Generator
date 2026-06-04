# resume_parser.py
import re
import PyPDF2
import spacy
from spacy.matcher import PhraseMatcher
from job_roles import JOB_ROLES

def extract_text_from_pdf(pdf_path):
    """Extracts all text from a PDF file using PyPDF2."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def parse_resume(pdf_path):
    """Parses resume PDF to extract skills and estimate experience."""
    text = extract_text_from_pdf(pdf_path)
    
    # Load spaCy English model (require the model to be installed)
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        raise RuntimeError("spaCy model 'en_core_web_sm' is required. Install it with: python -m spacy download en_core_web_sm") from e
            
    doc = nlp(text.lower())
    
    # Extract hard and soft skills defined in job_roles
    extracted_hard_skills = set()
    extracted_soft_skills = set()
    
    all_hard_skills = []
    all_soft_skills = []
    for role_info in JOB_ROLES.values():
        all_hard_skills.extend(role_info["hard_skills"])
        all_soft_skills.extend(role_info["soft_skills"])
        
    # Match skills using PhraseMatcher
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    
    hard_patterns = [nlp.make_doc(skill) for skill in set(all_hard_skills)]
    soft_patterns = [nlp.make_doc(skill) for skill in set(all_soft_skills)]
    
    matcher.add("HARD_SKILLS", hard_patterns)
    matches_hard = matcher(doc)
    for match_id, start, end in matches_hard:
        extracted_hard_skills.add(doc[start:end].text)
        
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER") # reset matcher
    matcher.add("SOFT_SKILLS", soft_patterns)
    matches_soft = matcher(doc)
    for match_id, start, end in matches_soft:
        extracted_soft_skills.add(doc[start:end].text)
        
    # Estimate years of experience
    # Look for patterns like "X+ years", "X years", "X yrs"
    experience_years = 0
    exp_patterns = [
        r'(\d+)\s*\+?\s*years?\s+(?:of\s+)?experience',
        r'experience\s*:\s*(\d+)\s*years?',
        r'(\d+)\s*yrs?'
    ]
    
    matches = []
    for pattern in exp_patterns:
        matches.extend(re.findall(pattern, text.lower()))
    
    if matches:
        # Get the maximum number found in the experience contexts
        try:
            experience_years = max(int(m) for m in matches if int(m) < 40)
        except ValueError:
            pass
            
    # Also attempt a heuristic based on date ranges (e.g. 2018 - 2022)
    date_matches = re.findall(r'\b(19\d{2}|20\d{2})\b\s*[-–—]\s*\b(19\d{2}|20\d{2}|present|current)\b', text.lower())
    if date_matches:
        calculated_exp = 0
        current_year = 2026 # Local time metadata says 2026
        for start_yr, end_yr in date_matches:
            try:
                s_yr = int(start_yr)
                e_yr = current_year if end_yr in ['present', 'current'] else int(end_yr)
                if e_yr >= s_yr:
                    calculated_exp += (e_yr - s_yr)
            except ValueError:
                pass
        experience_years = max(experience_years, calculated_exp)

    return {
        "hard_skills": list(extracted_hard_skills),
        "soft_skills": list(extracted_soft_skills),
        "experience_years": experience_years if experience_years > 0 else 1
    }


