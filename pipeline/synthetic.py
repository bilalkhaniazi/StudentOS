"""Synthetic CS B.S. and Applied CS M.S. student records.

Invented coursework and grades only. No real names, student IDs, GPAs,
quality points, or degree dates.
"""

from __future__ import annotations

from typing import Any

CAREERS = [
    {
        "id": "data-engineer",
        "label": "Data Engineer",
        "shortLabel": "Data Engineer",
        "onetSoc": "15-1243.00",
        "onetTitle": "Database Architects",
        "summary": "Build pipelines, warehouses, and reliable data platforms. Catalog courses that often show up on this path include databases, cloud, and applied machine learning.",
    },
    {
        "id": "cloud-engineer",
        "label": "Cloud Engineer",
        "shortLabel": "Cloud",
        "onetSoc": "15-1299.08",
        "onetTitle": "Computer Systems Engineers/Architects",
        "summary": "Design and operate infrastructure and cloud platforms. Look at networking, operating systems, distributed systems, and cloud application courses.",
    },
    {
        "id": "backend-engineer",
        "label": "Backend Engineer",
        "shortLabel": "Backend",
        "onetSoc": "15-1252.00",
        "onetTitle": "Software Developers",
        "summary": "Build server-side applications and APIs. Software engineering, web programming, databases, and systems courses sit nearby in the catalog.",
    },
    {
        "id": "ml-engineer",
        "label": "ML Engineer",
        "shortLabel": "ML",
        "onetSoc": "15-2051.00",
        "onetTitle": "Data Scientists",
        "summary": "Train and ship machine-learning systems. Applied machine learning, data mining, databases, and statistics-adjacent CIS courses are the browse starting point.",
    },
]

# Keep JSON snapshot in sync for non-DB readers.
try:
    from api.app.career_path import enrich_career  # type: ignore

    CAREERS = [enrich_career(c) for c in CAREERS]
except Exception:
    pass


def _course(
    code: str,
    title: str,
    credit_hours: float,
    status: str,
    term: str,
    grade: str | None = None,
    level: str | None = None,
    term_source: str = "Period",
) -> dict[str, Any]:
    subject, number = code.split()
    return {
        "subject": subject,
        "courseNumber": number,
        "code": code,
        "level": level,
        "title": title,
        "creditHours": credit_hours,
        "gradeLetter": grade,
        "repeatFlag": None,
        "term": term,
        "termSource": term_source,
        "status": status,
    }


def _bs_base(**kwargs: Any) -> dict[str, Any]:
    row = {
        "institution": "GVSU",
        "transcriptLevel": "Undergraduate",
        "transcriptType": "Advising",
        "college": "College of Computing",
        "degreeLine": "Bachelor of Science",
        "major": "Computer Science",
        "majorAndDepartment": "Computer Science",
        "catalogYear": "2026-2027",
        "programId": "cs-bs",
        "transcriptReadAt": "2026-01-15T12:00:00+00:00",
        "targetCareer": None,
        "careerInterests": [],
        "careerSurvey": None,
        "remainingCredits": None,
        "termCreditPreference": "softCap15",
        "skills": [],
        "projects": [],
        "certifications": [],
        "curriculum": [
            {
                "kind": "degree",
                "status": "sought",
                "college": "College of Computing",
                "major": "Computer Science",
                "degreeDateOptional": None,
            }
        ],
        "courses": [],
        "editable": True,
        "synthetic": True,
    }
    row.update(kwargs)
    return row


def _ms_base(**kwargs: Any) -> dict[str, Any]:
    row = {
        "institution": "GVSU",
        "transcriptLevel": "Masters",
        "transcriptType": "Advising",
        "college": "College of Computing",
        "degreeLine": "Master of Science",
        "major": "Applied Computer Science",
        "majorAndDepartment": "Applied Computer Science",
        "catalogYear": "2026-2027",
        "programId": "applied-cs-ms",
        "transcriptReadAt": "2026-01-15T12:00:00+00:00",
        "targetCareer": None,
        "careerInterests": [],
        "careerSurvey": None,
        "remainingCredits": None,
        "termCreditPreference": "softCap15",
        "skills": [],
        "projects": [],
        "certifications": [],
        "curriculum": [
            {
                "kind": "degree",
                "status": "sought",
                "college": "College of Computing",
                "major": "Applied Computer Science",
                "degreeDateOptional": None,
            }
        ],
        "courses": [],
        "editable": True,
        "synthetic": True,
    }
    row.update(kwargs)
    return row


