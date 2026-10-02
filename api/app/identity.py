"""Map a signed-in GVSU Google account to one academic profile."""

from __future__ import annotations

import hashlib


def profile_id_for_email(email: str) -> str:
    key = (email or "").strip().lower()
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"u-{digest}"


def empty_profile(profile_id: str, *, email: str, display_name: str) -> dict:
    return {
        "syntheticId": profile_id,
        "displayName": display_name,
        "email": email,
        "institution": "GVSU",
        "transcriptLevel": None,
        "transcriptType": "Advising",
        "college": None,
        "degreeLine": None,
        "major": None,
        "majors": [],
        "majorAndDepartment": None,
        "badges": [],
        "catalogYear": "2026-2027",
        "targetCareer": None,
        "careerInterests": [],
        "remainingCredits": None,
        "termCreditPreference": "softCap15",
        "summary": None,
        "studentType": None,
        "programId": None,
        "transcriptReadAt": None,
        "transcriptFilename": None,
        "careerSurvey": None,
        "skills": [],
        "projects": [],
        "experiences": [],
        "education": [],
        "languages": [],
        "certifications": [],
        "curriculum": [],
        "courses": [],
        "resumeFilename": None,
        "resumeReadAt": None,
        "resumeParsed": None,
        "editable": True,
        "synthetic": False,
    }
