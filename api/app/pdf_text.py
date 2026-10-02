"""Read Banner transcript PDFs in memory. Print-to-PDF files need OCR; text PDFs do not."""

from __future__ import annotations

from functools import lru_cache

MIN_TEXT_CHARS = 180


def pdf_bytes_to_text(data: bytes) -> tuple[str, str]:
    """Return (text, method). method is 'text' or 'ocr'. Does not write the file to disk."""
    try:
        import pymupdf
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pymupdf is required to read transcript PDFs.") from exc

    doc = pymupdf.open(stream=data, filetype="pdf")
    try:
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text("text") or "")
        text = "\n".join(parts).strip()
        if _usable(text):
            return text, "text"
        return _ocr_document(doc), "ocr"
    finally:
        doc.close()


def _usable(text: str) -> bool:
    if len(text) < MIN_TEXT_CHARS:
        return False
    low = text.lower()
    return "transcript" in low or "institution credit" in low or "course(s) in progress" in low


def _ocr_document(doc) -> str:
    ocr = _ocr_engine()
    pages: list[str] = []
    for page in doc:
        pix = page.get_pixmap(matrix=__import__("pymupdf").Matrix(2.2, 2.2), alpha=False)
        result, _elapsed = ocr(pix.tobytes("png"))
        lines: list[str] = []
        if result:
            for item in result:
                piece = item[1] if len(item) > 1 else ""
                if piece:
                    lines.append(str(piece))
        pages.append("\n".join(lines))
    return "\n\n".join(pages)


@lru_cache(maxsize=1)
def _ocr_engine():
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR()
