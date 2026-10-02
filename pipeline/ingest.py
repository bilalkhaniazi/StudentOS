"""Batch ingest of the public GVSU CS B.S. and Applied CS M.S. catalog.

Structured fields only. Attribute Grand Valley State University.
Prototype use; not a republished catalog and not official SIS.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CATALOG_DIR = DATA_DIR / "catalog"
SNAPSHOT_COURSES = CATALOG_DIR / "courses.json"
SNAPSHOT_PROGRAMS = CATALOG_DIR / "programs.json"
SNAPSHOT_META = CATALOG_DIR / "ingest_meta.json"

CATALOG_YEAR = os.environ.get("CATALOG_YEAR", "2026-2027")
BASE = "https://www.gvsu.edu"
USER_AGENT = (
    "StudentOS-catalog-ingest/0.1 (academic prototype; public catalog snapshot)"
)

SUBJECT_PAGES = {
    "CIS": f"{BASE}/catalog/subject/computer-information-systems.htm",
    "AI": f"{BASE}/catalog/subject/artificial-intelligence.htm",
    "CYB": f"{BASE}/catalog/subject/cybersecurity.htm",
    "SE": f"{BASE}/catalog/subject/software-engineering.htm",
    "HCC": f"{BASE}/catalog/subject/human-centered-computing.htm",
}

PROGRAM_PAGES = {
    "cs-bs": {
        "url": f"{BASE}/catalog/program/bachelor-of-science-in-computer-science.htm",
        "title": "Bachelor of Science in Computer Science",
        "degree_line": "Bachelor of Science",
        "major": "Computer Science",
        "level": "Undergraduate",
    },
    "applied-cs-ms": {
        "url": f"{BASE}/catalog/program/master-of-science-in-applied-computer-science.htm",
        "title": "Master of Science in Applied Computer Science",
        "degree_line": "Master of Science",
        "major": "Applied Computer Science",
        "level": "Masters",
    },
}

BADGE_PAGES = {
    "biomedical-informatics": {
        "name": "Biomedical Informatics",
        "url": f"{BASE}/catalog/program/badge-in-biomedical-informatics.htm",
    },
    "cybersecurity": {
        "name": "Cybersecurity",
        "url": f"{BASE}/catalog/program/badge-in-cybersecurity.htm",
    },
    "data-analytics": {
        "name": "Data Analytics",
        "url": f"{BASE}/catalog/program/badge-in-data-analytics.htm",
    },
    "database-management": {
        "name": "Database Management",
        "url": f"{BASE}/catalog/program/badge-in-database-management.htm",
    },
    "distributed-computing": {
        "name": "Distributed Computing",
        "url": f"{BASE}/catalog/program/badge-in-distributed-computing.htm",
    },
    "information-systems-management": {
        "name": "Information Systems Management",
        "url": f"{BASE}/catalog/program/badge-in-information-systems-management.htm",
    },
    "software-design-and-development": {
        "name": "Software Design and Development",
        "url": f"{BASE}/catalog/program/badge-in-software-design-and-development.htm",
    },
    "software-engineering": {
        "name": "Software Engineering",
        "url": f"{BASE}/catalog/program/badge-in-software-engineering.htm",
    },
    "web-and-mobile-computing": {
        "name": "Web and Mobile Computing",
        "url": f"{BASE}/catalog/program/badge-in-web-and-mobile-computing.htm",
    },
}

COURSE_CODE_RE = re.compile(r"\b([A-Z]{2,4})\s+(\d{3})\b")
HEADING_RE = re.compile(r"^([A-Z]{2,4})\s+(\d{3})\s+[—\-–]\s+(.+)$")
CREDITS_RE = re.compile(
    r"(?:^|[.\s])Credits?:\s*(\d+(?:\.\d+)?)(?:\s*to\s*(\d+(?:\.\d+)?))?",
    re.I,
)
LISTING_RE = re.compile(
    r"([A-Z]{2,4})\s+(\d{3})\s+[—\-–]\s+(.+?)\s*\(([^)]+credits?)\)", re.I
)

TOPIC_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("databases", ("database", "data management", "sql", "information storage")),
    ("data-engineering", ("data engineering", "etl", "pipeline", "information pipeline")),
    ("data-mining", ("data mining", "knowledge discovery")),
    ("machine-learning", ("machine learning", "neural", "deep learning")),
    ("artificial-intelligence", ("artificial intelligence", "ai ")),
    ("cloud", ("cloud computing", "cloud application", "virtualization")),
    ("distributed-systems", ("distributed", "high-performance computing")),
    ("networking", ("network", "data communication", "wireless")),
    ("security", ("security", "cryptograph", "forensic", "ethical hacking", "information assurance")),
    ("web", ("web application", "web architect", "internet media")),
    ("mobile", ("mobile application", "pervasive")),
    ("software-engineering", ("software engineering", "requirements specification", "software testing", "software architecture")),
    ("operating-systems", ("operating system",)),
    ("programming", ("programming", "data structures", "algorithms", "computer science i", "computer science ii")),
    ("computer-organization", ("computer organization", "computer architecture", "system-level")),
    ("visualization", ("visualiz", "computer graphics")),
    ("project", ("project", "capstone", "internship", "practicum", "thesis")),
]


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        }
    )
    return s


def fetch(s: requests.Session, url: str, retries: int = 3) -> str | None:
    last_err = None
    for attempt in range(retries):
        try:
            r = s.get(url, timeout=30)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.text
        except requests.RequestException as exc:
            last_err = exc
            time.sleep(0.4 * (attempt + 1))
    print(f"warn: failed to fetch {url}: {last_err}", file=sys.stderr)
    return None


def soup_text(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def decode_href(href: str) -> str:
    return html_lib.unescape(href or "")


def parse_credits(raw: str | None) -> tuple[float | None, float | None, str | None]:
    if not raw:
        return None, None, None
    cleaned = re.sub(r"\s+", " ", raw).strip()
    m = re.search(
        r"(?:Credits?:\s*)?(\d+(?:\.\d+)?)(?:\s*to\s*(\d+(?:\.\d+)?))?(?:\s*credits?)?",
        cleaned,
        re.I,
    )
    if not m:
        m = re.fullmatch(r"(\d+(?:\.\d+)?)(?:\s*to\s*(\d+(?:\.\d+)?))?", cleaned, re.I)
    if not m:
        return None, None, None
    lo, hi = m.group(1), m.group(2)
    credits_min = float(lo)
    credits_max = float(hi) if hi else credits_min
    text = f"{credits_min:g}" if credits_max == credits_min else f"{credits_min:g} to {credits_max:g}"
    return credits_min, credits_max, text


def derive_topics(title: str, description: str) -> list[str]:
    blob = f"{title} {description}".lower()
    topics: list[str] = []
    for topic, needles in TOPIC_RULES:
        if any(n in blob for n in needles):
            topics.append(topic)
    return topics


def parse_prerequisite_codes(prereq_text: str | None) -> list[str]:
    if not prereq_text:
        return []
    codes: list[str] = []
    seen: set[str] = set()
    for subj, num in COURSE_CODE_RE.findall(prereq_text.upper()):
        code = f"{subj} {num}"
        if code not in seen:
            seen.add(code)
            codes.append(code)
    return codes


def parse_subject_listing(html: str, subject: str, page_url: str) -> list[dict[str, Any]]:
    soup = soup_text(html)
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = decode_href(a["href"])
        if "/catalog/course/" not in href:
            continue
        abs_url = urljoin(page_url, href)
        label = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
        m = LISTING_RE.search(label) or COURSE_CODE_RE.search(label.upper())
        if not m:
            slug = Path(href).stem  # e.g. cis-162
            slug_m = re.match(r"([a-z]+)-(\d{3})$", slug)
            if not slug_m:
                continue
            subj, num = slug_m.group(1).upper(), slug_m.group(2)
            title = label
            credits_raw = None
        elif hasattr(m, "group") and m.lastindex and m.lastindex >= 4:
            subj, num, title, credits_raw = (
                m.group(1).upper(),
                m.group(2),
                m.group(3).strip(),
                m.group(4),
            )
        else:
            subj, num = m.group(1).upper(), m.group(2)
            title = label
            credits_raw = None
        code = f"{subj} {num}"
        if code in seen:
            continue
        seen.add(code)
        credits_min, credits_max, credits_text = parse_credits(credits_raw)
        found.append(
            {
                "code": code,
                "subject": subj,
                "course_number": num,
                "title": title.split(" - ", 1)[-1] if " - " in title and title.startswith(subj) else title,
                "source_url": abs_url,
                "listing_subject": subject,
                "credits_min": credits_min,
                "credits_max": credits_max,
                "credits_text": credits_text,
            }
        )
    return found


def parse_course_page(html: str, url: str, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    soup = soup_text(html)
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()
    main = soup.find("main") or soup
    heading_el = None
    heading = ""
    for h in main.find_all(["h2", "h1", "h3"]):
        t = re.sub(r"\s+", " ", h.get_text(" ", strip=True))
        if HEADING_RE.match(t):
            heading_el = h
            heading = t
            break
    if not heading:
        title_tag = soup.find("title")
        heading = title_tag.get_text(" ", strip=True) if title_tag else ""
        heading = heading.split(" - Courses")[0].strip()

    hm = HEADING_RE.match(heading)
    if hm:
        subject, number, title = hm.group(1), hm.group(2), hm.group(3).strip()
        code = f"{subject} {number}"
    elif fallback:
        code = fallback["code"]
        subject = fallback["subject"]
        number = fallback["course_number"]
        title = fallback.get("title") or heading
    else:
        cm = COURSE_CODE_RE.search(heading.upper())
        if not cm:
            raise ValueError(f"could not parse course heading from {url}: {heading!r}")
        subject, number = cm.group(1), cm.group(2)
        code = f"{subject} {number}"
        title = heading

    paragraphs: list[str] = []
    if heading_el:
        for sib in heading_el.find_next_siblings():
            if sib.name in {"h1", "h2", "h3"}:
                break
            text = re.sub(r"\s+", " ", sib.get_text(" ", strip=True)).strip()
            if not text:
                continue
            if text.lower().startswith("if you are in need"):
                break
            if text.lower().startswith("catalog year"):
                break
            paragraphs.append(text)
    else:
        paragraphs = [re.sub(r"\s+", " ", main.get_text(" ", strip=True))]

    credits_min = credits_max = None
    credits_text = None
    prereq_text = None
    desc_parts: list[str] = []
    for para in paragraphs:
        if para.lower().startswith("credits"):
            credits_min, credits_max, credits_text = parse_credits(para)
            continue
        pm = re.search(r"Prerequisite[s]?:\s*(.+)$", para, re.I)
        if pm:
            prereq_text = pm.group(1).strip(" .")
            if prereq_text.lower() in {"none", "n/a"}:
                prereq_text = None
            desc_parts.append(re.split(r"Prerequisite[s]?:", para, maxsplit=1, flags=re.I)[0].strip(" ."))
            continue
        desc_parts.append(para)
    desc = " ".join(p for p in desc_parts if p).strip()
    if credits_min is None and fallback:
        credits_min = fallback.get("credits_min")
        credits_max = fallback.get("credits_max")
        credits_text = fallback.get("credits_text")

    offered = None
    om = re.search(r"Offered[^.]*\.", desc)
    if om:
        offered = om.group(0).strip()

    return {
        "code": code,
        "subject": subject,
        "course_number": number,
        "title": title.strip(),
        "description": desc,
        "credits_min": credits_min if credits_min is not None else (fallback or {}).get("credits_min"),
        "credits_max": credits_max if credits_max is not None else (fallback or {}).get("credits_max"),
        "credits_text": credits_text or (fallback or {}).get("credits_text"),
        "prerequisites_text": prereq_text,
        "prerequisite_codes": parse_prerequisite_codes(prereq_text),
        "offered": offered,
        "source_url": url,
        "catalog_year": CATALOG_YEAR,
        "level": "graduate" if int(number) >= 500 else "undergraduate",
        "topics": derive_topics(title, desc),
        "programs": {},
    }


def _listing_rows(line: str, section: str, program_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for m in LISTING_RE.finditer(line):
        subj, num, title, credits_raw = (
            m.group(1).upper(),
            m.group(2),
            m.group(3).strip(" -"),
            m.group(4),
        )
        title = re.sub(r"\s+", " ", title).strip()
        credits_min, credits_max, credits_text = parse_credits(credits_raw)
        rows.append(
            {
                "code": f"{subj} {num}",
                "subject": subj,
                "course_number": num,
                "title": title,
                "credits_min": credits_min,
                "credits_max": credits_max,
                "credits_text": credits_text,
                "section": section,
                "program_id": program_id,
            }
        )
    return rows


def _program_section_for(line: str, current: str) -> str:
    lower = line.lower().strip()
    if "suggested order of coursework" in lower:
        return "suggested-order"
    if lower.startswith("year one") or lower == "year 1":
        return "suggested-year-1"
    if lower.startswith("year two") or lower == "year 2":
        return "suggested-year-2"
    if lower.startswith("year three") or lower == "year 3":
        return "suggested-year-3"
    if lower.startswith("year four") or lower == "year 4":
        return "suggested-year-4"
    if "bachelor of science degree requirements" in lower:
        return "foundation"
    if "required computer science courses" in lower:
        return "required"
    if "elective computer science courses" in lower:
        return "elective"
    if "required non-computing" in lower:
        return "cognate"
    if "select one math elective" in lower:
        return "math-elective"
    if "physical sciences or life sciences" in lower or "has a lab component" in lower:
        return "science-lab"
    if lower in {"core", "core courses"} or lower.startswith("core courses"):
        return "core"
    if "badge courses" in lower:
        return "badge"
    if lower.strip("1234. ") == "data engineering":
        return "core-data-engineering"
    if "management of systems" in lower:
        return "core-systems-development"
    if lower.strip("1234. ") == "software engineering":
        return "core-software-engineering"
    if lower.strip("1234. ") == "networking":
        return "core-networking"
    if lower == "electives" or lower.startswith("electives"):
        return "elective"
    if lower == "capstone" or lower.startswith("capstone"):
        return "capstone"
    return current


def parse_program_page(html: str, program_id: str, page_url: str) -> dict[str, Any]:
    soup = soup_text(html)
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()
    main = soup.find("main") or soup
    text = main.get_text("\n", strip=True)
    courses: list[dict[str, Any]] = []
    suggested: list[dict[str, Any]] = []
    current_section = "general"
    overview_notes: list[str] = []
    blocks: list[str] = []
    for el in main.find_all(["h2", "h3", "h4", "p", "li"]):
        line = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
        if line:
            blocks.append(line)
    if not blocks:
        blocks = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    for line in blocks:
        if line.lower().startswith("if you are in need"):
            break
        listings = _listing_rows(line, current_section, program_id)
        if not listings:
            nxt = _program_section_for(line, current_section)
            if nxt != current_section:
                current_section = nxt
            elif program_id == "applied-cs-ms" and len(overview_notes) < 6:
                low = line.lower()
                if "33 credit" in low or "11 three-credit" in low or "at least one badge" in low:
                    overview_notes.append(line)
            continue
        if current_section.startswith("suggested"):
            year = {
                "suggested-year-1": "Year One",
                "suggested-year-2": "Year Two",
                "suggested-year-3": "Year Three",
                "suggested-year-4": "Year Four",
            }.get(current_section, "Sequence")
            for row in listings:
                suggested.append({**row, "year": year, "section": "suggested"})
            continue
        if " or " in line.lower() and len(listings) >= 2 and current_section in {"cognate", "foundation"}:
            for row in listings:
                row["section"] = "stats-choice"
                row["choice_group"] = "statistics"
        courses.extend(listings)

    info = PROGRAM_PAGES[program_id]
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in courses:
        key = (row["code"], row["section"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)

    payload: dict[str, Any] = {
        "id": program_id,
        "title": info["title"],
        "degree_line": info["degree_line"],
        "major": info["major"],
        "level": info["level"],
        "source_url": page_url,
        "catalog_year": CATALOG_YEAR,
        "overview": overview_notes,
        "courses": unique,
        "suggested_order": suggested,
        "badges": [],
        "rules": _program_rules(program_id, unique),
    }
    return payload


def _program_rules(program_id: str, courses: list[dict[str, Any]]) -> dict[str, Any]:
    if program_id == "applied-cs-ms":
        return {
            "total_credits": 33,
            "course_count": 11,
            "core": {
                "credits": 9,
                "choose_areas": 3,
                "of_areas": 4,
                "note": "Complete one course in three of the four core areas.",
            },
            "badge": {
                "credits": 9,
                "course_count": 3,
                "choose": 1,
                "note": "Complete at least one College of Computing graduate badge (three courses).",
            },
            "electives": {
                "credits_min": 9,
                "credits_max": 12,
                "note": "Take enough electives to reach 33 credits. Electives are graduate computing courses not used as core, badge, or capstone.",
            },
            "capstone": {
                "credits": 3,
                "note": "CIS 693 Master's Project, or CIS 695 Master's Thesis (taken twice for 6 credits). Internship only with Graduate Program Director approval.",
            },
        }
    required_n = sum(1 for c in courses if c["section"] == "required")
    elective_n = sum(1 for c in courses if c["section"] == "elective")
    return {
        "total_credits": None,
        "core": {
            "note": "Complete every required Computer Science course with a minimum 2.0 GPA.",
            "course_count": required_n,
        },
        "electives": {
            "choose": 4,
            "of": elective_n,
            "note": "Select four elective Computer Science courses from the catalog list.",
        },
        "cognate": {
            "note": "Complete the non-computing cognates, including one statistics choice, one math elective, and one lab science.",
        },
        "capstone": {
            "note": "CIS 467 Computer Science Project is the major capstone. CIS 490 Internship is also required (2 to 5 credits).",
        },
    }


def _badge_structure_kind(line: str, current: str) -> str:
    low = line.lower()
    if "choose 3 of the following" in low or "choose three of the following" in low:
        return "choose-3"
    if "two of the following" in low or "2 of the following" in low:
        return "choose-2"
    if "1 of the following" in low or "one of the following" in low:
        return "choose-1"
    if "students must take" in low:
        return "required"
    return current


def parse_badge_page(html: str, badge_id: str, info: dict[str, Any]) -> dict[str, Any]:
    soup = soup_text(html)
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()
    main = soup.find("main") or soup
    heading = None
    for h in main.find_all(["h2", "h3", "h4"]):
        if "requirement" in h.get_text(" ", strip=True).lower():
            heading = h
    blocks: list[str] = []
    if heading:
        for sib in heading.find_next_siblings():
            if sib.name in {"h1", "h2", "h3", "h4"}:
                break
            if sib.name in {"ul", "ol"}:
                for li in sib.find_all("li", recursive=False) or sib.find_all("li"):
                    t = re.sub(r"\s+", " ", li.get_text(" ", strip=True)).strip()
                    if t:
                        blocks.append(t)
                continue
            t = re.sub(r"\s+", " ", sib.get_text(" ", strip=True)).strip()
            if t:
                blocks.append(t)
    else:
        blocks = [re.sub(r"\s+", " ", line).strip() for line in main.get_text("\n", strip=True).splitlines()]

    kind = "required"
    slots: list[dict[str, Any]] = []
    required: list[dict[str, Any]] = []
    choose_from: list[dict[str, Any]] = []
    choose_n = 0
    for line in blocks:
        if line.lower().startswith("if you are in need"):
            break
        kind = _badge_structure_kind(line, kind)
        listings = _listing_rows(line, kind, badge_id)
        if not listings:
            continue
        if " or " in line.lower() and len(listings) >= 2:
            slots.append({"kind": "choose_n", "n": 1, "courses": listings})
            continue
        if kind.startswith("choose-"):
            choose_n = int(kind.split("-")[1])
            choose_from.extend(listings)
        else:
            required.extend(listings)
    if required:
        slots.insert(0, {"kind": "all", "n": len(required), "courses": required})
    if choose_from:
        slots.append({"kind": "choose_n", "n": choose_n or 1, "courses": choose_from})
    courses: list[dict[str, Any]] = []
    seen: set[str] = set()
    for slot in slots:
        for row in slot["courses"]:
            if row["code"] in seen:
                continue
            seen.add(row["code"])
            courses.append(row)
    return {
        "id": badge_id,
        "name": info["name"],
        "kind": "Post-Baccalaureate Badge",
        "credits": 9,
        "course_count": 3,
        "source_url": info["url"],
        "catalog_year": CATALOG_YEAR,
        "slots": slots,
        "courses": courses,
    }


def guess_course_url(code: str) -> str:
    subj, num = code.split()
    return f"{BASE}/catalog/course/{subj.lower()}-{num}.htm"


def fetch_catalog(live: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not live and SNAPSHOT_COURSES.exists() and SNAPSHOT_PROGRAMS.exists():
        courses = json.loads(SNAPSHOT_COURSES.read_text())
        programs = json.loads(SNAPSHOT_PROGRAMS.read_text())
        meta = json.loads(SNAPSHOT_META.read_text()) if SNAPSHOT_META.exists() else {}
        return courses, programs, meta

    s = session()
    listings: dict[str, dict[str, Any]] = {}
    for subject, url in SUBJECT_PAGES.items():
        page = fetch(s, url)
        if not page:
            continue
        for row in parse_subject_listing(page, subject, url):
            listings[row["code"]] = row

    programs: list[dict[str, Any]] = []
    for pid, info in PROGRAM_PAGES.items():
        page = fetch(s, info["url"])
        if not page:
            continue
        program = parse_program_page(page, pid, info["url"])
        programs.append(program)
        for row in program["courses"]:
            listings.setdefault(
                row["code"],
                {
                    "code": row["code"],
                    "subject": row["subject"],
                    "course_number": row["course_number"],
                    "title": row["title"],
                    "source_url": guess_course_url(row["code"]),
                    "listing_subject": row["subject"],
                    "credits_min": row["credits_min"],
                    "credits_max": row["credits_max"],
                    "credits_text": row["credits_text"],
                },
            )

    badges: list[dict[str, Any]] = []
    for badge_id, info in BADGE_PAGES.items():
        page = fetch(s, info["url"])
        if not page:
            print(f"warn: missing badge page {info['url']}", file=sys.stderr)
            continue
        badge = parse_badge_page(page, badge_id, info)
        badges.append(badge)
        for row in badge["courses"]:
            listings.setdefault(
                row["code"],
                {
                    "code": row["code"],
                    "subject": row["subject"],
                    "course_number": row["course_number"],
                    "title": row["title"],
                    "source_url": guess_course_url(row["code"]),
                    "listing_subject": row["subject"],
                    "credits_min": row["credits_min"],
                    "credits_max": row["credits_max"],
                    "credits_text": row["credits_text"],
                },
            )

    for program in programs:
        if program["id"] == "applied-cs-ms":
            program["badges"] = badges
            for badge in badges:
                for row in badge["courses"]:
                    program["courses"].append(
                        {
                            **row,
                            "section": f"badge-{badge['id']}",
                            "program_id": "applied-cs-ms",
                            "badge_id": badge["id"],
                        }
                    )

    courses: dict[str, dict[str, Any]] = {}

    def load_one(code: str, listing: dict[str, Any]) -> dict[str, Any] | None:
        url = listing.get("source_url") or guess_course_url(code)
        page = fetch(s, url)
        if page:
            try:
                return parse_course_page(page, url, listing)
            except ValueError as exc:
                print(f"warn: {exc}", file=sys.stderr)
        # Keep structured listing even if the detail page is missing.
        credits_min, credits_max = listing.get("credits_min"), listing.get("credits_max")
        return {
            "code": code,
            "subject": listing["subject"],
            "course_number": listing["course_number"],
            "title": listing.get("title") or code,
            "description": "",
            "credits_min": credits_min,
            "credits_max": credits_max,
            "credits_text": listing.get("credits_text"),
            "prerequisites_text": None,
            "prerequisite_codes": [],
            "offered": None,
            "source_url": url,
            "catalog_year": CATALOG_YEAR,
            "level": "graduate" if int(listing["course_number"]) >= 500 else "undergraduate",
            "topics": derive_topics(listing.get("title") or "", ""),
            "programs": {},
        }

    items = list(listings.items())
    print(f"fetching {len(items)} course pages…")
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = {pool.submit(load_one, code, listing): code for code, listing in items}
        for fut in as_completed(futs):
            row = fut.result()
            if row:
                courses[row["code"]] = row

    # Attach program membership
    for program in programs:
        for row in program["courses"]:
            course = courses.get(row["code"])
            if not course:
                continue
            course.setdefault("programs", {})
            sections = course["programs"].setdefault(program["id"], [])
            if row["section"] not in sections:
                sections.append(row["section"])
            if row.get("badge_id"):
                badges_on = course.setdefault("badges", [])
                if row["badge_id"] not in badges_on:
                    badges_on.append(row["badge_id"])

    # Stub nodes for prerequisite courses not already in the catalog snapshot
    extra_codes: set[str] = set()
    for course in courses.values():
        extra_codes.update(course.get("prerequisite_codes") or [])
    for code in sorted(extra_codes):
        if code in courses:
            continue
        url = guess_course_url(code)
        page = fetch(s, url)
        if page:
            try:
                courses[code] = parse_course_page(page, url)
                continue
            except ValueError:
                pass
        subj, num = code.split()
        courses[code] = {
            "code": code,
            "subject": subj,
            "course_number": num,
            "title": code,
            "description": "Referenced as a prerequisite on a CIS / CS program course; detail page not ingested.",
            "credits_min": None,
            "credits_max": None,
            "credits_text": None,
            "prerequisites_text": None,
            "prerequisite_codes": [],
            "offered": None,
            "source_url": url,
            "catalog_year": CATALOG_YEAR,
            "level": "graduate" if int(num) >= 500 else "undergraduate",
            "topics": [],
            "programs": {},
        }

    course_list = [courses[k] for k in sorted(courses)]
    meta = {
        "catalog_year": CATALOG_YEAR,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "source": "GVSU public catalog",
        "attribution": "Grand Valley State University public catalog. Structured fields only. Not official SIS.",
        "subject_pages": SUBJECT_PAGES,
        "program_pages": {k: v["url"] for k, v in PROGRAM_PAGES.items()},
        "badge_pages": {k: v["url"] for k, v in BADGE_PAGES.items()},
        "course_count": len(course_list),
        "program_count": len(programs),
        "badge_count": len(next((p.get("badges") or [] for p in programs if p["id"] == "applied-cs-ms"), [])),
    }
    return course_list, programs, meta


def save_snapshot(
    courses: list[dict[str, Any]],
    programs: list[dict[str, Any]],
    meta: dict[str, Any],
) -> None:
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_COURSES.write_text(json.dumps(courses, indent=2))
    SNAPSHOT_PROGRAMS.write_text(json.dumps(programs, indent=2))
    SNAPSHOT_META.write_text(json.dumps(meta, indent=2))
    from pipeline.synthetic import CAREERS, DEMO_PROFILE, SYNTHETIC_STUDENTS

    synth_dir = DATA_DIR / "synthetic"
    synth_dir.mkdir(parents=True, exist_ok=True)
    (synth_dir / "students.json").write_text(
        json.dumps(SYNTHETIC_STUDENTS + [DEMO_PROFILE], indent=2)
    )
    (synth_dir / "careers.json").write_text(json.dumps(CAREERS, indent=2))


def clean_frames(
    courses: list[dict[str, Any]], programs: list[dict[str, Any]]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cdf = pd.DataFrame(courses)
    cdf["code"] = cdf["code"].str.replace(r"\s+", " ", regex=True).str.strip()
    cdf = cdf.drop_duplicates(subset=["code"]).sort_values("code")
    cdf["title"] = cdf["title"].fillna("").str.strip()
    cdf["description"] = cdf["description"].fillna("").str.strip()
    pdf = pd.DataFrame(programs)
    return cdf, pdf


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS nodes (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  properties JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS edges (
  src TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  rel TEXT NOT NULL,
  dst TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  properties JSONB NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (src, rel, dst)
);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_edges_rel ON edges(rel);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst);
CREATE TABLE IF NOT EXISTS sessions (
  identity_id TEXT PRIMARY KEY,
  active_profile_id TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def connect(dsn: str):
    import psycopg2

    return psycopg2.connect(dsn)


def upsert_node(cur, node_id: str, node_type: str, properties: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO nodes (id, type, properties)
        VALUES (%s, %s, %s::jsonb)
        ON CONFLICT (id) DO UPDATE SET type = EXCLUDED.type, properties = EXCLUDED.properties
        """,
        (node_id, node_type, json.dumps(properties)),
    )


