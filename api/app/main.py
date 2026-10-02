from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.app import db
from api.app.models import CareerPick, ProfileUpdate, SessionUpdate, TranscriptImportResult
from pipeline.ingest import SCHEMA_SQL, fetch_catalog, save_snapshot, write_catalog, clean_frames

app = FastAPI(
    title="StudentOS API",
    version="0.4.0",
    description="Slice A: GVSU CS catalog, synthetic profiles, and target career.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ensure_loaded() -> None:
    with db.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            cur.execute("SELECT COUNT(*) FROM nodes WHERE type = 'course'")
            count = cur.fetchone()[0]
            if count:
                return
            live = os.environ.get("INGEST_FETCH", "").lower() in {"1", "true", "yes"}
            courses, programs, meta = fetch_catalog(live=live)
            if live:
                save_snapshot(courses, programs, meta)
            cdf, pdf = clean_frames(courses, programs)
            write_catalog(conn, cdf, pdf, meta)


@app.on_event("startup")
def startup() -> None:
    _ensure_loaded()


@app.get("/health")
def health() -> dict:
    try:
        row = db.fetch_one("SELECT COUNT(*) AS n FROM nodes WHERE type = 'course'")
        return {"ok": True, "courses": row["n"] if row else 0}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "error": str(exc)}


@app.get("/api/meta")
def meta() -> dict:
    row = db.fetch_one("SELECT properties FROM nodes WHERE id = 'meta:catalog'")
    course_n = db.fetch_one("SELECT COUNT(*) AS n FROM nodes WHERE type = 'course'")
    student_n = db.fetch_one("SELECT COUNT(*) AS n FROM nodes WHERE type = 'student'")
    props = row["properties"] if row else {}
    if isinstance(props, str):
        props = json.loads(props)
    return {
        **props,
        "courseCount": course_n["n"] if course_n else 0,
        "studentCount": student_n["n"] if student_n else 0,
        "slice": "A",
        "identity": "local-demo",
    }


@app.get("/api/session")
def get_session() -> dict:
    row = db.fetch_one(
        "SELECT identity_id, active_profile_id, updated_at FROM sessions WHERE identity_id = 'local-demo'"
    )
    if not row:
        db.execute(
            "INSERT INTO sessions (identity_id, active_profile_id) VALUES ('local-demo', 'demo-profile')"
        )
        row = {
            "identity_id": "local-demo",
            "active_profile_id": "demo-profile",
            "updated_at": None,
        }
    return {
        "identityId": row["identity_id"],
        "identityLabel": "Local demo",
        "activeProfileId": row["active_profile_id"],
        "updatedAt": str(row["updated_at"]) if row.get("updated_at") else None,
        "note": "Campus SSO is not part of this prototype. This is a local identity slot, not a GVSU login.",
    }


@app.put("/api/session")
def put_session(body: SessionUpdate) -> dict:
    student = db.fetch_one(
        "SELECT id FROM nodes WHERE id = %s AND type = 'student'",
        (f"student:{body.activeProfileId}",),
    )
    if not student:
        raise HTTPException(status_code=404, detail="No student profile with that id.")
    db.execute(
        """
        INSERT INTO sessions (identity_id, active_profile_id)
        VALUES ('local-demo', %s)
        ON CONFLICT (identity_id) DO UPDATE SET
          active_profile_id = EXCLUDED.active_profile_id,
          updated_at = now()
        """,
        (body.activeProfileId,),
    )
    return get_session()


def _node_to_profile(row: dict) -> dict:
    props = row["properties"]
    if isinstance(props, str):
        props = json.loads(props)
    props["syntheticId"] = row["id"].removeprefix("student:")
    return props


