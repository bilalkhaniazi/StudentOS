"""Parse student resumes from PDF / DOCX / TXT in memory. Heuristic, format-tolerant."""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree as ET

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": (
        "summary",
        "professional summary",
        "profile",
        "objective",
        "career objective",
        "about me",
        "about",
    ),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
        "work history",
        "internship experience",
        "internships",
        "relevant experience",
    ),
    "projects": (
        "projects",
        "personal projects",
        "academic projects",
        "selected projects",
        "key projects",
        "project experience",
    ),
    "skills": (
        "skills",
        "technical skills",
        "core skills",
        "skills & tools",
        "skills and tools",
        "technologies",
        "technical proficiency",
        "competencies",
    ),
    "education": (
        "education",
        "academic background",
        "academic history",
        "education and training",
    ),
    "languages": (
        "languages",
        "language skills",
        "spoken languages",
    ),
    "certifications": (
        "certifications",
        "certificates",
        "licenses",
        "licenses & certifications",
        "professional certifications",
    ),
}

HEADING_RE = re.compile(
    r"^(?P<title>[A-Za-z][A-Za-z0-9 /&+\-]{1,48})$"
)
DATE_RANGE_RE = re.compile(
    r"(?P<start>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{1,2}/\d{4}|\d{4})"
    r"\s*(?:[-–—to]+|\s+to\s+)\s*"
    r"(?P<end>(?:Present|Current|Now|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{1,2}/\d{4}|\d{4}))",
    re.I,
)
BULLET_RE = re.compile(r"^[\u2022\u2023\u25E6\u2043\u2219•●▪‣*\-–—]\s+")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s\-.]?)?(?:\(?\d{3}\)?[\s\-.]?)\d{3}[\s\-.]?\d{4}")
SKILL_SPLIT_RE = re.compile(r"[,|;/•·]|\n| {2,}")
DEGREE_HINT_RE = re.compile(
    r"\b(Bachelor|Master|B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?A\.?|Ph\.?D\.?|Associate|Diploma)\b",
    re.I,
)
TECH_TOKEN_RE = re.compile(
    r"\b(?:Python|Java(?:Script)?|TypeScript|C\+\+|C#|Go|Rust|SQL|R|Kotlin|Swift|"
    r"React|Next\.?js|Node\.?js|Django|Flask|FastAPI|Spring|Angular|Vue|"
    r"AWS|Azure|GCP|Docker|Kubernetes|Linux|Git|PostgreSQL|MySQL|MongoDB|"
    r"Redis|Kafka|Spark|TensorFlow|PyTorch|Pandas|NumPy|Tableau|Power\s*BI|"
    r"HTML|CSS|Tailwind|GraphQL|REST|Terraform|Airflow)\b",
    re.I,
)

KNOWN_LANGUAGES = {
    "english",
    "spanish",
    "french",
    "german",
    "arabic",
    "chinese",
    "mandarin",
    "cantonese",
    "hindi",
    "urdu",
    "punjabi",
    "bengali",
    "portuguese",
    "russian",
    "japanese",
    "korean",
    "italian",
    "turkish",
    "persian",
    "farsi",
    "vietnamese",
    "polish",
    "dutch",
    "swahili",
}


@dataclass
class ParsedResume:
    summary: str | None = None
    experiences: list[dict[str, Any]] = field(default_factory=list)
    projects: list[dict[str, Any]] = field(default_factory=list)
    skills: list[dict[str, Any]] = field(default_factory=list)
    education: list[dict[str, Any]] = field(default_factory=list)
    languages: list[dict[str, Any]] = field(default_factory=list)
    certifications: list[dict[str, Any]] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    studentTypeHint: str | None = None
    method: str = "text"
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "experiences": self.experiences,
            "projects": self.projects,
            "skills": self.skills,
            "education": self.education,
            "languages": self.languages,
            "certifications": self.certifications,
            "emails": self.emails,
            "phones": self.phones,
            "studentTypeHint": self.studentTypeHint,
            "method": self.method,
            "warnings": self.warnings,
        }


