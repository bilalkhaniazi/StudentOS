from __future__ import annotations

import unittest

from api.app.career_path import (
    apply_tilt_3a,
    build_career_path_payload,
    gap_label,
    score_career,
    survey_preference_scores,
    transcript_present,
)


CAREERS = [
    {
        "id": "data-engineer",
        "label": "Data Engineer",
        "summary": "Pipelines",
    },
    {
        "id": "cloud-engineer",
        "label": "Cloud Engineer",
        "summary": "Cloud",
    },
    {
        "id": "backend-engineer",
        "label": "Backend Engineer",
        "summary": "APIs",
    },
    {
        "id": "ml-engineer",
        "label": "ML Engineer",
        "summary": "Models",
    },
]

PROGRAMS = [
    {
        "id": "applied-cs-ms",
        "title": "Applied Computer Science, M.S.",
        "courses": [
            {"code": "CIS 660", "title": "Information Management", "section": "core-data-engineering"},
            {"code": "CIS 673", "title": "Distributed Data Systems", "section": "core-data-engineering"},
            {"code": "SE 512", "title": "Requirements", "section": "core-software-engineering"},
            {"code": "CIS 654", "title": "OS", "section": "core-systems-development"},
            {"code": "CIS 656", "title": "Networks", "section": "core-networking"},
            {"code": "CIS 693", "title": "Project", "section": "capstone"},
        ],
        "badges": [
            {"id": "database-management", "name": "Database Management"},
            {"id": "data-analytics", "name": "Data Analytics"},
        ],
        "rules": {"electives": {"note": "Reach 33 credits."}},
    }
]

CATALOG = [
    {
        "code": "CIS 353",
        "title": "Database",
        "description": "SQL and relational databases",
        "topics": ["sql", "database"],
        "credits_min": 3,
    },
    {
        "code": "CIS 660",
        "title": "Information Management",
        "description": "Data warehouses and ETL",
        "topics": ["etl", "warehouse"],
        "credits_min": 3,
    },
    {
        "code": "CIS 635",
        "title": "Knowledge Discovery",
        "description": "Machine learning with Python",
        "topics": ["machine learning", "python"],
        "credits_min": 3,
    },
]


class CareerPathTests(unittest.TestCase):
    def test_transcript_gate_requires_banner_context(self):
        self.assertFalse(transcript_present({"programId": "applied-cs-ms"}))
        self.assertTrue(transcript_present({"transcriptReadAt": "2026-10-02T00:00:00+00:00"}))
        self.assertTrue(transcript_present({"degreeLine": "Master of Science"}))
        self.assertTrue(
            transcript_present({"courses": [{"code": "CIS 160", "status": "completed"}]})
        )

    def test_gap_labels(self):
        self.assertEqual(gap_label(set()), "missing")
        self.assertEqual(gap_label({"self_report"}), "weak")
        self.assertEqual(gap_label({"coursework"}), "moderate")
        self.assertEqual(gap_label({"coursework", "project"}), "strong")

    def test_match_formula_uses_evidence(self):
        profile = {
            "transcriptReadAt": "2026-10-02T00:00:00+00:00",
            "programId": "applied-cs-ms",
            "courses": [
                {
                    "code": "CIS 353",
                    "title": "Database",
                    "status": "completed",
                    "gradeLetter": "A",
                }
            ],
            "skills": [{"label": "Python", "evidence": "resume"}],
            "projects": [
                {
                    "name": "ETL warehouse",
                    "summary": "Built SQL pipelines",
                    "technologies": ["Python", "SQL", "Airflow"],
                    "demonstratesSkills": ["etl"],
                },
                {
                    "name": "Kafka lab",
                    "summary": "Streaming",
                    "technologies": ["Kafka"],
                    "demonstratesSkills": [],
                },
            ],
            "certifications": [],
            "experiences": [],
        }
        scored = score_career("data-engineer", profile, CATALOG)
        self.assertGreaterEqual(scored["match"], 20)
        self.assertIn("factors", scored)
        self.assertEqual(set(scored["factors"]), {"S", "C", "P", "K"})

    def test_tilt_keeps_clear_leader(self):
        ranked = [
            {"careerId": "data-engineer", "match": 72},
            {"careerId": "cloud-engineer", "match": 50},
            {"careerId": "backend-engineer", "match": 40},
            {"careerId": "ml-engineer", "match": 30},
        ]
        answers = {
            "interestData": 1,
            "interestCloud": 5,
            "interestBackend": 1,
            "interestMl": 1,
            "workStyle": "cloud-ops",
            "tools": ["aws"],
        }
        out = apply_tilt_3a(ranked, answers)
        self.assertEqual(out[0]["careerId"], "data-engineer")
        self.assertTrue(out[0].get("recommended"))
        cloud = next(r for r in out if r["careerId"] == "cloud-engineer")
        self.assertTrue(cloud.get("yourInterest"))

    def test_tilt_breaks_close_race(self):
        ranked = [
            {"careerId": "data-engineer", "match": 55},
            {"careerId": "cloud-engineer", "match": 52},
            {"careerId": "backend-engineer", "match": 40},
            {"careerId": "ml-engineer", "match": 30},
        ]
        answers = {
            "interestData": 1,
            "interestCloud": 5,
            "interestBackend": 1,
            "interestMl": 1,
            "workStyle": "cloud-ops",
            "tools": ["docker", "aws"],
        }
        prefs = survey_preference_scores(answers)
        self.assertGreater(prefs["cloud-engineer"], prefs["data-engineer"])
        out = apply_tilt_3a(ranked, answers)
        self.assertEqual(out[0]["careerId"], "cloud-engineer")
        self.assertIn("Close evidence", out[0].get("reason", ""))

    def test_payload_blocks_without_transcript(self):
        profile = {"syntheticId": "x", "displayName": "Test", "courses": [], "skills": []}
        payload = build_career_path_payload(profile, CAREERS, PROGRAMS, CATALOG)
        self.assertFalse(payload["ready"])
        self.assertEqual(payload["rankings"], [])

    def test_payload_path_with_zero_courses(self):
        profile = {
            "syntheticId": "x",
            "displayName": "Test",
            "transcriptReadAt": "2026-10-02T00:00:00+00:00",
            "transcriptLevel": "Masters",
            "programId": "applied-cs-ms",
            "degreeLine": "Master of Science",
            "courses": [],
            "skills": [],
            "projects": [],
            "experiences": [],
            "certifications": [],
            "badges": [],
            "careerSurvey": {
                "answeredAt": "2026-10-02T00:00:00+00:00",
                "answers": {
                    "interestData": 5,
                    "interestCloud": 2,
                    "interestBackend": 2,
                    "interestMl": 2,
                    "workStyle": "data-systems",
                    "tools": ["sql", "python"],
                },
            },
        }
        payload = build_career_path_payload(profile, CAREERS, PROGRAMS, CATALOG)
        self.assertTrue(payload["ready"])
        self.assertEqual(len(payload["rankings"]), 4)
        self.assertIsNotNone(payload["path"])
        self.assertEqual(payload["path"]["programId"], "applied-cs-ms")
        self.assertTrue(payload["path"]["buckets"])
        self.assertTrue(payload["path"]["suggestedCourses"])


if __name__ == "__main__":
    unittest.main()
