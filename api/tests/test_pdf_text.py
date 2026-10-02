from __future__ import annotations

import unittest

from api.app.banner import parse_banner
from api.app.pdf_text import pdf_bytes_to_text


class PdfTextTests(unittest.TestCase):
    def test_selectable_text_pdf_skips_ocr(self):
        import pymupdf

        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            "Academic Transcript\nTranscript Level\nMasters\nInstitution Credit\n"
            "Period : Fall 2025\nCIS 660 G Data Engineering A 3.000 12.00\n"
            "Course(s) in Progress\nTerm : Winter 2026\nCIS 656 G Distributed Systems 3.000\n",
        )
        data = doc.tobytes()
        doc.close()
        text, method = pdf_bytes_to_text(data)
        self.assertEqual(method, "text")
        parsed = parse_banner(text, method=method)
        codes = {c.code for c in parsed.courses}
        self.assertIn("CIS 660", codes)
        self.assertIn("CIS 656", codes)


if __name__ == "__main__":
    unittest.main()