@app.get("/api/profiles")
def list_profiles() -> list[dict]:
    rows = db.fetch_all(
        "SELECT id, properties FROM nodes WHERE type = 'student' ORDER BY id"
    )
    return [_node_to_profile(r) for r in rows]


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str) -> dict:
    row = db.fetch_one(
        "SELECT id, properties FROM nodes WHERE id = %s AND type = 'student'",
        (f"student:{profile_id}",),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return _node_to_profile(row)


@app.post("/api/profiles")
def create_profile() -> dict:
    from pipeline.synthetic import DEMO_PROFILE

    props = json.loads(json.dumps(DEMO_PROFILE))
    db.execute(
        """
        INSERT INTO nodes (id, type, properties)
        VALUES ('student:demo-profile', 'student', %s)
        ON CONFLICT (id) DO UPDATE SET properties = EXCLUDED.properties
        """,
        (db.as_json(props),),
    )
    db.execute(
        """
        INSERT INTO sessions (identity_id, active_profile_id)
        VALUES ('local-demo', 'demo-profile')
        ON CONFLICT (identity_id) DO UPDATE SET
          active_profile_id = 'demo-profile',
          updated_at = now()
        """
    )
    # Creating a fresh demo profile also drops prior completed-course edges for it.
    db.execute("DELETE FROM edges WHERE src = 'student:demo-profile' AND rel = 'completed'")
    return get_profile("demo-profile")


@app.put("/api/profiles/{profile_id}")
def update_profile(profile_id: str, body: ProfileUpdate) -> dict:
    row = db.fetch_one(
        "SELECT id, properties FROM nodes WHERE id = %s AND type = 'student'",
        (f"student:{profile_id}",),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found.")
    props = row["properties"]
    if isinstance(props, str):
        props = json.loads(props)
    patch = body.model_dump(exclude_unset=True)
    for key, value in patch.items():
        if hasattr(value, "model_dump"):
            props[key] = value.model_dump()
        elif isinstance(value, list):
            props[key] = [
                v.model_dump() if hasattr(v, "model_dump") else v for v in value
            ]
        else:
            props[key] = value
    props["syntheticId"] = profile_id
    db.execute(
        "UPDATE nodes SET properties = %s WHERE id = %s",
        (db.as_json(props), f"student:{profile_id}"),
    )
    db.execute("DELETE FROM edges WHERE src = %s AND rel = 'completed'", (f"student:{profile_id}",))
    for entry in props.get("courses") or []:
        if entry.get("status") != "completed":
            continue
        course_node = f"course:{entry.get('code')}"
        exists = db.fetch_one("SELECT 1 AS ok FROM nodes WHERE id = %s", (course_node,))
        if not exists:
            continue
        db.execute(
            """
            INSERT INTO edges (src, rel, dst, properties)
            VALUES (%s, 'completed', %s, %s)
            ON CONFLICT (src, rel, dst) DO UPDATE SET properties = EXCLUDED.properties
            """,
            (
                f"student:{profile_id}",
                course_node,
                db.as_json(
                    {
                        "gradeLetter": entry.get("gradeLetter"),
                        "term": entry.get("term"),
                        "creditHours": entry.get("creditHours"),
                    }
                ),
            ),
        )
    return get_profile(profile_id)


@app.put("/api/profiles/{profile_id}/career")
def set_career(profile_id: str, body: CareerPick) -> dict:
    career = db.fetch_one(
        "SELECT id FROM nodes WHERE id = %s AND type = 'career'",
        (f"career:{body.targetCareer}",),
    )
    if not career:
        raise HTTPException(
            status_code=400,
            detail="Unknown career. Use data-engineer, cloud-engineer, backend-engineer, or ml-engineer.",
        )
    return update_profile(profile_id, ProfileUpdate(targetCareer=body.targetCareer))


@app.get("/api/careers")
def list_careers() -> list[dict]:
    rows = db.fetch_all(
        "SELECT id, properties FROM nodes WHERE type = 'career' ORDER BY id"
    )
    out = []
    for row in rows:
        props = row["properties"]
        if isinstance(props, str):
            props = json.loads(props)
        props["id"] = row["id"].removeprefix("career:")
        out.append(props)
    return out


def _course_from_node(row: dict) -> dict:
    props = row["properties"]
    if isinstance(props, str):
        props = json.loads(props)
    props["id"] = row["id"].removeprefix("course:")
    return props


@app.get("/api/courses")
def list_courses(
    q: str | None = None,
    program: str | None = None,
    level: str | None = None,
    topic: str | None = None,
    subject: str | None = None,
) -> dict:
    rows = db.fetch_all(
        "SELECT id, properties FROM nodes WHERE type = 'course' ORDER BY id"
    )
    courses = [_course_from_node(r) for r in rows]
    if q:
        needle = q.lower().strip()
        courses = [
            c
            for c in courses
            if needle in (c.get("code") or "").lower()
            or needle in (c.get("title") or "").lower()
            or needle in (c.get("description") or "").lower()
        ]
    if program:
        courses = [c for c in courses if program in (c.get("programs") or {})]
    if level:
        courses = [c for c in courses if (c.get("level") or "").lower() == level.lower()]
    if topic:
        courses = [c for c in courses if topic in (c.get("topics") or [])]
    if subject:
        courses = [c for c in courses if (c.get("subject") or "").upper() == subject.upper()]
    return {"count": len(courses), "courses": courses}


@app.get("/api/courses/{code}")
def get_course(code: str) -> dict:
    normalized = code.replace("-", " ").replace("_", " ")
    normalized = " ".join(normalized.split()).upper()
    # CIS353 -> CIS 353
    import re

    m = re.match(r"^([A-Z]{2,4})\s*(\d{3})$", normalized)
    if m:
        normalized = f"{m.group(1)} {m.group(2)}"
    row = db.fetch_one(
        "SELECT id, properties FROM nodes WHERE id = %s AND type = 'course'",
        (f"course:{normalized}",),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Course not in the ingested catalog.")
    course = _course_from_node(row)
    prereqs = db.fetch_all(
        """
        SELECT n.id, n.properties
        FROM edges e
        JOIN nodes n ON n.id = e.src
        WHERE e.dst = %s AND e.rel = 'prerequisite_of'
        ORDER BY n.id
        """,
        (row["id"],),
    )
    unlocks = db.fetch_all(
        """
        SELECT n.id, n.properties
        FROM edges e
        JOIN nodes n ON n.id = e.dst
        WHERE e.src = %s AND e.rel = 'prerequisite_of'
        ORDER BY n.id
        """,
        (row["id"],),
    )
    course["prerequisiteCourses"] = [_course_from_node(r) for r in prereqs]
    course["unlocksCourses"] = [_course_from_node(r) for r in unlocks]
    return course


@app.get("/api/programs")
def list_programs() -> list[dict]:
    rows = db.fetch_all(
        "SELECT id, properties FROM nodes WHERE type = 'program' ORDER BY id"
    )
    out = []
    for row in rows:
        props = row["properties"]
        if isinstance(props, str):
            props = json.loads(props)
        props["id"] = row["id"].removeprefix("program:")
        out.append(props)
    return out


@app.post("/api/transcripts/import", response_model=TranscriptImportResult)
async def import_transcript(file: UploadFile = File(...)) -> TranscriptImportResult:
    name = file.filename or "upload"
    # Read and discard. Do not persist the file or extract personal values.
    await file.read()
    return TranscriptImportResult(
        accepted=True,
        filename=name,
        parsed=False,
        mappedCourses=[],
        message=(
            "The file was received locally and was not stored. "
            "Banner advising-transcript parsing (Student Information, Awarded, "
            "Institution Credit, Totals, Courses in Progress) is stubbed in this slice. "
            "Add courses on the profile by catalog code instead. "
            "Do not commit transcripts or personal identifiers to git."
        ),
    )
