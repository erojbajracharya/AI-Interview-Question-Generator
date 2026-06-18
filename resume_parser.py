# resume_parser.py
import os
import re
import json
import datetime
import pymupdf4llm
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

from job_roles import JOB_ROLES
import api_rotator


class ResumeProfile(BaseModel):
    is_resume: bool
    full_name: str
    hard_skills: List[str]
    soft_skills: List[str]
    experience_years: float


def _extract_explicit_experience(text):
    """Try to infer exact experience durations from the resume text."""
    text_lower = text.lower()

    # Look for patterns like "5 years of experience" or "6 months experience"
    month_unit = r'(?:months?|mos?|mo\.?)'
    year_unit = r'(?:years?|yrs?|yr\.?)'

    # Check for years first
    year_patterns = [
        r'experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:[-\s]?' + year_unit + r')',
        r'(\d+(?:\.\d+)?)\s*(?:[-\s]?' + year_unit + r')\s*(?:of\s*)?experience',
        r'^(\d+(?:\.\d+)?)\s*(?:[-\s]?' + year_unit + r')\b',
    ]
    for pattern in year_patterns:
        match = re.search(pattern, text_lower, re.MULTILINE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue

    # Then check for months
    month_patterns = [
        r'experience\s*[:\-]?\s*(\d+)\s*(?:[-\s]?' + month_unit + r')',
        r'(\d+)\s*(?:[-\s]?' + month_unit + r')\s*(?:of\s*)?experience',
        r'^(\d+)\s*(?:[-\s]?' + month_unit + r')\b',
    ]

    for pattern in month_patterns:
        match = re.search(pattern, text_lower, re.MULTILINE)
        if match:
            try:
                return int(match.group(1)) / 12.0
            except ValueError:
                continue

    # Support spelled-out month numbers like "six months".
    word_to_number = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    }

    word_pattern = re.search(
        r'\b(' + '|'.join(word_to_number.keys()) + r')(?:[-\s]?' + month_unit + r')\b',
        text_lower
    )
    if word_pattern:
        return word_to_number.get(word_pattern.group(1)) / 12.0

    # Support common half-year phrasing.
    if re.search(r'\bhalf(?:[-\s]+year|\s+year)\b', text_lower):
        return 0.5

    return None


def _normalize_experience_years(experience_years, text):
    """Normalize extracted experience by using exact text mentions when available."""
    if experience_years is None:
        experience_years = 0.0

    explicit_val = _extract_explicit_experience(text)
    if explicit_val is not None:
        # Heuristic: if an explicit mention of "X years of experience" is found and it is
        # greater than what the LLM extracted, prefer the explicit mention.
        if explicit_val > experience_years:
            return explicit_val

    return experience_years


def convert_pdf_to_md(pdf_path):
    """Converts a PDF file to a Markdown (.md) file next to the original PDF."""
    md_content = pymupdf4llm.to_markdown(pdf_path)
    md_path = os.path.splitext(pdf_path)[0] + ".md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    return md_path


def parse_text(text):
    """Parses resume text using the Gemini API with key rotation and structured JSON output."""
    # Gather canonical skills list from JOB_ROLES
    all_hard_skills = set()
    all_soft_skills = set()
    for role_info in JOB_ROLES.values():
        all_hard_skills.update(role_info["hard_skills"])
        all_soft_skills.update(role_info["soft_skills"])

    canonical_hard = sorted(list(all_hard_skills))
    canonical_soft = sorted(list(all_soft_skills))

    rotator = api_rotator.get_rotator()
    rotator.reset()
    
    if rotator.is_offline:
        raise ValueError("Offline mode: No API keys configured.")

    # Get current date for accurate experience calculation (dynamic for any year: 2026, 2027, 2030, etc.)
    today = datetime.date.today()
    current_date_str = today.strftime("%B %Y")

    prompt = f"""
    You are an expert resume parser.

    Current Date: {current_date_str}

    Task:
    Extract structured resume data.

    Rules:
    - Determine whether the document is a resume/CV.
    - Extract full name, education, work history, and skills.
    - Calculate total professional experience.
    - For active roles (Present, Current, Ongoing, To Date), use {current_date_str}.
    - Sum role durations and return experience_years rounded to 1 decimal.

    Skills:
    - Extract ONLY from dedicated Skills/Technical Skills sections.
    - Ignore skills mentioned in experience, projects, education, certifications, or summaries.
    - Normalize skills using the provided canonical lists.
    - Remove duplicates.
    - Do not infer or invent skills.

    Allowed Hard Skills:
    {', '.join(canonical_hard)}

    Allowed Soft Skills:
    {', '.join(canonical_soft)}

    Document:
    {text}

    Return only schema-compliant output.
    """

    attempt = 0
    while True:
        api_key = rotator.get_current_key()
        if not api_key or not api_key.strip():
            # Skip empty keys
            rotator.mark_failed(api_key)
            rotator.rotate()
            attempt += 1
            if attempt >= len(api_rotator.get_all_keys()) * 3:
                break
            continue

        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-3-flash-preview',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ResumeProfile,
                ),
            )
            data = json.loads(response.text)
            if not data.get("is_resume", True):
                print("[Resume Parser] Error: The uploaded file is not a resume.")
                raise ValueError("The uploaded file does not appear to be a valid resume.")
                
            extracted_years = float(data.get("experience_years", 0.0))
            normalized_years = _normalize_experience_years(extracted_years, text)
            return {
                "full_name": data.get("full_name", "Unknown Candidate"),
                "hard_skills": data.get("hard_skills", []),
                "soft_skills": data.get("soft_skills", []),
                "experience_years": normalized_years,
            }
        except Exception as e:
            if "The uploaded file does not appear to be a valid resume" in str(e):
                raise e
            attempt += 1
            print(f"[Resume Parser] Gemini API key attempt {attempt} failed: {e}")
            rotator.mark_failed(api_key)
            
            if attempt < len(api_rotator.get_all_keys()) * 3:
                rotator.rotate()
                print(f"[Resume Parser] Rotating to next API key (attempt {attempt + 1})...")
                import time
                time.sleep(1)
            else:
                raise ValueError(f"All API keys failed after multiple cycles. Last error: {e}")

    raise ValueError("All API keys failed.")


def parse_resume(pdf_path):
    """Convenience wrapper: convert PDF to Markdown file, parse, and clean up."""
    md_path = None
    try:
        md_path = convert_pdf_to_md(pdf_path)
        with open(md_path, "r", encoding="utf-8") as f:
            text = f.read()
        return parse_text(text)
    finally:
        if md_path and os.path.exists(md_path):
            try:
                os.remove(md_path)
            except Exception as e:
                print(f"[Resume Parser] Error cleaning up temporary markdown file: {e}")

