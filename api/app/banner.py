"""Parse a GVSU Banner advising transcript (text or OCR). Never keep name, ID, or GPA."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_SUBJECTS = {
    "CIS",
    "SE",
    "MTH",
    "STA",
    "PHL",
    "PHI",
    "WRT",
    "COM",
    "BIO",
    "CHM",
    "PHY",
    "PSY",
    "SOC",
    "ECO",
    "ACC",
    "BUS",
    "MGT",
    "MKT",
    "FIN",
    "ENG",
    "EGR",
    "STA",
    "CS",
    "DS",
    "CYB",
}

_SUBJECT_FIX = {
    "SID": "CIS",
    "S1D": "CIS",
    "CLS": "CIS",
    "C1S": "CIS",
    "CIS.": "CIS",
    "5E": "SE",
    "S E": "SE",
}

_HEADER_WORDS = {
    "subject",
    "course",
    "level",
    "title",
    "grade",
    "credit hours",
    "credit",
    "hours",
    "quality points",
    "quality",
    "points",
    "r",
    "college",
    "major",
    "academic standing",
    "last academic standing",
    "good standing",
    "period totals",
    "current period",
    "cumulative",
    "attempt hours",
    "passed hours",
    "earned hours",
    "gpa hours",
    "gpa",
    "institution",
    "pending",
    "awarded",
    "degree date",
    "transcript totals",
    "level comments",
    "overall",
    "total institution",
    "total transfer",
    "academic transcript",
    "student information",
    "curriculum information",
    "institution credit",
    "course(s) in progress",
    "courses in progress",
    "transcript level",
    "transcript type",
    "advising",
    "name",
}

_NOISE_PREFIXES = (
    "https://",
    "http://",
    "ellucian",
    "this is not an official",
    "studentacademic",
    "student academic",
    "responsible conduct",
    "@ 2013",
    "© 2013",
)

_PERIOD_RE = re.compile(
    r"(?:^|(?<=\s))(?P<kind>period|term)\s*:\s*(fall|winter|spring|summer)\s+(\d{4})\b",
    re.I,
)
_TOC_NAV = {
    "awarded",
    "institution credit",
    "transcript totals",
    "course(s) in progress",
    "courses in progress",
}
_COURSE_NO_RE = re.compile(r"^(\d{3})$")
_SHORT_NO_RE = re.compile(r"^(\d{2})$")
_CREDITS_RE = re.compile(r"^(\d{1,2}\.000)$")
_GRADE_RE = re.compile(r"^(?:[A-D][+-]?|F|CR|NC|AU|P|N|I|W|IP)$", re.I)
_QP_RE = re.compile(r"^(\d{1,2}\.\d{2})$")
_LEVEL_RE = re.compile(r"^[UG]$", re.I)

_LETTER_POINTS = {
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "C-": 1.7,
    "D+": 1.3,
    "D": 1.0,
    "F": 0.0,
}


@dataclass
class ParsedCourse:
    subject: str
    courseNumber: str
    code: str
    title: str | None = None
    creditHours: float | None = None
    gradeLetter: str | None = None
    level: str | None = None
    term: str | None = None
    termSource: str | None = None
    status: str = "completed"
    repeatFlag: str | None = None
    catalogMatched: bool = False
    warnings: list[str] = field(default_factory=list)

    def as_entry(self) -> dict:
        return {
            "subject": self.subject,
            "courseNumber": self.courseNumber,
            "code": self.code,
            "title": self.title,
            "creditHours": self.creditHours,
            "gradeLetter": self.gradeLetter if self.status == "completed" else None,
            "level": self.level,
            "term": self.term,
            "termSource": self.termSource,
            "status": self.status,
            "repeatFlag": self.repeatFlag,
        }


@dataclass
class ParsedTranscript:
    transcriptLevel: str | None = None
    transcriptType: str = "Advising"
    college: str | None = None
    degreeLine: str | None = None
    major: str | None = None
    courses: list[ParsedCourse] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    method: str = "text"

    def completed(self) -> list[ParsedCourse]:
        return [c for c in self.courses if c.status == "completed"]

    def in_progress(self) -> list[ParsedCourse]:
        return [c for c in self.courses if c.status == "in_progress"]


def _norm_title(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _fix_subject(token: str) -> str | None:
    raw = token.strip().upper().replace(".", "")
    raw = _SUBJECT_FIX.get(raw, raw)
    if raw in _SUBJECTS:
        return raw
    return None


def _is_noise(line: str) -> bool:
    low = line.lower().strip()
    if not low:
        return True
    if low in _HEADER_WORDS or low.strip("[]") in _HEADER_WORDS:
        return True
    if any(low.startswith(p) for p in _NOISE_PREFIXES):
        return True
    if re.fullmatch(r"\d{1,2}/\d", low):
        return True
    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}.*", low):
        return True
    if "mybanner.gvsu.edu" in low or "studentselfservice" in low:
        return True
    if low in {"and", "department", "computing", "science"}:
        return True
    return False


def _looks_like_qp(value: float, credits: float | None) -> bool:
    if credits and credits > 0:
        ratio = value / credits
        if 0 <= ratio <= 4.05:
            return True
    return 0 <= value <= 20 and not (1 <= value <= 6 and value == int(value))


def _letter_from_quality(qp: float, credits: float | None) -> str | None:
    if not credits or credits <= 0:
        return None
    gpa = qp / credits
    best = None
    best_delta = 0.2
    for letter, pts in _LETTER_POINTS.items():
        delta = abs(gpa - pts)
        if delta < best_delta:
            best = letter
            best_delta = delta
    return best


def _canon_grade(tok: str) -> str:
    token = tok.strip()
    if re.fullmatch(r"[A-D][+-]|F", token, re.I):
        return token[0].upper() + token[1:]
    return token.upper()


def _is_course_number_token(tok: str, tokens: list[str], idx: int) -> bool:
    if _COURSE_NO_RE.fullmatch(tok) and 100 <= int(tok) <= 799:
        return True
    # Print-to-PDF OCR often drops a digit from 693 → "69" + level "G".
    if not (_SHORT_NO_RE.fullmatch(tok) and 50 <= int(tok) <= 99):
        return False
    nearby = tokens[max(0, idx - 2) : min(len(tokens), idx + 4)]
    if any(_LEVEL_RE.fullmatch(t) for t in nearby):
        return True
    return any(_fix_subject(t) for t in tokens[max(0, idx - 2) : idx + 1])


def _courses_from_tokens(
    tokens: list[str],
    *,
    term: str | None,
    term_source: str | None,
    status: str,
) -> list[ParsedCourse]:
    number_idxs = [i for i, tok in enumerate(tokens) if _is_course_number_token(tok, tokens, i)]
    courses: list[ParsedCourse] = []
    for n, idx in enumerate(number_idxs):
        prev_idx = number_idxs[n - 1] if n else -8
        start = prev_idx + 1 if n else max(0, idx - 4)
        end = number_idxs[n + 1] if n + 1 < len(number_idxs) else min(len(tokens), idx + 8)
        lookback = tokens[start:idx]
        subject = None
        subj_j = None
        for j, tok in enumerate(lookback):
            found = _fix_subject(tok)
            if found:
                subject = found
                subj_j = j
        extra: list[str] = []
        if subj_j is not None:
            subj_abs = start + subj_j
            dist_curr = idx - subj_abs
            dist_prev = subj_abs - prev_idx
            if dist_curr <= dist_prev:
                extra = lookback[subj_j + 1 :]
            else:
                subject = None
        window = ([subject] if subject else []) + extra + tokens[idx:end]
        course = _flush_course(window, term=term, term_source=term_source, status=status)
        if course:
            courses.append(course)
    return courses


def _flush_course(
    tokens: list[str],
    *,
    term: str | None,
    term_source: str | None,
    status: str,
) -> ParsedCourse | None:
    if not tokens:
        return None
    subject = None
    number = None
    grade = None
    credits = None
    level = None
    qp = None
    title_parts: list[str] = []
    for tok in tokens:
        sub = _fix_subject(tok)
        if sub:
            if subject is None:
                subject = sub
            continue
        if _COURSE_NO_RE.fullmatch(tok) and number is None and 100 <= int(tok) <= 799:
            number = tok
            continue
        if _SHORT_NO_RE.fullmatch(tok) and number is None and 50 <= int(tok) <= 99:
            number = tok
            continue
        if _LEVEL_RE.fullmatch(tok) and level is None:
            level = tok.upper()
            continue
        if _GRADE_RE.fullmatch(tok) and grade is None:
            grade = _canon_grade(tok)
            continue
        cred = _CREDITS_RE.fullmatch(tok)
        if cred and credits is None:
            credits = float(cred.group(1))
            continue
        qp_m = _QP_RE.fullmatch(tok)
        if qp_m and not tok.endswith(".000"):
            qv = float(qp_m.group(1))
            if credits is not None and _looks_like_qp(qv, credits):
                qp = qv
                continue
        if not _is_noise(tok) and not _CREDITS_RE.fullmatch(tok) and not _QP_RE.fullmatch(tok):
            title_parts.append(tok)
    if number is None:
        return None
    if subject is None:
        subject = "CIS"
    title = " ".join(title_parts).strip() or None
    if title:
        title = re.sub(r"\s+", " ", title)
        title = title.replace("Master s ", "Master's ").replace("Masters Project", "Master's Project")
    if status == "completed" and not grade and qp is not None:
        grade = _letter_from_quality(qp, credits)
    if status == "in_progress":
        grade = None
    if level is None and int(number) >= 500:
        level = "G"
    return ParsedCourse(
        subject=subject,
        courseNumber=number,
        code=f"{subject} {number}",
        title=title,
        creditHours=credits,
        gradeLetter=grade,
        level=level,
        term=term,
        termSource=term_source,
        status=status,
    )


def parse_banner(text: str, method: str = "text") -> ParsedTranscript:
    parsed = ParsedTranscript(method=method)
    if not text or not text.strip():
        parsed.warnings.append("The PDF had no readable text.")
        return parsed

    raw_lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [ln for ln in raw_lines if ln]

    section = "header"
    term: str | None = None
    term_source: str | None = None
    status = "completed"
    group: list[str] = []
    seen_period = False

    def dump_group() -> None:
        nonlocal group
        if group:
            parsed.courses.extend(
                _courses_from_tokens(group, term=term, term_source=term_source, status=status)
            )
        group = []

    def note_major(low: str, line: str) -> None:
        if parsed.major:
            return
        cleaned = line.replace(", Undeclared", "").strip()
        if cleaned in {"Applied Computer Science", "Computer Science"}:
            parsed.major = cleaned
            return
        if low.startswith("applied computer"):
            parsed.major = "Applied Computer Science"
            return
        if low in {"computer science", "computer science, undeclared"}:
            parsed.major = "Computer Science"

    for line in lines:
        low = line.lower()

        if low.startswith("transcript level"):
            section = "header"
            continue
        if line in {"Masters", "Undergraduate"} and parsed.transcriptLevel is None:
            parsed.transcriptLevel = line
            continue
        if low == "masters" and parsed.transcriptLevel is None:
            parsed.transcriptLevel = "Masters"
            continue
        if low == "undergraduate" and parsed.transcriptLevel is None:
            parsed.transcriptLevel = "Undergraduate"
            continue
        if low.startswith("transcript type"):
            continue
        if low == "advising":
            parsed.transcriptType = "Advising"
            continue
        if "curriculum information" in low or low == "student information":
            section = "student"
            continue
        # Banner print PDFs put a one-line TOC (Awarded / Institution Credit /
        # Transcript Totals / Course(s) in Progress) on page 1. Those labels
        # must not lock the parser out of the real period tables later.
        if not seen_period and (
            low in _TOC_NAV or low.startswith("awarded") or low.startswith("transcript totals")
        ):
            continue
        if low == "awarded" or low.startswith("awarded"):
            continue
        if "institution credit" in low:
            dump_group()
            section = "credit"
            status = "completed"
            continue
        if "course(s) in progress" in low or "courses in progress" in low:
            dump_group()
            section = "progress"
            status = "in_progress"
            term = None
            continue
        if "transcript totals" in low:
            dump_group()
            section = "totals"
            continue

        if line in {"Master of Science", "Bachelor of Science", "Bachelor of Arts"}:
            if parsed.degreeLine is None or section in {"header", "student"}:
                parsed.degreeLine = line
            continue
        if "college of computing" in low or (low.startswith("college of ") and "computing" in low):
            parsed.college = "College of Computing"
            continue

        note_major(low, line)

        period = _PERIOD_RE.search(line)
        if period:
            dump_group()
            seen_period = True
            season, year = period.group(2).title(), period.group(3)
            term = f"{season} {year}"
            if period.group("kind").lower() == "term":
                term_source = "Term"
                status = "in_progress"
                section = "progress"
            else:
                term_source = "Period"
                status = "completed"
                section = "credit"
            continue

        if section not in {"credit", "progress"}:
            continue
        if _is_noise(line):
            continue
        if low in {"college of", "applied computer", "computing", "science"}:
            continue

        group.extend(line.split())

    dump_group()

    # Deduplicate exact code+term+status, keep the richer title.
    merged: dict[tuple[str, str | None, str], ParsedCourse] = {}
    for course in parsed.courses:
        key = (course.code, course.term, course.status)
        prev = merged.get(key)
        if not prev:
            merged[key] = course
            continue
        if course.title and (not prev.title or len(course.title) > len(prev.title)):
            prev.title = course.title
        if course.gradeLetter and not prev.gradeLetter:
            prev.gradeLetter = course.gradeLetter
        if course.creditHours and not prev.creditHours:
            prev.creditHours = course.creditHours
    parsed.courses = list(merged.values())

    if parsed.transcriptLevel is None:
        if parsed.degreeLine == "Master of Science" or (
            parsed.courses and all((c.courseNumber or "0") >= "500" for c in parsed.courses)
        ):
            parsed.transcriptLevel = "Masters"
        else:
            parsed.transcriptLevel = "Undergraduate"

    if not parsed.courses:
        parsed.warnings.append(
            "No course rows were found. Save the Banner Academic Transcript as a PDF (Print → Microsoft Print to PDF is fine)."
        )
    return parsed


def attach_catalog(
    parsed: ParsedTranscript,
    catalog: list[dict],
    programs: list[dict],
) -> ParsedTranscript:
    by_code = {c["code"]: c for c in catalog if c.get("code")}
    by_number: dict[str, list[dict]] = {}
    by_title: dict[str, list[dict]] = {}
    for course in catalog:
        num = str(course.get("course_number") or course.get("courseNumber") or "")
        if num:
            by_number.setdefault(num, []).append(course)
        title_key = _norm_title(course.get("title"))
        if title_key:
            by_title.setdefault(title_key, []).append(course)

    for course in parsed.courses:
        notes: list[str] = []
        hit = by_code.get(course.code)
        if not hit:
            title_key = _norm_title(course.title)
            titled = by_title.get(title_key) or []
            numbered = by_number.get(course.courseNumber) or []
            if len(titled) == 1:
                hit = titled[0]
                notes.append(f"Mapped {course.code} to {hit['code']} using the catalog title.")
            elif numbered:
                cis = [c for c in numbered if c.get("subject") == "CIS"]
                if course.subject == "CIS" and len(cis) == 1:
                    hit = cis[0]
                elif len(numbered) == 1:
                    hit = numbered[0]
                    notes.append(f"Mapped {course.code} to {hit['code']} using the catalog number.")
        if hit:
            if course.code != hit["code"]:
                course.subject = hit.get("subject") or course.subject
                course.courseNumber = str(hit.get("course_number") or course.courseNumber)
                course.code = hit["code"]
            if hit.get("title"):
                course.title = hit["title"]
            course.catalogMatched = True
            course.warnings.extend(notes)
            parsed.warnings.extend(notes)
        else:
            course.catalogMatched = False

    _recover_catalog_titles(parsed, unique_titles=by_title)

    taken = {c.code for c in parsed.courses}
    remaining = remaining_program_courses(parsed, programs, catalog, taken)
    parsed.courses.extend(remaining)
    return parsed


def _recover_catalog_titles(parsed: ParsedTranscript, unique_titles: dict[str, list[dict]]) -> None:
    """If OCR glued a second catalog title onto a row, emit that course too."""
    singles = {key: rows[0] for key, rows in unique_titles.items() if len(rows) == 1 and len(key) >= 12}
    taken = {c.code for c in parsed.courses}
    extras: list[ParsedCourse] = []
    for course in parsed.courses:
        blob = _norm_title(course.title)
        if not blob:
            continue
        own = _norm_title(course.title)
        for key, row in singles.items():
            code = row.get("code")
            if not code or code in taken:
                continue
            if key not in blob or own == key:
                continue
            extras.append(
                ParsedCourse(
                    subject=row.get("subject") or code.split(" ")[0],
                    courseNumber=str(row.get("course_number") or code.split(" ")[-1]),
                    code=code,
                    title=row.get("title"),
                    creditHours=row.get("credits_min") or course.creditHours,
                    level=course.level,
                    term=course.term,
                    termSource=course.termSource,
                    status=course.status,
                    catalogMatched=True,
                    warnings=[f"Recovered {code} from text on {course.code}."],
                )
            )
            taken.add(code)
            parsed.warnings.append(f"Recovered {code} from text on {course.code}.")
    parsed.courses.extend(extras)


def remaining_program_courses(
    parsed: ParsedTranscript,
    programs: list[dict],
    catalog: list[dict],
    taken: set[str],
) -> list[ParsedCourse]:
    program = _pick_program(parsed, programs)
    if not program:
        return []

    rows = program.get("courses") or []
    by_section: dict[str, list[dict]] = {}
    for row in rows:
        by_section.setdefault(row.get("section") or "other", []).append(row)

    leftover: list[ParsedCourse] = []

    capstones = by_section.get("capstone") or []
    if capstones:
        if not any(row["code"] in taken for row in capstones):
            for row in capstones:
                leftover.append(_program_row_to_course(row, "Capstone option from the catalog."))

    core_sections = [s for s in by_section if s.startswith("core-")]
    if core_sections:
        filled = []
        unfilled = []
        for section in core_sections:
            group = by_section[section]
            if any(row["code"] in taken for row in group):
                filled.append(section)
            else:
                unfilled.append(section)
        # Applied CS M.S.: three of four core areas.
        need = max(0, 3 - len(filled)) if len(core_sections) >= 4 else max(0, len(core_sections) - len(filled))
        if need:
            for section in unfilled:
                for row in by_section[section]:
                    leftover.append(
                        _program_row_to_course(
                            row,
                            f"Still needed from {section.replace('core-', '').replace('-', ' ')}.",
                        )
                    )
    else:
        for section in ("required", "general", "cognate"):
            for row in by_section.get(section) or []:
                if row["code"] in taken:
                    continue
                leftover.append(_program_row_to_course(row, f"Still needed ({section})."))

    # Avoid duplicates if the student already has the row.
    return [c for c in leftover if c.code not in taken]


def _pick_program(parsed: ParsedTranscript, programs: list[dict]) -> dict | None:
    level = parsed.transcriptLevel
    major = (parsed.major or "").lower()
    for program in programs:
        if level == "Masters" and program.get("id") == "applied-cs-ms":
            if "applied" in major or not major:
                return program
        if level == "Undergraduate" and program.get("id") == "cs-bs":
            if "applied" not in major:
                return program
    if level == "Masters":
        return next((p for p in programs if p.get("id") == "applied-cs-ms"), None)
    return next((p for p in programs if p.get("id") == "cs-bs"), None)


def _program_row_to_course(row: dict, note: str) -> ParsedCourse:
    subject = row.get("subject") or row["code"].split(" ")[0]
    number = str(row.get("course_number") or row["code"].split(" ")[-1])
    return ParsedCourse(
        subject=subject,
        courseNumber=number,
        code=row["code"],
        title=row.get("title"),
        creditHours=row.get("credits_min"),
        status="planned",
        catalogMatched=True,
        warnings=[note],
    )


def program_credit_target(parsed: ParsedTranscript) -> float | None:
    if parsed.transcriptLevel == "Masters":
        return 33.0
    return None


def remaining_credits(parsed: ParsedTranscript) -> float | None:
    target = program_credit_target(parsed)
    earned = 0.0
    for course in parsed.courses:
        if course.status in {"completed", "in_progress"} and course.creditHours:
            earned += course.creditHours
    if target is None:
        planned = sum(c.creditHours or 0 for c in parsed.courses if c.status == "planned")
        return planned or None
    return max(0.0, target - earned)


def parsed_to_payload(parsed: ParsedTranscript) -> dict:
    completed = [c.as_entry() for c in parsed.completed()]
    in_progress = [c.as_entry() for c in parsed.in_progress()]
    remaining = [c.as_entry() for c in parsed.courses if c.status == "planned"]
    return {
        "transcriptLevel": parsed.transcriptLevel,
        "transcriptType": parsed.transcriptType,
        "college": parsed.college,
        "degreeLine": parsed.degreeLine,
        "major": parsed.major,
        "completed": completed,
        "inProgress": in_progress,
        "remaining": remaining,
        "remainingCredits": remaining_credits(parsed),
        "warnings": parsed.warnings,
        "method": parsed.method,
        "courses": completed + in_progress + remaining,
    }