def extract_resume_text(data: bytes, filename: str) -> tuple[str, str, list[str]]:
    """Return (text, method, warnings). Never writes the file."""
    warnings: list[str] = []
    name = (filename or "resume").lower()
    if name.endswith(".txt"):
        text = _decode_bytes(data)
        return text, "text", warnings
    if name.endswith(".docx"):
        text = _docx_to_text(data)
        if text.strip():
            return text, "docx", warnings
        warnings.append("Could not read Word text from that .docx.")
        return "", "docx", warnings
    if name.endswith(".doc"):
        warnings.append("Legacy .doc is unreliable here — export to PDF or .docx if results look empty.")
        # Best effort: sometimes binary still has readable ASCII runs.
        text = _legacy_doc_ascii(data)
        return text, "doc-ascii", warnings
    # PDF (default)
    try:
        from api.app.pdf_text import pdf_bytes_to_text  # type: ignore
    except Exception:
        from pdf_text import pdf_bytes_to_text  # type: ignore

    # Resume OCR: temporarily relax transcript-only usability by using a local helper.
    text, method = _pdf_resume_text(data)
    if not text.strip():
        warnings.append("Little or no text found in the PDF. A text-based PDF or DOCX works best.")
    return text, method, warnings


def _pdf_resume_text(data: bytes) -> tuple[str, str]:
    try:
        import pymupdf
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pymupdf is required to read resume PDFs.") from exc

    doc = pymupdf.open(stream=data, filetype="pdf")
    try:
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text("text") or "")
        text = "\n".join(parts).strip()
        if len(text) >= 120:
            return text, "text"
        # OCR fallback for scanned resumes
        try:
            from api.app.pdf_text import _ocr_document  # type: ignore
        except Exception:
            from pdf_text import _ocr_document  # type: ignore
        ocr_text = _ocr_document(doc).strip()
        if ocr_text:
            return ocr_text, "ocr"
        return text, "text"
    finally:
        doc.close()


