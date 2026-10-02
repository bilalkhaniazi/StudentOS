from __future__ import annotations

import unittest

from api.app.banner import attach_catalog, parse_banner, remaining_credits

CLEAN = """
Academic Transcript
Transcript Level
Masters
Transcript Type
Advising
Student Information
Curriculum Information
Master of Science
College
College of Computing
Major and Department
Applied Computer Science, Undeclared
Institution Credit
Period : Fall 2025
Subject Course Level Title Grade Credit Hours Quality Points
CIS 660 G Data Engineering A 3.000 12.00
CIS 655 G Cloud Applications Development B+ 3.000 9.90
Period : Winter 2026
CIS 673 G Principles of Database Design A- 3.000 11.10
Course(s) in Progress
Term : Fall 2026
Subject Course Level Title Credit Hours
CIS 656 G Distributed Systems 3.000
CIS 693 G Master's Project 3.000
"""

OCR_MESSY = """
Academic Transcript
Transcript Level
Masters
Advising
Curriculum Information
Master of Science
College of Computing
Applied Computer
Science, Undeclared
Institution Credit
Period : Winter 2025
Subject
Course
Level
Grade
Credit Hours
Title
Quality Points
SID
613
Software Testing
3.000
A-
11.10
SID
655
3.000
Cloud Applications Development
12.00
SID
Data Engineering
3.000
660
12.00
Course(s) in Progress
Term : Fall 2026
SID
671
Information Visualization
3.000
SID
569
Master's Project
3.000
"""

CATALOG = [
    {"code": "CIS 655", "subject": "CIS", "course_number": "655", "title": "Cloud Applications Development"},
    {"code": "CIS 656", "subject": "CIS", "course_number": "656", "title": "Distributed Systems"},
    {"code": "CIS 660", "subject": "CIS", "course_number": "660", "title": "Data Engineering"},
    {"code": "CIS 671", "subject": "CIS", "course_number": "671", "title": "Information Visualization"},
    {"code": "CIS 673", "subject": "CIS", "course_number": "673", "title": "Principles of Database Design"},
    {"code": "CIS 693", "subject": "CIS", "course_number": "693", "title": "Master's Project"},
    {"code": "CIS 695", "subject": "CIS", "course_number": "695", "title": "Master's Thesis"},
    {"code": "SE 513", "subject": "SE", "course_number": "513", "title": "Software Testing"},
    {"code": "CIS 554", "subject": "CIS", "course_number": "554", "title": "Computer Networking"},
    {"code": "CIS 641", "subject": "CIS", "course_number": "641", "title": "Systems Analysis and Design"},
    {"code": "CIS 642", "subject": "CIS", "course_number": "642", "title": "IS Project Management"},
    {"code": "CIS 518", "subject": "CIS", "course_number": "518", "title": "Secure Software Engineering"},
]

PROGRAMS = [
    {
        "id": "applied-cs-ms",
        "level": "Masters",
        "major": "Applied Computer Science",
        "courses": [
            {"code": "CIS 660", "subject": "CIS", "course_number": "660", "title": "Data Engineering", "section": "core-data-engineering"},
            {"code": "CIS 673", "subject": "CIS", "course_number": "673", "title": "Principles of Database Design", "section": "core-data-engineering"},
            {"code": "CIS 641", "subject": "CIS", "course_number": "641", "title": "Systems Analysis and Design", "section": "core-systems-development"},
            {"code": "CIS 642", "subject": "CIS", "course_number": "642", "title": "IS Project Management", "section": "core-systems-development"},
            {"code": "CIS 518", "subject": "CIS", "course_number": "518", "title": "Secure Software Engineering", "section": "core-software-engineering"},
            {"code": "SE 513", "subject": "SE", "course_number": "513", "title": "Software Testing", "section": "core-software-engineering"},
            {"code": "CIS 554", "subject": "CIS", "course_number": "554", "title": "Computer Networking", "section": "core-networking"},
            {"code": "CIS 656", "subject": "CIS", "course_number": "656", "title": "Distributed Systems", "section": "core-networking"},
            {"code": "CIS 693", "subject": "CIS", "course_number": "693", "title": "Master's Project", "section": "capstone"},
            {"code": "CIS 695", "subject": "CIS", "course_number": "695", "title": "Master's Thesis", "section": "capstone"},
        ],
    }
]


