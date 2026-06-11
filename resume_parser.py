# resume_parser.py
import re
import difflib
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


def parse_text(text):
    """Parses raw resume text to extract hard/soft skills and estimate experience years."""
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        raise RuntimeError("spaCy model 'en_core_web_sm' is required. Install it with: python -m spacy download en_core_web_sm") from e

    doc = nlp(text)

    extracted_hard_skills = set()
    extracted_soft_skills = set()

    all_hard_skills = []
    all_soft_skills = []
    for role_info in JOB_ROLES.values():
        all_hard_skills.extend(role_info["hard_skills"])
        all_soft_skills.extend(role_info["soft_skills"])

    # Build canonical mapping for normalization: lower -> canonical
    canonical_hard = {s.lower(): s for s in set(all_hard_skills)}
    canonical_soft = {s.lower(): s for s in set(all_soft_skills)}
    vocab_hard_keys = list(canonical_hard.keys())
    vocab_soft_keys = list(canonical_soft.keys())

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    hard_patterns = [nlp.make_doc(skill) for skill in set(all_hard_skills)]
    soft_patterns = [nlp.make_doc(skill) for skill in set(all_soft_skills)]
    matcher.add("HARD_SKILLS", None, *hard_patterns)
    matcher.add("SOFT_SKILLS", None, *soft_patterns)
    matches = matcher(doc)
    for match_id, start, end in matches:
        label = nlp.vocab.strings[match_id]
        skill_text = doc[start:end].text
        key = skill_text.lower()
        # Normalize to canonical if available, otherwise fuzzy match
        if label == "HARD_SKILLS":
            if key in canonical_hard:
                extracted_hard_skills.add(canonical_hard[key])
            else:
                best = difflib.get_close_matches(key, vocab_hard_keys, n=1, cutoff=0.85)
                extracted_hard_skills.add(canonical_hard[best[0]] if best else skill_text)
        elif label == "SOFT_SKILLS":
            if key in canonical_soft:
                extracted_soft_skills.add(canonical_soft[key])
            else:
                best = difflib.get_close_matches(key, vocab_soft_keys, n=1, cutoff=0.85)
                extracted_soft_skills.add(canonical_soft[best[0]] if best else skill_text)

    # Additional extraction from explicit Skills / Technical Skills sections (higher precision)
    def extract_from_skills_section(text, headers):
        t_low = text.lower()
        start_idx = -1
        for h in headers:
            m = re.search(r'\n' + h + r'\b', t_low)
            if m:
                start_idx = m.end()
                break
        if start_idx == -1:
            return []
        # find next section header
        end_headers = [r'\nexperience\b', r'\neducation\b', r'\nprojects\b', r'\ncertifications\b', r'\nwork\b']
        end_idx = len(text)
        for eh in end_headers:
            ems = list(re.finditer(eh, t_low))
            for em in ems:
                if em.start() > start_idx and em.start() < end_idx:
                    end_idx = em.start()
        section = text[start_idx:end_idx]
        # split by newlines, commas, semicolons
        candidates = re.split(r'[\n,;•·\u2022]', section)
        items = []
        for c in candidates:
            s = c.strip()
            if not s:
                continue
            # remove trailing descriptors in parentheses
            s = re.sub(r'\([^)]*\)', '', s).strip()
            items.append(s)
        return items

    skills_headers = ['technical skills', 'skills', 'skills & tools', 'technical expertise']
    skills_items = extract_from_skills_section(text, skills_headers)
    for item in skills_items:
        key = item.lower()
        # exact or fuzzy match against hard skills first, then soft
        if key in canonical_hard:
            extracted_hard_skills.add(canonical_hard[key])
            continue
        best_h = difflib.get_close_matches(key, vocab_hard_keys, n=1, cutoff=0.78)
        if best_h:
            extracted_hard_skills.add(canonical_hard[best_h[0]])
            continue
        if key in canonical_soft:
            extracted_soft_skills.add(canonical_soft[key])
            continue
        best_s = difflib.get_close_matches(key, vocab_soft_keys, n=1, cutoff=0.78)
        if best_s:
            extracted_soft_skills.add(canonical_soft[best_s[0]])

    # EXPERIENCE section extraction for experience estimation
    text_lower = text.lower()
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
                if m.start() > start_idx and m.start() < end_idx:
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

        current_dt = __import__('datetime').datetime.now()
        current_year = current_dt.year
        current_month = current_dt.month

        def ym_to_index(y, m):
            return int(y) * 12 + int(m) - 1

        ranges = []

        month_regex = r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{4})\b\s*[-–—]\s*\b(?:(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{4})|(present|current))\b'
        for m in re.findall(month_regex, exp_section.lower()):
            start_m, start_y, end_m, end_y, present = m
            try:
                s_year = int(start_y)
                s_month = months_map.get(start_m, 1)
                if present in ['present', 'current']:
                    e_year = current_year
                    e_month = current_month
                else:
                    e_year = int(end_y)
                    e_month = months_map.get(end_m, 1)
                s_idx = ym_to_index(s_year, s_month)
                e_idx = ym_to_index(e_year, e_month)
                if e_idx >= s_idx:
                    ranges.append((s_idx, e_idx))
            except Exception:
                continue

        year_regex = r'\b(19\d{2}|20\d{2})\b\s*[-–—]\s*\b(19\d{2}|20\d{2}|present|current)\b'
        for start_yr, end_yr in re.findall(year_regex, exp_section.lower()):
            try:
                s_year = int(start_yr)
                if end_yr in ['present', 'current']:
                    e_year = current_year
                    e_month = current_month
                    e_idx = ym_to_index(e_year, e_month)
                else:
                    e_year = int(end_yr)
                    e_idx = ym_to_index(e_year, 1)
                s_idx = ym_to_index(s_year, 1)
                if e_idx >= s_idx:
                    ranges.append((s_idx, e_idx))
            except Exception:
                continue

        for ent in doc.ents:
            if ent.label_ == 'DATE' and '-' in ent.text:
                t = ent.text.lower()
                m = re.findall(month_regex, t)
                if m:
                    for mm in m:
                        start_m, start_y, end_m, end_y, present = mm
                        try:
                            s_year = int(start_y)
                            s_month = months_map.get(start_m, 1)
                            if present in ['present', 'current']:
                                e_year = current_year
                                e_month = current_month
                            else:
                                e_year = int(end_y)
                                e_month = months_map.get(end_m, 1)
                            s_idx = ym_to_index(s_year, s_month)
                            e_idx = ym_to_index(e_year, e_month)
                            if e_idx >= s_idx:
                                ranges.append((s_idx, e_idx))
                        except Exception:
                            continue

        total_months = 0
        if ranges:
            ranges.sort()
            merged = [list(ranges[0])]
            for s, e in ranges[1:]:
                if s <= merged[-1][1] + 1:
                    merged[-1][1] = max(merged[-1][1], e)
                else:
                    merged.append([s, e])
            for s, e in merged:
                total_months += max(1, e - s)
        calculated_exp = round(total_months / 12.0, 1)

        experience_years = max(experience_years, calculated_exp)

    return {
        "hard_skills": list(extracted_hard_skills),
        "soft_skills": list(extracted_soft_skills),
        "experience_years": experience_years,
    }


def parse_resume(pdf_path):
    """Convenience wrapper: extract text from PDF and parse it."""
    text = extract_text_from_pdf(pdf_path)
    return parse_text(text)