def _decode_bytes(data: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _docx_to_text(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            xml = zf.read("word/document.xml")
    except Exception:
        return ""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return ""
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    lines: list[str] = []
    for para in root.findall(".//w:p", ns):
        bits = [node.text or "" for node in para.findall(".//w:t", ns)]
        line = "".join(bits).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def _legacy_doc_ascii(data: bytes) -> str:
    chars: list[str] = []
    for b in data:
        if 32 <= b < 127 or b in (9, 10, 13):
            chars.append(chr(b))
        else:
            chars.append("\n")
    text = "".join(chars)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]{2,}", " ", text)
    return text.strip()


def parse_resume_text(text: str, *, method: str = "text", warnings: list[str] | None = None) -> ParsedResume:
    parsed = ParsedResume(method=method, warnings=list(warnings or []))
    cleaned = _normalize_text(text)
    if not cleaned.strip():
        parsed.warnings.append("No readable resume text.")
        return parsed

    parsed.emails = sorted(set(EMAIL_RE.findall(cleaned)))
    parsed.phones = sorted(set(m.group(0).strip() for m in PHONE_RE.finditer(cleaned)))
    parsed.studentTypeHint = _student_type_hint(cleaned)

    sections = _split_sections(cleaned)
    if "summary" in sections:
        parsed.summary = _clean_summary(sections["summary"])
    elif not sections:
        # No headings — keep a short top blurb as summary.
        top = "\n".join(cleaned.splitlines()[:8]).strip()
        if len(top) > 40:
            parsed.summary = _clean_summary(top[:600])

    if "experience" in sections:
        parsed.experiences = _parse_experience_block(sections["experience"])
    if "projects" in sections:
        parsed.projects = _parse_projects_block(sections["projects"])
    if "skills" in sections:
        parsed.skills = _parse_skills_block(sections["skills"])
    else:
        # Fallback: harvest known tech tokens from whole resume.
        parsed.skills = _skills_from_tokens(cleaned)

    if "education" in sections:
        parsed.education = _parse_education_block(sections["education"])
    if "languages" in sections:
        parsed.languages = _parse_languages_block(sections["languages"])
    else:
        parsed.languages = _languages_from_whole(cleaned)
    if "certifications" in sections:
        parsed.certifications = _parse_certifications_block(sections["certifications"])

    if not parsed.experiences and not parsed.projects and not parsed.skills:
        parsed.warnings.append(
            "Could not confidently split sections. Add headings like Experience, Projects, and Skills, or enter details manually."
        )
    return parsed


def parse_resume_bytes(data: bytes, filename: str) -> ParsedResume:
    text, method, warnings = extract_resume_text(data, filename)
    return parse_resume_text(text, method=method, warnings=warnings)


def merge_resume_into_profile(props: dict[str, Any], parsed: ParsedResume) -> dict[str, Any]:
    """Merge parsed resume fields into an existing student profile dict (in place + return)."""
    if parsed.summary and not (props.get("summary") or "").strip():
        props["summary"] = parsed.summary

    props["experiences"] = _merge_by_key(
        props.get("experiences") or [],
        parsed.experiences,
        lambda x: (
            (x.get("organization") or "").strip().lower(),
            (x.get("title") or "").strip().lower(),
            (x.get("startDate") or "").strip().lower(),
        ),
    )
    props["projects"] = _merge_by_key(
        props.get("projects") or [],
        parsed.projects,
        lambda x: (x.get("name") or "").strip().lower(),
    )
    props["education"] = _merge_by_key(
        props.get("education") or [],
        parsed.education,
        lambda x: (
            (x.get("institution") or "").strip().lower(),
            (x.get("degree") or "").strip().lower(),
        ),
    )
    props["languages"] = _merge_by_key(
        props.get("languages") or [],
        parsed.languages,
        lambda x: (x.get("name") or "").strip().lower(),
    )
    props["certifications"] = _merge_by_key(
        props.get("certifications") or [],
        [
            {
                "name": c.get("name") or "",
                "taggedSkills": c.get("taggedSkills") or [],
            }
            for c in parsed.certifications
            if c.get("name")
        ],
        lambda x: (x.get("name") or "").strip().lower(),
    )

    # Skills: union by label (case-insensitive)
    existing_skills = props.get("skills") or []
    seen = {(s.get("label") or "").strip().lower() for s in existing_skills}
    merged_skills = list(existing_skills)
    for skill in parsed.skills:
        label = (skill.get("label") or "").strip()
        key = label.lower()
        if not label or key in seen:
            continue
        seen.add(key)
        merged_skills.append({"label": label, "evidence": skill.get("evidence") or "self_report"})
    props["skills"] = merged_skills

    if parsed.studentTypeHint and not props.get("studentType"):
        props["studentType"] = parsed.studentTypeHint

    props["resumeParsed"] = {
        "method": parsed.method,
        "warnings": parsed.warnings,
        "emailsFound": len(parsed.emails),
        "phonesFound": len(parsed.phones),
    }
    return props


def _merge_by_key(existing: list[dict], incoming: list[dict], key_fn) -> list[dict]:
    out = list(existing)
    seen = {key_fn(x) for x in existing}
    for item in incoming:
        key = key_fn(item)
        if not any(key) or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    lines = [ln.strip() for ln in text.split("\n")]
    # Drop empty duplicates
    out: list[str] = []
    for ln in lines:
        if not ln:
            if out and out[-1] != "":
                out.append("")
            continue
        out.append(ln)
    return "\n".join(out).strip()


def _canonical_section(line: str) -> str | None:
    raw = line.strip().strip(":").strip()
    if len(raw) > 48:
        return None
    # All-caps or Title Case short heading
    letters = re.sub(r"[^A-Za-z]", "", raw)
    if not letters:
        return None
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    if upper_ratio < 0.6 and raw != raw.title() and not HEADING_RE.match(raw):
        # Still allow exact alias match in any case
        pass
    key = re.sub(r"\s+", " ", raw.lower())
    key = key.replace("&", "and")
    for section, aliases in SECTION_ALIASES.items():
        if key in aliases:
            return section
    return None


def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.split("\n"):
        heading = _canonical_section(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
            continue
        if current is None:
            continue
        sections[current].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}


def _clean_summary(block: str) -> str:
    text = re.sub(r"\s+", " ", block).strip()
    return text[:1200] if text else ""


def _student_type_hint(text: str) -> str | None:
    low = text.lower()
    intl_hits = (
        "international student",
        "f-1",
        "f1 student",
        "f-1 visa",
        "opt ",
        " cpt",
        "stem opt",
        "visa sponsorship",
        "requires sponsorship",
    )
    local_hits = ("u.s. citizen", "us citizen", "permanent resident", "green card", "authorized to work")
    if any(h in low for h in intl_hits):
        return "international"
    if any(h in low for h in local_hits):
        return "domestic"
    return None


def _chunk_entries(block: str) -> list[list[str]]:
    lines = [ln for ln in block.split("\n") if ln.strip()]
    chunks: list[list[str]] = []
    current: list[str] = []
    for ln in lines:
        if DATE_RANGE_RE.search(ln) and current:
            # New dated entry often starts here or previous line was title
            chunks.append(current)
            current = [ln]
            continue
        if not BULLET_RE.match(ln) and current and BULLET_RE.match(current[-1]) and not DATE_RANGE_RE.search(ln):
            # Non-bullet after bullets → likely next entry header
            if not DATE_RANGE_RE.search(ln) and len(ln) < 80:
                chunks.append(current)
                current = [ln]
                continue
        current.append(ln)
    if current:
        chunks.append(current)
    return chunks


def _parse_experience_block(block: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for chunk in _chunk_entries(block):
        if not chunk:
            continue
        joined = "\n".join(chunk)
        start, end, current = _extract_dates(joined)
        header_lines = [ln for ln in chunk if not BULLET_RE.match(ln)]
        bullets = [_strip_bullet(ln) for ln in chunk if BULLET_RE.match(ln)]
        title = None
        organization = None
        location = None
        if header_lines:
            first = header_lines[0]
            # Patterns: "Title — Org" / "Org — Title" / "Title at Org"
            parts = re.split(r"\s+[|@–—\-]\s+|\s+at\s+", first, maxsplit=1, flags=re.I)
            if len(parts) == 2:
                left, right = parts[0].strip(), parts[1].strip()
                # Prefer title-like left if it has role words
                if _looks_like_role(left) or not _looks_like_role(right):
                    title, organization = left, right
                else:
                    organization, title = left, right
            else:
                title = first
            if len(header_lines) > 1 and not organization:
                organization = DATE_RANGE_RE.sub("", header_lines[1]).strip(" |-–,")
            if len(header_lines) > 2:
                maybe_loc = DATE_RANGE_RE.sub("", header_lines[2]).strip(" |-–,")
                if maybe_loc and not DATE_RANGE_RE.fullmatch(maybe_loc or ""):
                    location = maybe_loc
        if not title and not organization:
            continue
        # If organization absorbed a date, clean it
        if organization:
            organization = DATE_RANGE_RE.sub("", organization).strip(" |-–,")
        out.append(
            {
                "organization": organization or "Organization",
                "title": title or "Role",
                "location": location,
                "startDate": start,
                "endDate": None if current else end,
                "current": current,
                "summary": " ".join(bullets)[:800] if bullets else None,
                "highlights": bullets[:12],
                "source": "resume",
            }
        )
    return out[:20]


def _parse_projects_block(block: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for chunk in _chunk_entries(block):
        if not chunk:
            continue
        header = next((ln for ln in chunk if not BULLET_RE.match(ln)), chunk[0])
        name = re.split(r"\s+[|–—\-]\s+", header, maxsplit=1)[0].strip()
        bullets = [_strip_bullet(ln) for ln in chunk if BULLET_RE.match(ln)]
        body = " ".join(bullets) if bullets else " ".join(chunk[1:])
        techs = sorted({m.group(0) for m in TECH_TOKEN_RE.finditer("\n".join(chunk))}, key=str.lower)
        if not name or len(name) > 120:
            continue
        out.append(
            {
                "name": name[:120],
                "summary": (body or None) and re.sub(r"\s+", " ", body).strip()[:600],
                "technologies": techs[:20],
                "demonstratesSkills": techs[:12],
                "source": "resume",
            }
        )
    return out[:20]


def _parse_skills_block(block: str) -> list[dict[str, Any]]:
    labels: list[str] = []
    for raw in SKILL_SPLIT_RE.split(block):
        token = raw.strip(" •·|-:")
        token = re.sub(r"^(?:languages?|frameworks?|tools?|databases?|cloud|libraries)\s*:\s*", "", token, flags=re.I)
        if not token or len(token) > 48:
            continue
        if EMAIL_RE.search(token) or PHONE_RE.search(token):
            continue
        if token.lower() in {"and", "or", "skills"}:
            continue
        labels.append(token)
    # Also pull known tech tokens
    for m in TECH_TOKEN_RE.finditer(block):
        labels.append(m.group(0))
    return _dedupe_skills(labels)[:60]


def _skills_from_tokens(text: str) -> list[dict[str, Any]]:
    labels = [m.group(0) for m in TECH_TOKEN_RE.finditer(text)]
    return _dedupe_skills(labels)[:40]


def _dedupe_skills(labels: list[str]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for label in labels:
        key = label.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append({"label": label.strip(), "evidence": "self_report"})
    return out


def _parse_education_block(block: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for chunk in _chunk_entries(block):
        if not chunk:
            continue
        joined = "\n".join(chunk)
        start, end, current = _extract_dates(joined)
        institution = None
        degree = None
        field = None
        for ln in chunk:
            if BULLET_RE.match(ln):
                continue
            clean = DATE_RANGE_RE.sub("", ln).strip(" |-–,")
            if not clean:
                continue
            if DEGREE_HINT_RE.search(clean) and not degree:
                degree = clean
                continue
            if not institution:
                institution = clean
                continue
            if not field:
                field = clean
        if not institution and not degree:
            continue
        out.append(
            {
                "institution": institution or "Institution",
                "degree": degree,
                "field": field,
                "location": None,
                "startDate": start,
                "endDate": None if current else end,
                "current": current,
                "source": "resume",
            }
        )
    return out[:12]


def _parse_languages_block(block: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in SKILL_SPLIT_RE.split(block):
        token = raw.strip(" •·|-:")
        if not token or len(token) > 40:
            continue
        # "English (Fluent)" / "Spanish - Intermediate" / "French: Native"
        m = re.match(
            r"^([A-Za-z][A-Za-z ]*?)\s*(?:\(([^)]+)\)|[:\-–—]\s*(.+))?$",
            token,
        )
        if not m:
            continue
        name = m.group(1).strip().title()
        proficiency = (m.group(2) or m.group(3) or "").strip() or None
        base = name.lower()
        if base not in KNOWN_LANGUAGES and base.split()[0] not in KNOWN_LANGUAGES:
            if len(name.split()) > 2:
                continue
        out.append({"name": name, "proficiency": proficiency, "source": "resume"})
    return _dedupe_languages(out)[:20]


def _languages_from_whole(text: str) -> list[dict[str, Any]]:
    low = text.lower()
    found = []
    for lang in sorted(KNOWN_LANGUAGES):
        if re.search(rf"\b{re.escape(lang)}\b", low):
            found.append({"name": lang.title(), "proficiency": None, "source": "resume"})
    return found[:12]


def _dedupe_languages(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = (item.get("name") or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _parse_certifications_block(block: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ln in block.split("\n"):
        clean = BULLET_RE.sub("", ln).strip()
        clean = DATE_RANGE_RE.sub("", clean).strip(" |-–,")
        if not clean or len(clean) < 3:
            continue
        out.append({"name": clean[:160], "taggedSkills": [], "source": "resume"})
    # Dedupe
    seen: set[str] = set()
    unique = []
    for item in out:
        key = item["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique[:20]


def _extract_dates(text: str) -> tuple[str | None, str | None, bool]:
    m = DATE_RANGE_RE.search(text)
    if not m:
        return None, None, False
    start = m.group("start").strip()
    end = m.group("end").strip()
    current = end.lower() in {"present", "current", "now"}
    return start, (None if current else end), current


def _strip_bullet(line: str) -> str:
    return BULLET_RE.sub("", line).strip()


def _looks_like_role(text: str) -> bool:
    low = text.lower()
    needles = (
        "engineer",
        "developer",
        "intern",
        "analyst",
        "manager",
        "assistant",
        "consultant",
        "specialist",
        "researcher",
        "lead",
        "architect",
        "tutor",
        "associate",
    )
    return any(n in low for n in needles)
