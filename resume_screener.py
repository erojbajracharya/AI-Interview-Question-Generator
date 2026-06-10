# resume_screener.py
"""
Resume Screener using Simple Linear Regression.

Computes three features from the resume vs. job role:
  X1 = hard skill match ratio   (0.0 - 1.0)
  X2 = soft skill match ratio   (0.0 - 1.0)
  X3 = experience match ratio   (0.0 - 1.0, capped at 1)

A linear regression model predicts the overall match score:
  match_score = w1*X1 + w2*X2 + w3*X3 + bias

The weights were chosen to reflect hiring priorities:
  - Hard skills matter the most  (50%)
  - Experience matters next      (30%)
  - Soft skills round it out     (20%)

Threshold: >= 51% -> PASS, < 51% -> REJECT
"""

import numpy as np
from job_roles import JOB_ROLES


# ── Linear Regression Coefficients ──────────────────────────────
# These represent a pre-trained linear regression: y = X @ W + b
# Weights reflect typical hiring priorities.
WEIGHTS = np.array([0.50, 0.20, 0.30])   # [hard, soft, experience]
BIAS = 0.0                                # no artificial boost

PASS_THRESHOLD = 0.51  # 51%


def _compute_features(resume_data: dict, role_key: str) -> dict:
    """
    Extracts the three regression features from a parsed resume
    and a target job role.

    Returns a dict with individual ratios and the feature vector.
    """
    role = JOB_ROLES.get(role_key)
    if not role:
        raise ValueError(f"Unknown role key: {role_key}")

    # ── 1. Hard-skill match ratio ───────────────────────────────
    required_hard = set(s.lower() for s in role["hard_skills"])
    candidate_hard = set(s.lower() for s in resume_data.get("hard_skills", []))
    hard_matched = required_hard & candidate_hard
    hard_ratio = len(hard_matched) / len(required_hard) if required_hard else 0.0

    # ── 2. Soft-skill match ratio ───────────────────────────────
    required_soft = set(s.lower() for s in role["soft_skills"])
    candidate_soft = set(s.lower() for s in resume_data.get("soft_skills", []))
    soft_matched = required_soft & candidate_soft
    soft_ratio = len(soft_matched) / len(required_soft) if required_soft else 0.0

    # ── 3. Experience match ratio ───────────────────────────────
    exp_reqs = role["experience_requirements"]
    # Use intermediate as a reasonable baseline expectation
    expected_exp = exp_reqs.get("intermediate", 2)
    candidate_exp = resume_data.get("experience_years", 0)

    if expected_exp == 0:
        exp_ratio = 1.0  # no experience required -> full match
    else:
        exp_ratio = min(candidate_exp / expected_exp, 1.0)

    feature_vector = np.array([hard_ratio, soft_ratio, exp_ratio])

    return {
        "hard_ratio": hard_ratio,
        "soft_ratio": soft_ratio,
        "exp_ratio": exp_ratio,
        "hard_matched": sorted(hard_matched),
        "hard_required": sorted(required_hard),
        "soft_matched": sorted(soft_matched),
        "soft_required": sorted(required_soft),
        "features": feature_vector,
    }


def screen_resume(resume_data: dict, role_key: str) -> dict:
    """
    Screens a parsed resume against a job role using linear regression.

    Parameters
    ----------
    resume_data : dict   – output of resume_parser.parse_resume()
    role_key    : str    – key from JOB_ROLES (e.g. "software_engineer")

    Returns
    -------
    dict with:
        match_score   : float (0-100, percentage)
        passed        : bool
        details       : dict of per-feature ratios and matched items
    """
    details = _compute_features(resume_data, role_key)
    X = details["features"]

    # ── Linear regression prediction ────────────────────────────
    # y = X · W + b   (simple dot product)
    raw_score = float(np.dot(X, WEIGHTS) + BIAS)

    # Clamp to [0, 1] (regression can theoretically exceed bounds)
    raw_score = max(0.0, min(1.0, raw_score))

    match_pct = round(raw_score * 100, 1)
    passed = match_pct >= (PASS_THRESHOLD * 100)

    return {
        "match_score": match_pct,
        "passed": passed,
        "details": details,
    }


def format_screening_report(result: dict, role_title: str) -> str:
    """Returns a human-readable screening summary string."""
    d = result["details"]
    status = "✅ PASSED" if result["passed"] else "❌ REJECTED"
    lines = [
        "═" * 50,
        "RESUME SCREENING REPORT",
        "═" * 50,
        f"Target Role     : {role_title}",
        f"Match Score     : {result['match_score']}%",
        f"Threshold       : {PASS_THRESHOLD * 100:.0f}%",
        f"Decision        : {status}",
        "─" * 50,
        f"Hard Skills     : {d['hard_ratio']:.0%}  ({len(d['hard_matched'])}/{len(d['hard_required'])})",
        f"  Matched       : {', '.join(d['hard_matched']) or 'None'}",
        f"  Missing       : {', '.join(sorted(set(d['hard_required']) - set(d['hard_matched']))) or 'None'}",
        f"Soft Skills     : {d['soft_ratio']:.0%}  ({len(d['soft_matched'])}/{len(d['soft_required'])})",
        f"  Matched       : {', '.join(d['soft_matched']) or 'None'}",
        f"  Missing       : {', '.join(sorted(set(d['soft_required']) - set(d['soft_matched']))) or 'None'}",
        f"Experience      : {d['exp_ratio']:.0%}",
        "─" * 50,
        f"Predicted Score : {result['match_score']}%",
        "═" * 50,
    ]
    return "\n".join(lines)
