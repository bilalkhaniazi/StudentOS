from __future__ import annotations

import unittest

from api.app.resume import merge_resume_into_profile, parse_resume_text


SAMPLE_A = """
Jordan Lee
jordan.lee@mail.gvsu.edu | (616) 555-0142
Grand Rapids, MI

SUMMARY
Applied Computer Science graduate student seeking a data engineering role. Familiar with Python, SQL, and cloud pipelines.

EXPERIENCE
Software Engineering Intern — Acme Analytics
May 2024 - August 2024
Grand Rapids, MI
- Built Python ETL jobs that loaded daily sales data into PostgreSQL
- Automated quality checks with Pandas and SQL

Research Assistant | GVSU College of Computing
Jan 2023 – Present
- Supported faculty projects on information visualization
- Presented findings to a weekly lab group

PROJECTS
StudentOS Course Planner — Python, FastAPI, React
- Mapped degree pathways and remaining requirements for Applied CS M.S.
Campus Events API | Node.js, MongoDB
- Designed REST endpoints for event discovery

SKILLS
Python, SQL, PostgreSQL, Docker, React, Git, AWS, Pandas

EDUCATION
Grand Valley State University
M.S. Applied Computer Science
2025 - Present

Grand Valley State University
B.S. Computer Science
2021 - 2025

LANGUAGES
English (Fluent), Spanish - Intermediate

CERTIFICATIONS
AWS Cloud Practitioner
"""


SAMPLE_B = """
ALEX MORGAN
alex@example.com

Work Experience
Data Analyst Intern at Bright Labs
06/2023 to 12/2023
• Cleaned messy CSVs with Python
• Built Tableau dashboards for stakeholders

Technical Skills
Java; Spring; MySQL; Git; Linux

Education
Bachelor of Science in Computer Science - State University
2019 - 2023

International student on F-1 visa seeking OPT.
"""


class ResumeParseTests(unittest.TestCase):
    def test_structured_resume(self):
        parsed = parse_resume_text(SAMPLE_A)
        self.assertTrue(parsed.summary)
        self.assertGreaterEqual(len(parsed.experiences), 2)
        titles = {e["title"] for e in parsed.experiences}
        self.assertTrue(any("Intern" in t or "Assistant" in t for t in titles))
        current = [e for e in parsed.experiences if e.get("current")]
        self.assertTrue(current)
        self.assertGreaterEqual(len(parsed.projects), 2)
        skill_labels = {s["label"].lower() for s in parsed.skills}
        self.assertIn("python", skill_labels)
        self.assertIn("postgresql", skill_labels)
        self.assertGreaterEqual(len(parsed.education), 1)
        langs = {l["name"].lower() for l in parsed.languages}
        self.assertIn("english", langs)
        self.assertIn("spanish", langs)
        self.assertTrue(parsed.certifications)

    def test_alternate_headings_and_intl_hint(self):
        parsed = parse_resume_text(SAMPLE_B)
        self.assertGreaterEqual(len(parsed.experiences), 1)
        self.assertEqual(parsed.experiences[0]["organization"], "Bright Labs")
        self.assertGreaterEqual(len(parsed.skills), 3)
        self.assertEqual(parsed.studentTypeHint, "international")

    def test_empty_does_not_crash(self):
        parsed = parse_resume_text("   ")
        self.assertEqual(parsed.experiences, [])
        self.assertTrue(parsed.warnings)

    def test_merge_does_not_duplicate(self):
        parsed = parse_resume_text(SAMPLE_A)
        props = {
            "summary": None,
            "skills": [{"label": "Python", "evidence": "self_report"}],
            "projects": [],
            "experiences": [],
            "education": [],
            "languages": [],
            "certifications": [],
        }
        merge_resume_into_profile(props, parsed)
        merge_resume_into_profile(props, parsed)
        py = [s for s in props["skills"] if s["label"].lower() == "python"]
        self.assertEqual(len(py), 1)
        self.assertTrue(props["summary"])
        self.assertGreaterEqual(len(props["experiences"]), 2)


if __name__ == "__main__":
    unittest.main()
