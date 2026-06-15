# resume_parser.py
import os
import re
import json
import pymupdf4llm
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List

from job_roles import JOB_ROLES
import api_rotator


class ResumeProfile(BaseModel):
    is_resume: bool
    hard_skills: List[str]
    soft_skills: List[str]
    experience_years: float


def _extract_explicit_months(text):
    """Try to infer exact month-based experience durations from the resume text."""
    text_lower = text.lower()

    # Prefer explicit total experience patterns first.
    month_unit = r'(?:months?|mos?|mo\.?)'
    patterns = [
        r'experience\s*[:\-]?\s*(\d+)\s*(?:[-\s]?' + month_unit + r')',
        r'(\d+)\s*(?:[-\s]?' + month_unit + r')\s*(?:of\s*)?experience',
        r'^(\d+)\s*(?:[-\s]?' + month_unit + r')\b',
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower, re.MULTILINE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue

    # Support spelled-out month numbers like "six months".
    word_to_number = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
    }

    word_pattern = re.search(
        r'\b(' + '|'.join(word_to_number.keys()) + r')(?:[-\s]?' + month_unit + r')\b',
        text_lower
    )
    if word_pattern:
        return word_to_number.get(word_pattern.group(1), None)

    # Support common half-year phrasing.
    if re.search(r'\bhalf(?:[-\s]+year|\s+year)\b', text_lower):
        return 6

    # Fallback: look for any numeric month mentions.
    match = re.search(r'(\d+)\s*(?:[-\s]?months?|[-\s]?mos?)', text_lower)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass

    return None


def _normalize_experience_years(experience_years, text):
    """Normalize extracted experience by using exact month text when available."""
    if experience_years is None:
        return 0.0

    if experience_years < 1.0:
        explicit_months = _extract_explicit_months(text)
        if explicit_months is not None:
            return explicit_months / 12.0

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
    keys = api_rotator.get_all_keys()
    
    # Check if we have any non-empty keys
    valid_keys = [k for k in keys if k and k.strip()]
    if not valid_keys:
        raise ValueError("No valid Gemini API keys configured.")

    prompt = (
        f"Determine if the following text is a resume/CV. If the text is clearly not a resume or CV (e.g. it is a completely unrelated document, blank, random noise, or general text with no resume-like details such as work history, skills, contact info, or education), set `is_resume` to false.\n"
        f"Extract resume data from the following Markdown text.\n"
        f"In your extraction, normalize the extracted skills to match these canonical lists if they refer to the same concept (case-insensitive):\n"
        f"Canonical Hard Skills: {', '.join(canonical_hard)}\n"
        f"Canonical Soft Skills: {', '.join(canonical_soft)}\n\n"
        f"Resume Markdown:\n"
        f"{text}"
    )

    for attempt in range(len(keys)):
        api_key = rotator.get_current_key()
        if not api_key or not api_key.strip():
            # Skip empty keys
            rotator.mark_failed(api_key)
            if attempt < len(keys) - 1:
                rotator.rotate()
            continue

        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
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
                "hard_skills": data.get("hard_skills", []),
                "soft_skills": data.get("soft_skills", []),
                "experience_years": normalized_years,
            }
        except Exception as e:
            if "The uploaded file does not appear to be a valid resume" in str(e):
                raise e
            print(f"[Resume Parser] Gemini API key attempt {attempt + 1} failed: {e}")
            rotator.mark_failed(api_key)
            if attempt < len(keys) - 1:
                rotator.rotate()
                print(f"[Resume Parser] Rotating to next API key...")
            else:
                raise ValueError(f"All API keys failed. Last error: {e}")

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

