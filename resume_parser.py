# resume_parser.py
import re
import PyPDF2
import spacy
from spacy.matcher import PhraseMatcher
from job_roles import JOB_ROLES

def extract_text_from_pdf(pdf_path):
    """Extracts all text content from a PDF file."""
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
    """Parses resume PDF to extract hard/soft skills and estimate experience years."""
    text = extract_text_from_pdf(pdf_path)
    
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        raise RuntimeError("spaCy model 'en_core_web_sm' is required. Install it with: python -m spacy download en_core_web_sm") from e
            
    doc = nlp(text.lower())
    
    extracted_hard_skills = set()
    extracted_soft_skills = set()
    
    all_hard_skills = []
    all_soft_skills = []
    for role_info in JOB_ROLES.values():
        all_hard_skills.extend(role_info["hard_skills"])
        all_soft_skills.extend(role_info["soft_skills"])
        
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    hard_patterns = [nlp.make_doc(skill) for skill in set(all_hard_skills)]
    matcher.add("HARD_SKILLS", hard_patterns)
    matches_hard = matcher(doc)
    for match_id, start, end in matches_hard:
        extracted_hard_skills.add(doc[start:end].text)
        
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    soft_patterns = [nlp.make_doc(skill) for skill in set(all_soft_skills)]
    matcher.add("SOFT_SKILLS", soft_patterns)
    matches_soft = matcher(doc)
    for match_id, start, end in matches_soft:
        extracted_soft_skills.add(doc[start:end].text)
        
    # Extract EXPERIENCE section
    text_lower = text.lower()
    # Headers must appear at the start of a line to avoid matching
    # words like "experience" inside sentences (e.g. "hands-on experience in...")
    exp_headers = [
        r'\nprofessional\s+experience\b',
        r'\nwork\s+experience\b',
        r'\nemployment\s+history\b',
        r'\nexperience\b'
    ]
    
    start_idx = -1
    for header in exp_headers:
        match = re.search(header, text_lower)
        if match:
            start_idx = match.end()
            break
            
    exp_section = ""
    if start_idx != -1:
        # End headers also anchored to start of line
        end_headers = [
            r'\nprojects\b',
            r'\neducation\b',
            r'\ntechnical\s+skills\b',
            r'\nsoft\s+skills\b',
            r'\nskills\b',
            r'\ncertifications\b',
            r'\nawards\b',
            r'\npublications\b',
            r'\nlanguages\b',
            r'\nprofessional\s+summary\b',
            r'\nsummary\b'
        ]
        end_idx = len(text)
        for header in end_headers:
            matches = list(re.finditer(header, text_lower))
            for m in matches:
                if m.start() > start_idx:
                    if m.start() < end_idx:
                        end_idx = m.start()
        exp_section = text[start_idx:end_idx]

    experience_years = 0
    if exp_section:
        exp_patterns = [
            r'(\d+)\s*\+?\s*years?\s+(?:of\s+)?experience',
            r'experience\s*:\s*(\d+)\s*years?',
            r'(\d+)\s*yrs?'
        ]
        
        matches = []
        for pattern in exp_patterns:
            matches.extend(re.findall(pattern, exp_section.lower()))
        
        if matches:
            try:
                experience_years = max(int(m) for m in matches if int(m) < 40)
            except ValueError:
                pass
                
        # Estimate based on date ranges (e.g. Jun 2024 - Dec 2024 or 2018 - 2022)
        months_map = {
            'jan': 1, 'january': 1,
            'feb': 2, 'february': 2,
            'mar': 3, 'march': 3,
            'apr': 4, 'april': 4,
            'may': 5,
            'jun': 6, 'june': 6,
            'jul': 7, 'july': 7,
            'aug': 8, 'august': 8,
            'sep': 9, 'september': 9,
            'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'dec': 12, 'december': 12
        }
        
        month_regex = r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{4})\b\s*[-–—]\s*\b(?:(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{4})|(present|current))\b'
        month_matches = re.findall(month_regex, exp_section.lower())
        
        calculated_exp = 0.0
        current_year = 2026
        current_month = 6
        
        used_ranges = []
        for start_m, start_y, end_m, end_y, present in month_matches:
            try:
                s_year = int(start_y)
                s_month = months_map.get(start_m, 1)
                
                if present in ['present', 'current']:
                    e_year = current_year
                    e_month = current_month
                else:
                    e_year = int(end_y)
                    e_month = months_map.get(end_m, 1)
                
                months_diff = (e_year - s_year) * 12 + (e_month - s_month)
                if months_diff >= 0:
                    calculated_exp += months_diff / 12.0
                    used_ranges.append((start_y, end_y if not present else 'present'))
            except ValueError:
                pass
                
        year_regex = r'\b(19\d{2}|20\d{2})\b\s*[-–—]\s*\b(19\d{2}|20\d{2}|present|current)\b'
        year_matches = re.findall(year_regex, exp_section.lower())
        for start_yr, end_yr in year_matches:
            is_covered = False
            for uy_start, uy_end in used_ranges:
                if start_yr == uy_start:
                    is_covered = True
                    break
            if not is_covered:
                try:
                    s_yr = int(start_yr)
                    e_yr = current_year if end_yr in ['present', 'current'] else int(end_yr)
                    if e_yr >= s_yr:
                        calculated_exp += (e_yr - s_yr)
                except ValueError:
                    pass
                    
        experience_years = max(experience_years, round(calculated_exp, 1))

    return {
        "hard_skills": list(extracted_hard_skills),
        "soft_skills": list(extracted_soft_skills),
        "experience_years": experience_years
    }