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
import psycopg2
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
    return BeautifulSoup(html, "lxml")


def decode_href(href: str) -> str:
    return html_lib.unescape(href or "")


def parse_credits(raw: str | None) -> tuple[float | None, float | None, str | None]:
    if not raw:
        return None, None, None
    cleaned = re.sub(r"\s+", " ", raw).strip()
    m = re.search(
        r"Credits?:\s*(\d+(?:\.\d+)?)(?:\s*to\s*(\d+(?:\.\d+)?))?",
        cleaned,
        re.I,
    )
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


def parse_program_page(html: str, program_id: str, page_url: str) -> dict[str, Any]:
    soup = soup_text(html)
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()
    main = soup.find("main") or soup
    text = main.get_text("\n", strip=True)
    courses: list[dict[str, Any]] = []
    current_section = "general"
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        lower = line.lower()
        if "suggested order of coursework" in lower:
            if courses:
                break
            continue
        if "required computer science" in lower:
            current_section = "required"
        elif "elective computer science" in lower:
            current_section = "elective"
        elif "required non-computing" in lower or "cognate" in lower:
            current_section = "cognate"
        elif line.lower() in {"core", "core courses"} or lower.startswith("core courses"):
            current_section = "core"
        elif "badge" in lower and "course" in lower:
            current_section = "badge"
        elif line.lower() == "electives" or lower.startswith("electives"):
            current_section = "elective"
        elif "capstone" in lower:
            current_section = "capstone"
        elif "data engineering" == lower.strip("1234. "):
            current_section = "core-data-engineering"
        elif "management of systems" in lower:
            current_section = "core-systems-development"
        elif "software engineering" == lower.strip("1234. "):
            current_section = "core-software-engineering"
        elif lower.strip("1234. ") == "networking":
            current_section = "core-networking"
        m = LISTING_RE.search(line)
        if not m:
            continue
        subj, num, title, credits_raw = (
            m.group(1).upper(),
            m.group(2),
            m.group(3).strip(),
            m.group(4),
        )
        credits_min, credits_max, credits_text = parse_credits(credits_raw)
        courses.append(
            {
                "code": f"{subj} {num}",
                "subject": subj,
                "course_number": num,
                "title": title,
                "credits_min": credits_min,
                "credits_max": credits_max,
                "credits_text": credits_text,
                "section": current_section,
                "program_id": program_id,
            }
        )
    info = PROGRAM_PAGES[program_id]
    return {
        "id": program_id,
        "title": info["title"],
        "degree_line": info["degree_line"],
        "major": info["major"],
        "level": info["level"],
        "source_url": page_url,
        "catalog_year": CATALOG_YEAR,
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
        "course_count": len(course_list),
        "program_count": len(programs),
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


def write_catalog(conn, courses: pd.DataFrame, programs: pd.DataFrame, meta: dict[str, Any]) -> None:
    from pipeline.synthetic import CAREERS, SYNTHETIC_STUDENTS, DEMO_PROFILE  # type: ignore

    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
        cur.execute("TRUNCATE TABLE edges, sessions, nodes CASCADE")
        for _, program in programs.iterrows():
            props = json_safe(program.to_dict())
            upsert_node(cur, f"program:{program['id']}", "program", props)

        for _, course in courses.iterrows():
            props = json_safe(course.to_dict())
            if isinstance(props.get("programs"), str):
                props["programs"] = json.loads(props["programs"])
            node_id = f"course:{course['code']}"
            upsert_node(cur, node_id, "course", props)

        # Prerequisite edges: src is prerequisite of dst
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

        for student in SYNTHETIC_STUDENTS + [DEMO_PROFILE]:
            node_id = f"student:{student['syntheticId']}"
            upsert_node(cur, node_id, "student", student)
            for entry in student.get("courses") or []:
                course_node = f"course:{entry['code']}"
                cur.execute("SELECT 1 FROM nodes WHERE id = %s", (course_node,))
                if not cur.fetchone():
                    continue
                if entry.get("status") == "completed":
                    upsert_edge(
                        cur,
                        node_id,
                        "completed",
                        course_node,
                        {
                            "gradeLetter": entry.get("gradeLetter"),
                            "term": entry.get("term"),
                            "creditHours": entry.get("creditHours"),
                        },
                    )

        upsert_node(cur, "meta:catalog", "meta", meta)
        cur.execute(
            """
            INSERT INTO sessions (identity_id, active_profile_id)
            VALUES ('local-demo', 'demo-profile')
            ON CONFLICT (identity_id) DO NOTHING
            """
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

    cdf, pdf = clean_frames(courses, programs)
    conn = connect(args.dsn)
    try:
        # Allow `python pipeline/ingest.py` without installing the package.
        sys.path.insert(0, str(ROOT))
        write_catalog(conn, cdf, pdf, meta)
    finally:
        conn.close()
    print(f"loaded {len(cdf)} courses into PostgreSQL")
    return 0


if __name__ == "__main__":
    # Running as a script: make `pipeline` importable
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
