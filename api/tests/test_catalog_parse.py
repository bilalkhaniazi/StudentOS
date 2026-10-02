from __future__ import annotations

import unittest

from pipeline.ingest import parse_badge_page, parse_credits, parse_program_page


class CreditParseTests(unittest.TestCase):
    def test_listing_credits(self):
        self.assertEqual(parse_credits("4 credits"), (4.0, 4.0, "4"))
        self.assertEqual(parse_credits("2 to 5 credits"), (2.0, 5.0, "2 to 5"))
        self.assertEqual(parse_credits("Credits: 3"), (3.0, 3.0, "3"))
        self.assertEqual(parse_credits("Credits: 1 to 4"), (1.0, 4.0, "1 to 4"))


class ProgramParseTests(unittest.TestCase):
    def test_bs_required_and_elective_credits(self):
        html = """
        <html><body><main>
        <h2>Required Computer Science Courses</h2>
        <p>CIS 162 - Computer Science I (4 credits)</p>
        <p>CIS 163 - Computer Science II (4 credits)</p>
        <p>CIS 467 - Computer Science Project (3 credits) (Capstone course)</p>
        <h2>Elective Computer Science Courses</h2>
        <p>Computer science majors must select four electives from the following:</p>
        <p>CIS 335 - Data Mining (3 credits)</p>
        <p>CIS 378 - Applied Machine Learning (3 credits)</p>
        <h2>Required Non-Computing Courses</h2>
        <p>STA 215 - Introductory Applied Statistics (3 credits) OR STA 312 - Probability and Statistics (3 credits) OR STA 330 - Probability and Statistics for Computing (3 credits)</p>
        <h2>Suggested Order of Coursework</h2>
        <p>Year One</p>
        <p>CIS 162 - Computer Science I (4 credits)</p>
        </main></body></html>
        """
        parsed = parse_program_page(html, "cs-bs", "https://example.test/cs-bs")
        by_section = {}
        for row in parsed["courses"]:
            by_section.setdefault(row["section"], []).append(row)
        self.assertEqual({c["code"] for c in by_section["required"]}, {"CIS 162", "CIS 163", "CIS 467"})
        self.assertEqual(by_section["required"][0]["credits_min"], 4.0)
        self.assertEqual({c["code"] for c in by_section["elective"]}, {"CIS 335", "CIS 378"})
        self.assertEqual(parsed["rules"]["electives"]["choose"], 4)
        self.assertEqual({c["code"] for c in by_section["stats-choice"]}, {"STA 215", "STA 312", "STA 330"})
        self.assertEqual(parsed["suggested_order"][0]["year"], "Year One")
        self.assertEqual(parsed["suggested_order"][0]["code"], "CIS 162")

    def test_ms_core_areas(self):
        html = """
        <html><body><main>
        <p>The program consists of 11 three-credit courses (33 credit hours).</p>
        <h2>Core Courses</h2>
        <p>1. Data Engineering</p>
        <p>CIS 660 - Data Engineering (3 credits)</p>
        <p>CIS 673 - Principles of Database Design (3 credits)</p>
        <p>2. Management of Systems Development</p>
        <p>CIS 641 - Systems Analysis and Design (3 credits)</p>
        <h2>Capstone</h2>
        <p>CIS 693 - Master's Project (3 credits)</p>
        <p>CIS 695 - Master's Thesis (3 credits)</p>
        </main></body></html>
        """
        parsed = parse_program_page(html, "applied-cs-ms", "https://example.test/ms")
        self.assertEqual(parsed["rules"]["total_credits"], 33)
        self.assertEqual(parsed["rules"]["core"]["choose_areas"], 3)
        sections = {c["code"]: c["section"] for c in parsed["courses"]}
        self.assertEqual(sections["CIS 660"], "core-data-engineering")
        self.assertEqual(sections["CIS 641"], "core-systems-development")
        self.assertEqual(sections["CIS 693"], "capstone")
        self.assertEqual(parsed["courses"][0]["credits_min"], 3.0)


class BadgeParseTests(unittest.TestCase):
    def test_database_management_required_plus_choose(self):
        html = """
        <html><body><main>
        <p>The Database Management badge is three courses (9 credits).</p>
        <p>Students must take:</p>
        <p>CIS 673 - Principles of Database Design (3 credits)</p>
        <p>AND two of the following:</p>
        <p>CIS 660 - Data Engineering (3 credits)</p>
        <p>CIS 676 - Database Architecture (3 credits)</p>
        </main></body></html>
        """
        badge = parse_badge_page(
            html,
            "database-management",
            {"name": "Database Management", "url": "https://example.test/badge"},
        )
        self.assertEqual(badge["credits"], 9)
        kinds = [s["kind"] for s in badge["slots"]]
        self.assertEqual(kinds, ["all", "choose_n"])
        self.assertEqual(badge["slots"][0]["courses"][0]["code"], "CIS 673")
        self.assertEqual(badge["slots"][1]["n"], 2)
        self.assertEqual({c["code"] for c in badge["slots"][1]["courses"]}, {"CIS 660", "CIS 676"})

    def test_or_slots(self):
        html = """
        <html><body><main>
        <p>SE 511 - Introduction to Software Engineering (3 credits) OR CIS 641 - Systems Analysis and Design (3 credits)</p>
        <p>CIS 657 - Mobile Application Development (3 credits) OR CIS 658 - Web Architectures (3 credits)</p>
        </main></body></html>
        """
        badge = parse_badge_page(
            html,
            "software-design-and-development",
            {"name": "Software Design and Development", "url": "https://example.test/sdd"},
        )
        self.assertEqual(len(badge["slots"]), 2)
        self.assertTrue(all(s["kind"] == "choose_n" and s["n"] == 1 for s in badge["slots"]))


if __name__ == "__main__":
    unittest.main()