class BannerParseTests(unittest.TestCase):
    def test_clean_masters_layout(self):
        parsed = parse_banner(CLEAN)
        self.assertEqual(parsed.transcriptLevel, "Masters")
        self.assertEqual(parsed.college, "College of Computing")
        self.assertEqual(parsed.degreeLine, "Master of Science")
        self.assertEqual(parsed.major, "Applied Computer Science")
        codes = {(c.code, c.status) for c in parsed.courses}
        self.assertIn(("CIS 660", "completed"), codes)
        self.assertIn(("CIS 655", "completed"), codes)
        self.assertIn(("CIS 673", "completed"), codes)
        self.assertIn(("CIS 656", "in_progress"), codes)
        self.assertIn(("CIS 693", "in_progress"), codes)
        data_eng = next(c for c in parsed.courses if c.code == "CIS 660")
        self.assertEqual(data_eng.gradeLetter, "A")
        self.assertEqual(data_eng.term, "Fall 2025")
        self.assertEqual(data_eng.creditHours, 3.0)

    def test_ocr_sid_and_title_recovery(self):
        parsed = parse_banner(OCR_MESSY, method="ocr")
        parsed = attach_catalog(parsed, CATALOG, PROGRAMS)
        completed = {c.code: c for c in parsed.completed()}
        self.assertIn("CIS 655", completed)
        self.assertIn("CIS 660", completed)
        self.assertEqual(completed["CIS 655"].gradeLetter, "A")
        self.assertEqual(completed["CIS 660"].gradeLetter, "A")
        # OCR often reads CIS as SID and 693 as another 3-digit number; title wins.
        self.assertTrue(any(c.code == "SE 513" for c in parsed.completed()))
        self.assertTrue(any(c.code == "CIS 693" and c.status == "in_progress" for c in parsed.courses))
        self.assertTrue(any(c.code == "CIS 671" and c.status == "in_progress" for c in parsed.courses))
        remaining_codes = {c.code for c in parsed.courses if c.status == "planned"}
        self.assertIn("CIS 641", remaining_codes)
        self.assertNotIn("CIS 660", remaining_codes)
        self.assertNotIn("CIS 693", remaining_codes)
        self.assertNotIn("CIS 695", remaining_codes)

    def test_does_not_keep_identity_lines(self):
        text = CLEAN.replace("Student Information", "Student Information\nName\nDemo Student\nG00000001")
        parsed = parse_banner(text)
        blob = " ".join(c.title or "" for c in parsed.courses)
        self.assertNotIn("Demo Student", blob)
        self.assertNotIn("G00000001", blob)

    def test_remaining_credits_masters(self):
        parsed = parse_banner(CLEAN)
        parsed = attach_catalog(parsed, CATALOG, PROGRAMS)
        # 9 completed + 6 in progress = 15 toward 33
        self.assertEqual(remaining_credits(parsed), 18.0)

    def test_undergraduate_program_pick(self):
        text = """
        Academic Transcript
        Transcript Level
        Undergraduate
        Bachelor of Science
        College of Computing
        Computer Science
        Institution Credit
        Period : Fall 2024
        CIS 162 U Computer Science I A 3.000 12.00
        """
        parsed = parse_banner(text)
        self.assertEqual(parsed.transcriptLevel, "Undergraduate")
        self.assertEqual(parsed.major, "Computer Science")
        self.assertEqual(parsed.courses[0].code, "CIS 162")

    def test_page1_toc_does_not_skip_institution_credit(self):
        text = """
        Academic Transcript
        Transcript Level
        Transcript Type
        Masters
        Advising
        Student Information
        Institution Credit
        Awarded
        Transcript Totals
        Course(s) in Progress
        This is not an official transcript.
        Student Information
        Curriculum Information
        Master of Science
        College of Computing
        Applied Computer Science, Undeclared
        Awarded
        Awarded
        Institution Credit
        Period : Winter 2025
        SID 613 Software Testing A- 3.000 11.10
        SID 655 Cloud Applications Development 3.000 12.00
        SID Data Engineering 3.000 660 12.00
        Period : Fall 2025
        SID 622 B+ 3.000 Software Design Methodologies 9.90
        SID 656 Distributed Systems 3.000 12.00
        SID 673 Principles of Database Design 3.000 12.00
        Transcript Totals
        Course(s) in Progress
        Term : Fall 2026
        SID 671 Information Visualization 3.000
        SID 569 Master's Project 3.000
        """
        parsed = parse_banner(text, method="ocr")
        parsed = attach_catalog(parsed, CATALOG, PROGRAMS)
        completed = {c.code: c for c in parsed.completed()}
        in_progress = {c.code: c for c in parsed.in_progress()}
        self.assertEqual(parsed.transcriptLevel, "Masters")
        self.assertEqual(parsed.major, "Applied Computer Science")
        self.assertIn("SE 513", completed)
        self.assertIn("CIS 655", completed)
        self.assertIn("CIS 660", completed)
        self.assertIn("CIS 656", completed)
        self.assertIn("CIS 673", completed)
        self.assertEqual(completed["CIS 655"].term, "Winter 2025")
        self.assertEqual(completed["CIS 656"].term, "Fall 2025")
        self.assertIn("CIS 671", in_progress)
        self.assertIn("CIS 693", in_progress)
        self.assertEqual(in_progress["CIS 671"].term, "Fall 2026")

    def test_ocr_number_before_subject(self):
        text = """
        Academic Transcript
        Transcript Level
        Masters
        Applied Computer
        Institution Credit
        Period : Winter 2026
        CIS
        658
        Web Architectures
        A-
        3.000
        11.10
        676
        3.000
        SID
        Database Architecture
        12.00
        678
        SID
        Machine Learning
        3.000
        12.00
        """
        parsed = parse_banner(text, method="ocr")
        self.assertEqual(parsed.major, "Applied Computer Science")
        codes = [c.code for c in parsed.completed()]
        self.assertEqual(codes, ["CIS 658", "CIS 676", "CIS 678"])
        titles = {c.code: c.title for c in parsed.completed()}
        self.assertIn("Web Architectures", titles["CIS 658"] or "")
        self.assertIn("Database Architecture", titles["CIS 676"] or "")
        self.assertIn("Machine Learning", titles["CIS 678"] or "")


if __name__ == "__main__":
    unittest.main()
