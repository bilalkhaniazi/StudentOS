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
from api.app.models import (
    BadgeEntry,
    CareerPick,
    IdentityEnsure,
    ProfileUpdate,
    ResumeImportResult,
    SessionUpdate,
    TranscriptImportResult,
    CourseEntry,
)
from api.app.identity import empty_profile, profile_id_for_email
from pipeline.ingest import SCHEMA_SQL, fetch_catalog, save_snapshot, write_catalog, clean_frames

app = FastAPI(
    title="StudentOS API",
    version="0.4.0",
    description="Slice A: GVSU CS catalog, Google login, Banner transcript import, and resume intake.",
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
    student_n = db.fetch_one(
        """
        SELECT COUNT(*) AS n FROM nodes
        WHERE type = 'student'
          AND COALESCE(properties->>'synthetic', 'false') <> 'true'
        """
    )
    props = row["properties"] if row else {}
    if isinstance(props, str):
        props = json.loads(props)
    return {
        **props,
        "courseCount": course_n["n"] if course_n else 0,
        "studentCount": student_n["n"] if student_n else 0,
        "slice": "A",
        "identity": "google",
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
        "identityLabel": "Signed-in student",
        "activeProfileId": row["active_profile_id"],
        "updatedAt": str(row["updated_at"]) if row.get("updated_at") else None,
        "note": "Each Google login gets its own academic profile. Synthetic demo students are not used.",
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
    props.setdefault("majors", [props["major"]] if props.get("major") else [])
    props.setdefault("badges", [])
    props.setdefault("email", None)
    props.setdefault("resumeFilename", None)
    props.setdefault("resumeReadAt", None)
    props.setdefault("resumeParsed", None)
    props.setdefault("studentType", None)
    props.setdefault("experiences", [])
    props.setdefault("education", [])
    props.setdefault("languages", [])
    props.setdefault("projects", props.get("projects") or [])
    props.setdefault("skills", props.get("skills") or [])
    props.setdefault("certifications", props.get("certifications") or [])
    return props


@app.get("/api/profiles")
def list_profiles() -> list[dict]:
    rows = db.fetch_all(
        """
        SELECT id, properties FROM nodes
        WHERE type = 'student'
          AND COALESCE(properties->>'synthetic', 'false') <> 'true'
          AND id NOT LIKE 'student:synth-%'
          AND id <> 'student:demo-profile'
        ORDER BY id
        """
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


@app.post("/api/profiles/ensure")
def ensure_profile(body: IdentityEnsure) -> dict:
    email = (body.email or "").strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="A signed-in email is required.")
    profile_id = profile_id_for_email(email)
    display = (body.displayName or "").strip() or email.split("@")[0]
    row = db.fetch_one(
        "SELECT id, properties FROM nodes WHERE id = %s AND type = 'student'",
        (f"student:{profile_id}",),
    )
    if not row:
        props = empty_profile(profile_id, email=email, display_name=display)
        db.execute(
            """
            INSERT INTO nodes (id, type, properties)
            VALUES (%s, 'student', %s)
            """,
            (f"student:{profile_id}", db.as_json(props)),
        )
    else:
        props = row["properties"]
        if isinstance(props, str):
            props = json.loads(props)
        props["email"] = email
        props["displayName"] = display
        props["synthetic"] = False
        props["syntheticId"] = profile_id
        db.execute(
            "UPDATE nodes SET properties = %s WHERE id = %s",
            (db.as_json(props), f"student:{profile_id}"),
        )
    db.execute(
        """
        INSERT INTO sessions (identity_id, active_profile_id)
        VALUES (%s, %s)
        ON CONFLICT (identity_id) DO UPDATE SET
          active_profile_id = EXCLUDED.active_profile_id,
          updated_at = now()
        """,
        (email, profile_id),
    )
    return get_profile(profile_id)


@app.post("/api/profiles")
def create_profile_removed() -> None:
    raise HTTPException(
        status_code=410,
        detail="Demo profiles are gone. Sign in with Google; StudentOS opens your own record.",
    )


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
async def import_transcript(
    file: UploadFile = File(...),
    profile_id: str | None = None,
) -> TranscriptImportResult:
    from api.app.banner import attach_catalog, parse_banner, parsed_to_payload
    from api.app.pdf_text import pdf_bytes_to_text

    name = file.filename or "upload.pdf"
    content_type = (file.content_type or "").lower()
    if not name.lower().endswith(".pdf") and "pdf" not in content_type:
        raise HTTPException(status_code=400, detail="Upload a PDF saved from Banner View Academic Transcript.")

    data = await file.read()
    # Bytes stay in memory only. Nothing is written to disk.
    if not data:
        raise HTTPException(status_code=400, detail="That file was empty.")
    if len(data) > 12 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="That PDF is too large. Export the Banner print again as a smaller file.")

    session = get_session()
    target_id = profile_id or session.get("activeProfileId")
    if not target_id:
        raise HTTPException(status_code=400, detail="Sign in first so the courses can attach to your profile.")
    existing = db.fetch_one(
        "SELECT id FROM nodes WHERE id = %s AND type = 'student'",
        (f"student:{target_id}",),
    )
    if not existing:
        raise HTTPException(status_code=404, detail="No student profile is selected to receive the courses.")

    try:
        text, method = pdf_bytes_to_text(data)
    except Exception:
        return TranscriptImportResult(
            accepted=True,
            filename=name,
            parsed=False,
            profileId=target_id,
            message="The file was read in memory and discarded, but StudentOS could not open it as a PDF.",
        )
    del data

    parsed = parse_banner(text, method=method)
    catalog, programs = _catalog_and_programs()
    parsed = attach_catalog(parsed, catalog, programs)
    payload = parsed_to_payload(parsed)

    if not parsed.completed() and not parsed.in_progress():
        return TranscriptImportResult(
            accepted=True,
            filename=name,
            parsed=False,
            profileId=target_id,
            method=method,
            warnings=payload["warnings"],
            message=(
                "The PDF was not stored. StudentOS could not find course rows. "
                "In Banner, open View Academic Transcript, choose Transcript Level and Advising, "
                "then print the page and save it as a PDF."
            ),
        )

    update = ProfileUpdate(
        transcriptLevel=payload["transcriptLevel"] or None,
        transcriptType=payload.get("transcriptType"),
        college=payload["college"],
        degreeLine=payload["degreeLine"],
        major=payload["major"],
        majors=payload.get("majors") or ([payload["major"]] if payload.get("major") else []),
        majorAndDepartment=payload["major"],
        badges=[BadgeEntry(**row) for row in payload.get("badges") or []],
        remainingCredits=payload["remainingCredits"],
        courses=[CourseEntry(**row) for row in payload["courses"]],
    )
    updated = update_profile(target_id, update)
    n_done = len(payload["completed"])
    n_now = len(payload["inProgress"])
    n_left = len(payload["remaining"])
    n_badges = len(payload.get("badges") or [])
    how = "printed page (OCR)" if method == "ocr" else "selectable text"
    badge_bit = f" and {n_badges} badge" + ("s" if n_badges != 1 else "") if n_badges else " and no Banner badge"
    return TranscriptImportResult(
        accepted=True,
        filename=name,
        parsed=True,
        profileId=updated.get("syntheticId", target_id),
        transcriptLevel=payload["transcriptLevel"],
        college=payload["college"],
        degreeLine=payload["degreeLine"],
        major=payload["major"],
        majors=payload.get("majors") or [],
        badges=[BadgeEntry(**row) for row in payload.get("badges") or []],
        remainingCredits=payload["remainingCredits"],
        method=method,
        warnings=payload["warnings"],
        completed=payload["completed"],
        inProgress=payload["inProgress"],
        remaining=payload["remaining"],
        mappedCourses=payload["completed"] + payload["inProgress"],
        message=(
            f"Read {n_done} completed, {n_now} in progress, and {n_left} still needed "
            f"from the catalog{badge_bit} ({how}). The PDF was discarded. "
            "Student ID and GPA were not saved. Your name stays the Google sign-in name."
        ),
    )


def _catalog_and_programs() -> tuple[list[dict], list[dict]]:
    course_rows = db.fetch_all("SELECT properties FROM nodes WHERE type = 'course'")
    program_rows = db.fetch_all("SELECT properties FROM nodes WHERE type = 'program'")
    courses = []
    for row in course_rows:
        props = row["properties"]
        if isinstance(props, str):
            props = json.loads(props)
        courses.append(props)
    programs = []
    for row in program_rows:
        props = row["properties"]
        if isinstance(props, str):
            props = json.loads(props)
        programs.append(props)
    return courses, programs


@app.post("/api/resumes/import", response_model=ResumeImportResult)
async def import_resume(
    file: UploadFile = File(...),
    profile_id: str | None = None,
) -> ResumeImportResult:
    from datetime import datetime, timezone

    from api.app.resume import merge_resume_into_profile, parse_resume_bytes

    name = file.filename or "resume"
    lower = name.lower()
    allowed = (".pdf", ".doc", ".docx", ".txt")
    if not any(lower.endswith(ext) for ext in allowed):
        raise HTTPException(
            status_code=400,
            detail="Upload a PDF, Word, or text resume (.pdf, .docx, .doc, .txt).",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="That file was empty.")
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="That resume is too large. Try a PDF under 8 MB.")

    session = get_session()
    target_id = profile_id or session.get("activeProfileId")
    if not target_id:
        del data
        raise HTTPException(status_code=400, detail="Sign in first so the resume can attach to your profile.")
    row = db.fetch_one(
        "SELECT id, properties FROM nodes WHERE id = %s AND type = 'student'",
        (f"student:{target_id}",),
    )
    if not row:
        del data
        raise HTTPException(status_code=404, detail="No student profile is signed in.")

    try:
        parsed = parse_resume_bytes(data, name)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read that resume. Try a text PDF or .docx. ({exc})",
        ) from exc
    finally:
        data = b""

    props = row["properties"]
    if isinstance(props, str):
        props = json.loads(props)
    merge_resume_into_profile(props, parsed)
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    props["resumeFilename"] = name
    props["resumeReadAt"] = stamp
    props["syntheticId"] = target_id
    db.execute(
        "UPDATE nodes SET properties = %s WHERE id = %s",
        (db.as_json(props), f"student:{target_id}"),
    )

    got_any = bool(
        parsed.experiences
        or parsed.projects
        or parsed.skills
        or parsed.education
        or parsed.languages
        or parsed.summary
    )
    message = (
        f"Parsed {name} in memory and discarded the file. "
        f"Found {len(parsed.experiences)} experience(s), {len(parsed.projects)} project(s), "
        f"{len(parsed.skills)} skill(s). Review and edit below — or enter details manually."
        if got_any
        else (
            f"Read {name} in memory and discarded it, but could not confidently extract sections. "
            "Enter experience, projects, and skills manually below."
        )
    )
    return ResumeImportResult(
        accepted=True,
        stored=False,
        parsed=got_any,
        filename=name,
        profileId=target_id,
        message=message,
        method=parsed.method,
        warnings=parsed.warnings,
        summary=parsed.summary,
        experienceCount=len(parsed.experiences),
        projectCount=len(parsed.projects),
        skillCount=len(parsed.skills),
        educationCount=len(parsed.education),
        languageCount=len(parsed.languages),
        certificationCount=len(parsed.certifications),
        studentTypeHint=parsed.studentTypeHint,
    )