def upsert_edge(cur, src: str, rel: str, dst: str, properties: dict[str, Any] | None = None) -> None:
    cur.execute(
        """
        INSERT INTO edges (src, rel, dst, properties)
        VALUES (%s, %s, %s, %s::jsonb)
        ON CONFLICT (src, rel, dst) DO UPDATE SET properties = EXCLUDED.properties
        """,
        (src, rel, dst, json.dumps(properties or {})),
    )


def json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if pd.isna(value):
            return None
        return value
    if hasattr(value, "item") and not isinstance(value, (bytes, dict, list)):
        try:
            return json_safe(value.item())
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if hasattr(value, "tolist"):
        return json_safe(value.tolist())
    if pd.isna(value):
        return None
    return value


def write_catalog(conn, courses: pd.DataFrame, programs: pd.DataFrame | list[dict[str, Any]], meta: dict[str, Any]) -> None:
    from pipeline.synthetic import CAREERS  # type: ignore

    if isinstance(programs, pd.DataFrame):
        program_rows = [json_safe(row.to_dict()) for _, row in programs.iterrows()]
    else:
        program_rows = [json_safe(row) for row in programs]

    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
        cur.execute(
            """
            SELECT id, properties FROM nodes WHERE type = 'student'
            """
        )
        students = cur.fetchall()
        cur.execute("DELETE FROM nodes WHERE type IN ('course', 'program', 'career', 'meta')")
        for program in program_rows:
            upsert_node(cur, f"program:{program['id']}", "program", program)

        for _, course in courses.iterrows():
            props = json_safe(course.to_dict())
            if isinstance(props.get("programs"), str):
                props["programs"] = json.loads(props["programs"])
            node_id = f"course:{course['code']}"
            upsert_node(cur, node_id, "course", props)

        for _, course in courses.iterrows():
            codes = json_safe(course.get("prerequisite_codes") or [])
            dst = f"course:{course['code']}"
            for prereq in codes:
                src = f"course:{prereq}"
                cur.execute("SELECT 1 FROM nodes WHERE id = %s", (src,))
                if cur.fetchone():
                    upsert_edge(cur, src, "prerequisite_of", dst, {"source": "gvsu-catalog"})

        for career in CAREERS:
            upsert_node(cur, f"career:{career['id']}", "career", career)

        upsert_node(cur, "meta:catalog", "meta", meta)

        for student_id, properties in students:
            props = properties
            if isinstance(props, str):
                props = json.loads(props)
            for entry in props.get("courses") or []:
                if entry.get("status") != "completed":
                    continue
                course_node = f"course:{entry.get('code')}"
                cur.execute("SELECT 1 FROM nodes WHERE id = %s", (course_node,))
                if not cur.fetchone():
                    continue
                upsert_edge(
                    cur,
                    student_id,
                    "completed",
                    course_node,
                    {
                        "gradeLetter": entry.get("gradeLetter"),
                        "term": entry.get("term"),
                        "creditHours": entry.get("creditHours"),
                    },
                )
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest GVSU CS catalog into PostgreSQL")
    parser.add_argument("--fetch", action="store_true", help="Refresh snapshot from the public catalog")
    parser.add_argument("--dsn", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args()
    if not args.dsn:
        print("DATABASE_URL / --dsn is required", file=sys.stderr)
        return 2

    live = args.fetch or not SNAPSHOT_COURSES.exists()
    courses, programs, meta = fetch_catalog(live=live)
    if live:
        save_snapshot(courses, programs, meta)
        print(f"wrote snapshot: {len(courses)} courses, {len(programs)} programs")

    cdf, _pdf = clean_frames(courses, programs)
    conn = connect(args.dsn)
    try:
        sys.path.insert(0, str(ROOT))
        write_catalog(conn, cdf, programs, meta)
    finally:
        conn.close()
    print(f"loaded {len(cdf)} courses into PostgreSQL")
    return 0


if __name__ == "__main__":
    # Running as a script: make `pipeline` importable
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