SYNTHETIC_STUDENTS: list[dict[str, Any]] = [
    _bs_base(
        syntheticId="synth-bs-data-eng",
        displayName="CS B.S. · Data Engineer example",
        targetCareer="data-engineer",
        careerInterests=["data pipelines", "cloud platforms", "SQL"],
        remainingCredits=28,
        summary="Databases, cloud, and applied ML coursework. Kafka, Airflow, and Terraform are still missing from the record.",
        skills=[
            {"label": "SQL", "evidence": "coursework"},
            {"label": "Python", "evidence": "coursework"},
            {"label": "Cloud computing", "evidence": "coursework"},
        ],
        courses=[
            _course("CIS 162", "Computer Science I", 4, "completed", "Fall 2022", "A"),
            _course("CIS 163", "Computer Science II", 4, "completed", "Winter 2023", "A-"),
            _course("CIS 241", "System-level Programming and Utilities", 3, "completed", "Fall 2023", "B+"),
            _course("CIS 263", "Data Structures and Algorithms", 3, "completed", "Winter 2024", "A"),
            _course("CIS 290", "Professional Responsibilities and Practices", 3, "completed", "Fall 2023", "A"),
            _course("CIS 351", "Computer Organization", 3, "completed", "Fall 2024", "B"),
            _course("CIS 343", "Structure of Programming Languages", 3, "completed", "Fall 2024", "B+"),
            _course("CIS 350", "Introduction to Software Engineering", 3, "completed", "Winter 2025", "B"),
            _course("CIS 353", "Database", 3, "completed", "Winter 2025", "A"),
            _course("CIS 457", "Data Communications", 3, "completed", "Fall 2025", "B"),
            _course("CIS 378", "Applied Machine Learning", 3, "completed", "Fall 2025", "A-"),
            _course("CIS 437", "Cloud Computing", 3, "completed", "Winter 2026", "B+"),
            _course("CIS 335", "Data Mining", 3, "completed", "Winter 2026", "A"),
            _course("CIS 452", "Operating Systems Concepts", 3, "in_progress", "Fall 2026", level=None, term_source="Term"),
        ],
    ),
    _bs_base(
        syntheticId="synth-bs-empty",
        displayName="CS B.S. · Empty profile",
        remainingCredits=120,
        summary="New undergraduate CS profile with no coursework yet.",
        courses=[],
    ),
    _bs_base(
        syntheticId="synth-bs-backend",
        displayName="CS B.S. · Backend-leaning",
        targetCareer="backend-engineer",
        careerInterests=["APIs", "web services", "databases"],
        remainingCredits=36,
        summary="Software engineering and web programming emphasis.",
        skills=[
            {"label": "Python", "evidence": "coursework"},
            {"label": "Web application programming", "evidence": "coursework"},
        ],
        projects=[
            {
                "name": "Campus events API",
                "summary": "REST API for student-org event listings.",
                "technologies": ["Python", "PostgreSQL"],
                "demonstratesSkills": ["API design", "SQL"],
            }
        ],
        courses=[
            _course("CIS 162", "Computer Science I", 4, "completed", "Fall 2023", "A-"),
            _course("CIS 163", "Computer Science II", 4, "completed", "Winter 2024", "B+"),
            _course("CIS 241", "System-level Programming and Utilities", 3, "completed", "Fall 2024", "B"),
            _course("CIS 263", "Data Structures and Algorithms", 3, "completed", "Winter 2025", "A-"),
            _course("CIS 290", "Professional Responsibilities and Practices", 3, "completed", "Fall 2024", "A"),
            _course("CIS 350", "Introduction to Software Engineering", 3, "completed", "Fall 2025", "A"),
            _course("CIS 353", "Database", 3, "completed", "Fall 2025", "B+"),
            _course("CIS 371", "Web Application Programming", 3, "completed", "Winter 2026", "A"),
            _course("CIS 343", "Structure of Programming Languages", 3, "completed", "Winter 2026", "B"),
            _course("CIS 351", "Computer Organization", 3, "in_progress", "Fall 2026", term_source="Term"),
        ],
    ),
    _bs_base(
        syntheticId="synth-bs-ml",
        displayName="CS B.S. · ML-leaning",
        targetCareer="ml-engineer",
        careerInterests=["machine learning", "data mining"],
        remainingCredits=40,
        summary="Applied machine learning and data mining electives on a CS B.S. core.",
        skills=[
            {"label": "Python", "evidence": "coursework"},
            {"label": "Machine learning", "evidence": "coursework"},
        ],
        courses=[
            _course("CIS 162", "Computer Science I", 4, "completed", "Fall 2023", "A"),
            _course("CIS 163", "Computer Science II", 4, "completed", "Winter 2024", "A"),
            _course("CIS 263", "Data Structures and Algorithms", 3, "completed", "Fall 2024", "A-"),
            _course("CIS 241", "System-level Programming and Utilities", 3, "completed", "Fall 2024", "B+"),
            _course("CIS 290", "Professional Responsibilities and Practices", 3, "completed", "Winter 2025", "A"),
            _course("CIS 353", "Database", 3, "completed", "Fall 2025", "A"),
            _course("CIS 335", "Data Mining", 3, "completed", "Winter 2026", "A"),
            _course("CIS 378", "Applied Machine Learning", 3, "completed", "Winter 2026", "A-"),
            _course("CIS 350", "Introduction to Software Engineering", 3, "in_progress", "Fall 2026", term_source="Term"),
        ],
    ),
    _bs_base(
        syntheticId="synth-bs-missing-prereq",
        displayName="CS B.S. · Missing prerequisites",
        targetCareer="data-engineer",
        remainingCredits=96,
        summary="Planning later CIS courses without the listed catalog prerequisites yet.",
        courses=[
            _course("CIS 162", "Computer Science I", 4, "completed", "Fall 2025", "B"),
            _course("CIS 353", "Database", 3, "planned", "Winter 2027"),
            _course("CIS 437", "Cloud Computing", 3, "planned", "Fall 2027"),
            _course("CIS 452", "Operating Systems Concepts", 3, "planned", "Fall 2027"),
        ],
    ),
    _bs_base(
        syntheticId="synth-bs-heavy-load",
        displayName="CS B.S. · Heavy remaining load",
        targetCareer="backend-engineer",
        remainingCredits=84,
        summary="Year-one CS complete; most required CIS courses still remain.",
        courses=[
            _course("CIS 162", "Computer Science I", 4, "completed", "Fall 2025", "B+"),
            _course("CIS 163", "Computer Science II", 4, "completed", "Winter 2026", "B"),
            _course("CIS 241", "System-level Programming and Utilities", 3, "in_progress", "Fall 2026", term_source="Term"),
        ],
    ),
    _ms_base(
        syntheticId="synth-ms-data-eng",
        displayName="Applied CS M.S. · Data Engineering track",
        targetCareer="data-engineer",
        careerInterests=["data engineering", "databases", "cloud"],
        remainingCredits=18,
        summary="Graduate data-engineering core plus cloud. Kafka, Airflow, and Terraform remain a gap versus the proposal example.",
        skills=[
            {"label": "SQL", "evidence": "coursework"},
            {"label": "Data engineering", "evidence": "coursework"},
            {"label": "Cloud applications", "evidence": "coursework"},
        ],
        courses=[
            _course("CIS 660", "Data Engineering", 3, "completed", "Fall 2025", "A", level="G"),
            _course("CIS 673", "Principles of Database Design", 3, "completed", "Winter 2026", "A", level="G"),
            _course("CIS 655", "Cloud Applications Development", 3, "completed", "Fall 2025", "B+", level="G"),
            _course("CIS 641", "Systems Analysis and Design", 3, "completed", "Winter 2026", "A-", level="G"),
            _course("CIS 656", "Distributed Systems", 3, "in_progress", "Fall 2026", level="G", term_source="Term"),
        ],
    ),
    _ms_base(
        syntheticId="synth-ms-empty",
        displayName="Applied CS M.S. · Empty profile",
        remainingCredits=33,
        summary="New Applied Computer Science M.S. profile with no coursework yet.",
        courses=[],
    ),
]


DEMO_PROFILE: dict[str, Any] = _bs_base(
    syntheticId="demo-profile",
    displayName="My demo profile",
    synthetic=False,
    remainingCredits=None,
    summary="Local demo profile you can create and edit. Not a campus account.",
    courses=[],
)
