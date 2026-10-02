"""Career Match Score, survey tilt (3a), and complete-path sketch.

Explicit rules only (Milestone 2). Applied CS M.S. path first.
"""

from __future__ import annotations

import re
from typing import Any

GAP_SCORE = {"strong": 1.0, "moderate": 0.65, "weak": 0.35, "missing": 0.0}
DEMAND_WEIGHT = {"core": 3, "common": 2, "emerging": 1}
CLOSE_RACE_POINTS = 10.0
MAX_TILT = 8.0

# Demand-weighted skills + linked catalog courses per locked career.
CAREER_MATRICES: dict[str, dict[str, Any]] = {
    "data-engineer": {
        "badgeLean": ["database-management", "data-analytics"],
        "linkedCourses": [
            "CIS 353",
            "CIS 335",
            "CIS 660",
            "CIS 673",
            "CIS 676",
            "CIS 635",
            "CIS 671",
            "CIS 655",
        ],
        "skills": [
            {"id": "sql", "label": "SQL / relational databases", "demand": "core", "aliases": ["sql", "postgresql", "mysql", "database", "rdbms"]},
            {"id": "pipelines", "label": "Data pipelines / ETL", "demand": "core", "aliases": ["etl", "pipeline", "data engineering", "airflow", "spark"]},
            {"id": "python-data", "label": "Python for data", "demand": "core", "aliases": ["python", "pandas", "numpy"]},
            {"id": "cloud-data", "label": "Cloud data platforms", "demand": "common", "aliases": ["aws", "azure", "gcp", "s3", "redshift", "snowflake"]},
            {"id": "warehousing", "label": "Warehousing / modeling", "demand": "common", "aliases": ["warehouse", "dimensional", "schema", "dbt"]},
            {"id": "streaming", "label": "Streaming / messaging", "demand": "emerging", "aliases": ["kafka", "kinesis", "pubsub", "streaming"]},
        ],
    },
    "cloud-engineer": {
        "badgeLean": ["distributed-computing", "web-and-mobile-computing"],
        "linkedCourses": [
            "CIS 452",
            "CIS 457",
            "CIS 554",
            "CIS 656",
            "CIS 655",
            "CIS 658",
            "CIS 677",
        ],
        "skills": [
            {"id": "linux", "label": "Linux / OS fundamentals", "demand": "core", "aliases": ["linux", "unix", "operating system"]},
            {"id": "networking", "label": "Networking / TCP-IP", "demand": "core", "aliases": ["network", "tcp", "dns", "vpc"]},
            {"id": "cloud-infra", "label": "Cloud infrastructure", "demand": "core", "aliases": ["aws", "azure", "gcp", "cloud", "ec2", "iam"]},
            {"id": "containers", "label": "Containers / orchestration", "demand": "common", "aliases": ["docker", "kubernetes", "k8s", "container"]},
            {"id": "iac", "label": "Infrastructure as code", "demand": "common", "aliases": ["terraform", "cloudformation", "ansible", "iac"]},
            {"id": "distributed", "label": "Distributed systems", "demand": "emerging", "aliases": ["distributed", "microservice", "high-performance"]},
        ],
    },
    "backend-engineer": {
        "badgeLean": ["software-engineering", "software-design-and-development", "web-and-mobile-computing"],
        "linkedCourses": [
            "CIS 163",
            "CIS 350",
            "CIS 353",
            "CIS 371",
            "CIS 518",
            "SE 512",
            "SE 513",
            "SE 522",
            "CIS 641",
            "CIS 658",
            "CIS 657",
        ],
        "skills": [
            {"id": "server-lang", "label": "Server-side language", "demand": "core", "aliases": ["python", "java", "c#", "go", "node", "typescript", "javascript"]},
            {"id": "apis", "label": "APIs / web services", "demand": "core", "aliases": ["api", "rest", "graphql", "fastapi", "spring", "express"]},
            {"id": "databases-app", "label": "Application databases", "demand": "core", "aliases": ["sql", "postgresql", "mysql", "mongodb", "database"]},
            {"id": "software-eng", "label": "Software engineering practices", "demand": "common", "aliases": ["testing", "git", "agile", "ci", "cd", "requirements"]},
            {"id": "architecture", "label": "Service architecture", "demand": "common", "aliases": ["architecture", "design pattern", "microservice"]},
            {"id": "security-app", "label": "Application security basics", "demand": "emerging", "aliases": ["security", "oauth", "auth", "secure"]},
        ],
    },
    "ml-engineer": {
        "badgeLean": ["data-analytics", "biomedical-informatics"],
        "linkedCourses": [
            "CIS 335",
            "CIS 378",
            "CIS 635",
            "CIS 671",
            "CIS 678",
            "CIS 677",
            "AI 201",
            "STA 330",
        ],
        "skills": [
            {"id": "ml-fundamentals", "label": "ML fundamentals", "demand": "core", "aliases": ["machine learning", "ml", "scikit", "sklearn"]},
            {"id": "python-ml", "label": "Python for ML", "demand": "core", "aliases": ["python", "pandas", "numpy"]},
            {"id": "deep-learning", "label": "Deep learning frameworks", "demand": "common", "aliases": ["pytorch", "tensorflow", "keras", "neural"]},
            {"id": "data-prep", "label": "Feature / data preparation", "demand": "common", "aliases": ["feature", "etl", "cleaning", "sql"]},
            {"id": "eval", "label": "Model evaluation", "demand": "common", "aliases": ["evaluation", "metrics", "validation", "auc"]},
            {"id": "mlops", "label": "MLOps / deployment", "demand": "emerging", "aliases": ["mlops", "deploy", "serving", "docker"]},
        ],
    },
}

SURVEY_CAREER_KEYS = {
    "interestData": "data-engineer",
    "interestCloud": "cloud-engineer",
    "interestBackend": "backend-engineer",
    "interestMl": "ml-engineer",
}

WORK_STYLE_TO_CAREER = {
    "data-systems": "data-engineer",
    "cloud-ops": "cloud-engineer",
    "product-features": "backend-engineer",
    "models": "ml-engineer",
}


def enrich_career(base: dict[str, Any]) -> dict[str, Any]:
    matrix = CAREER_MATRICES.get(base["id"]) or {}
    out = dict(base)
    out["skills"] = matrix.get("skills") or []
    out["linkedCourses"] = matrix.get("linkedCourses") or []
    out["badgeLean"] = matrix.get("badgeLean") or []
    return out


def transcript_present(profile: dict[str, Any]) -> bool:
    """Hard gate: Banner advising context must exist. programId alone is not enough."""
    if profile.get("transcriptReadAt"):
        return True
    if profile.get("transcriptLevel") in {"Undergraduate", "Masters"}:
        return True
    if (profile.get("degreeLine") or "").strip():
        return True
    if (profile.get("college") or "").strip():
        return True
    if (profile.get("transcriptFilename") or "").strip():
        return True
    courses = profile.get("courses") or []
    return any(c.get("status") in {"completed", "in_progress", "planned"} for c in courses)


def resolve_program_id(profile: dict[str, Any], programs: list[dict[str, Any]]) -> str | None:
    if profile.get("programId") in {"cs-bs", "applied-cs-ms"}:
        return profile["programId"]
    level = profile.get("transcriptLevel")
    major = " ".join(
        [
            str(profile.get("major") or ""),
            " ".join(profile.get("majors") or []),
            str(profile.get("degreeLine") or ""),
        ]
    ).lower()
    if level == "Masters" or "master" in major or "applied" in major:
        return "applied-cs-ms" if any(p.get("id") == "applied-cs-ms" for p in programs) else None
    if level == "Undergraduate" or "bachelor" in major or "computer science" in major:
        return "cs-bs" if any(p.get("id") == "cs-bs" for p in programs) else None
    return None


def evidence_summary(profile: dict[str, Any]) -> dict[str, Any]:
    courses = profile.get("courses") or []
    completed = [c for c in courses if c.get("status") == "completed"]
    in_progress = [c for c in courses if c.get("status") == "in_progress"]
    return {
        "transcriptPresent": transcript_present(profile),
        "courseCompleted": len(completed),
        "courseInProgress": len(in_progress),
        "skills": len(profile.get("skills") or []),
        "projects": len(profile.get("projects") or []),
        "experiences": len(profile.get("experiences") or []),
        "certifications": len(profile.get("certifications") or []),
        "hasResumeSignal": bool(
            profile.get("resumeFilename")
            or profile.get("skills")
            or profile.get("projects")
            or profile.get("experiences")
        ),
        "programId": profile.get("programId"),
        "degreeLine": profile.get("degreeLine"),
        "transcriptLevel": profile.get("transcriptLevel"),
    }


def _norm(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _token_hit(haystack: str, alias: str) -> bool:
    alias_n = _norm(alias)
    if not alias_n:
        return False
    return f" {alias_n} " in f" {haystack} " or haystack.startswith(alias_n + " ") or haystack.endswith(" " + alias_n) or haystack == alias_n


def _profile_text_blobs(profile: dict[str, Any]) -> dict[str, str]:
    skill_text = " ".join(_norm(s.get("label")) for s in profile.get("skills") or [])
    project_parts = []
    for p in profile.get("projects") or []:
        project_parts.append(_norm(p.get("name")))
        project_parts.append(_norm(p.get("summary")))
        project_parts.extend(_norm(t) for t in p.get("technologies") or [])
        project_parts.extend(_norm(t) for t in p.get("demonstratesSkills") or [])
    exp_parts = []
    for e in profile.get("experiences") or []:
        exp_parts.append(_norm(e.get("title")))
        exp_parts.append(_norm(e.get("organization")))
        exp_parts.append(_norm(e.get("summary")))
        exp_parts.extend(_norm(h) for h in e.get("highlights") or [])
    cert_parts = []
    for c in profile.get("certifications") or []:
        cert_parts.append(_norm(c.get("name")))
        cert_parts.extend(_norm(t) for t in c.get("taggedSkills") or [])
    return {
        "skills": skill_text,
        "projects": " ".join(project_parts),
        "experience": " ".join(exp_parts),
        "certs": " ".join(cert_parts),
        "summary": _norm(profile.get("summary")),
    }


def _course_index(catalog: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {c.get("code"): c for c in catalog if c.get("code")}


def _skill_sources(
    skill: dict[str, Any],
    profile: dict[str, Any],
    catalog_by_code: dict[str, dict[str, Any]],
    linked_codes: list[str],
) -> set[str]:
    aliases = [skill.get("label") or ""] + list(skill.get("aliases") or [])
    blobs = _profile_text_blobs(profile)
    sources: set[str] = set()

    # Coursework: completed linked courses whose topics/title/desc match aliases, or any completed linked course for this career skill set via topic overlap
    for course in profile.get("courses") or []:
        if course.get("status") != "completed":
            continue
        grade = (course.get("gradeLetter") or "").upper()
        if grade in {"F", "W", "N", "NC", "U"}:
            continue
        code = course.get("code")
        cat = catalog_by_code.get(code) or {}
        hay = " ".join(
            [
                _norm(code),
                _norm(course.get("title")),
                _norm(cat.get("title")),
                _norm(cat.get("description")),
                " ".join(_norm(t) for t in cat.get("topics") or []),
            ]
        )
        if any(_token_hit(hay, a) for a in aliases):
            sources.add("coursework")
            break
        # Soft: completed a course explicitly linked to this career counts toward related core skills only if alias loosely in topics
        if code in linked_codes and any(_token_hit(hay, a) for a in aliases):
            sources.add("coursework")
            break

    if any(_token_hit(blobs["projects"], a) for a in aliases):
        sources.add("project")
    if any(_token_hit(blobs["certs"], a) for a in aliases):
        sources.add("certification")
    if any(_token_hit(blobs["skills"], a) for a in aliases) or any(
        _token_hit(blobs["experience"] + " " + blobs["summary"], a) for a in aliases
    ):
        sources.add("self_report")
    return sources


def gap_label(sources: set[str]) -> str:
    if not sources:
        return "missing"
    if sources == {"self_report"}:
        return "weak"
    non_self = sources - {"self_report"}
    if len(sources) >= 2:
        return "strong"
    if non_self:
        return "moderate"
    return "weak"


def score_career(
    career_id: str,
    profile: dict[str, Any],
    catalog: list[dict[str, Any]],
) -> dict[str, Any]:
    matrix = CAREER_MATRICES.get(career_id) or {"skills": [], "linkedCourses": []}
    skills = matrix.get("skills") or []
    linked = matrix.get("linkedCourses") or []
    catalog_by_code = _course_index(catalog)

    skill_rows = []
    weighted = 0.0
    weight_sum = 0.0
    for skill in skills:
        sources = _skill_sources(skill, profile, catalog_by_code, linked)
        label = gap_label(sources)
        demand = skill.get("demand") or "common"
        w = DEMAND_WEIGHT.get(demand, 2)
        weighted += GAP_SCORE[label] * w
        weight_sum += w
        skill_rows.append(
            {
                "id": skill["id"],
                "label": skill["label"],
                "demand": demand,
                "gap": label,
                "sources": sorted(sources),
            }
        )
    s_factor = (weighted / weight_sum) if weight_sum else 0.0

    completed_codes = {
        c.get("code")
        for c in profile.get("courses") or []
        if c.get("status") == "completed" and c.get("code")
    }
    linked_hit = sum(1 for code in linked if code in completed_codes)
    c_factor = (linked_hit / len(linked)) if linked else 0.0

    required_aliases = []
    for skill in skills:
        required_aliases.extend(skill.get("aliases") or [])
        required_aliases.append(skill.get("label") or "")
    project_hits = 0
    for project in profile.get("projects") or []:
        hay = " ".join(
            [
                _norm(project.get("name")),
                _norm(project.get("summary")),
                " ".join(_norm(t) for t in project.get("technologies") or []),
                " ".join(_norm(t) for t in project.get("demonstratesSkills") or []),
            ]
        )
        if any(_token_hit(hay, a) for a in required_aliases):
            project_hits += 1
    p_factor = min(1.0, project_hits / 2.0)

    cert_hit = False
    for cert in profile.get("certifications") or []:
        hay = " ".join([_norm(cert.get("name")), " ".join(_norm(t) for t in cert.get("taggedSkills") or [])])
        if any(_token_hit(hay, a) for a in required_aliases):
            cert_hit = True
            break
    k_factor = 1.0 if cert_hit else 0.0

    match = int(round(100 * (0.50 * s_factor + 0.25 * c_factor + 0.15 * p_factor + 0.10 * k_factor)))
    match = max(0, min(100, match))
    return {
        "careerId": career_id,
        "match": match,
        "factors": {
            "S": round(s_factor, 3),
            "C": round(c_factor, 3),
            "P": round(p_factor, 3),
            "K": round(k_factor, 3),
        },
        "skills": skill_rows,
        "linkedCoursesCompleted": linked_hit,
        "linkedCoursesTotal": len(linked),
    }


def survey_preference_scores(answers: dict[str, Any] | None) -> dict[str, float]:
    scores = {cid: 0.0 for cid in CAREER_MATRICES}
    if not answers:
        return scores
    for key, career_id in SURVEY_CAREER_KEYS.items():
        try:
            val = float(answers.get(key) or 0)
        except (TypeError, ValueError):
            val = 0.0
        scores[career_id] = max(0.0, min(5.0, val))
    style = answers.get("workStyle")
    if style in WORK_STYLE_TO_CAREER:
        scores[WORK_STYLE_TO_CAREER[style]] += 1.5
    tools = answers.get("tools") or []
    tool_map = {
        "sql": "data-engineer",
        "python": "data-engineer",
        "spark": "data-engineer",
        "kafka": "data-engineer",
        "docker": "cloud-engineer",
        "kubernetes": "cloud-engineer",
        "aws": "cloud-engineer",
        "azure": "cloud-engineer",
        "react": "backend-engineer",
        "apis": "backend-engineer",
        "java": "backend-engineer",
        "tensorflow": "ml-engineer",
        "pytorch": "ml-engineer",
    }
    for tool in tools:
        cid = tool_map.get(str(tool).lower())
        if cid:
            scores[cid] += 0.4
    return scores


def apply_tilt_3a(ranked: list[dict[str, Any]], answers: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Evidence leads; survey may reorder only a close race (within CLOSE_RACE_POINTS)."""
    if len(ranked) < 2:
        return ranked
    prefs = survey_preference_scores(answers)
    out = [dict(row) for row in ranked]
    for row in out:
        row["evidenceMatch"] = row["match"]
        row["surveyPreference"] = round(prefs.get(row["careerId"], 0.0), 2)

    top, second = out[0], out[1]
    gap = top["match"] - second["match"]
    if gap >= CLOSE_RACE_POINTS:
        out[0]["recommended"] = True
        out[0]["reason"] = "Stronger evidence on your transcript and resume."
        if prefs.get(second["careerId"], 0) > prefs.get(top["careerId"], 0):
            out[1]["yourInterest"] = True
            out[1]["reason"] = "Survey leans this way; evidence still favors another path — you can override."
        return out

    # Close race: tip toward higher survey preference
    tipped = sorted(
        out,
        key=lambda r: (r["match"] + min(MAX_TILT, r["surveyPreference"]), r["surveyPreference"]),
        reverse=True,
    )
    for i, row in enumerate(tipped):
        row["recommended"] = i == 0
        if i == 0:
            row["reason"] = "Close evidence race — survey preference tipped this recommendation."
        elif row.get("surveyPreference", 0) >= tipped[0].get("surveyPreference", 0):
            row["yourInterest"] = True
    return tipped


def path_sketch(
    career_id: str,
    profile: dict[str, Any],
    programs: list[dict[str, Any]],
    catalog: list[dict[str, Any]],
    score: dict[str, Any],
) -> dict[str, Any]:
    program_id = resolve_program_id(profile, programs) or "applied-cs-ms"
    program = next((p for p in programs if p.get("id") == program_id), None)
    matrix = CAREER_MATRICES.get(career_id) or {}
    taken = {
        c.get("code")
        for c in profile.get("courses") or []
        if c.get("status") in {"completed", "in_progress"} and c.get("code")
    }
    catalog_by_code = _course_index(catalog)

    def course_row(code: str, why: str) -> dict[str, Any] | None:
        if code in taken:
            return None
        cat = catalog_by_code.get(code) or {"code": code, "title": code}
        return {
            "code": code,
            "title": cat.get("title") or code,
            "credits": cat.get("credits_min"),
            "why": why,
        }

    suggested: list[dict[str, Any]] = []
    for code in matrix.get("linkedCourses") or []:
        row = course_row(code, "Advances this career’s linked catalog courses")
        if row:
            suggested.append(row)
        if len(suggested) >= 6:
            break

    # Skill-gap courses: prefer linked list already; annotate missing/weak skills
    develop = [s for s in score.get("skills") or [] if s.get("gap") in {"missing", "weak"}]

    buckets: list[dict[str, Any]] = []
    badge_names = [b.get("name") for b in profile.get("badges") or [] if b.get("status") != "none"]
    if program_id == "applied-cs-ms" and program:
        rules = program.get("rules") or {}
        courses = program.get("courses") or []
        by_section: dict[str, list] = {}
        for row in courses:
            by_section.setdefault(row.get("section") or "other", []).append(row)
        core_sections = [s for s in by_section if str(s).startswith("core-")]
        filled = 0
        open_areas = []
        for section in core_sections:
            group = by_section[section]
            if any(r.get("code") in taken for r in group):
                filled += 1
            else:
                open_areas.append(
                    {
                        "area": section.replace("core-", "").replace("-", " "),
                        "options": [
                            {"code": r.get("code"), "title": r.get("title")}
                            for r in group
                            if r.get("code") not in taken
                        ],
                    }
                )
        need_core = max(0, 3 - filled) if len(core_sections) >= 4 else max(0, len(core_sections) - filled)
        buckets.append(
            {
                "id": "core",
                "title": "Core areas (3 of 4)",
                "status": "complete" if need_core == 0 else "open",
                "detail": f"{filled} of 4 areas started; need {need_core} more area(s)."
                if need_core
                else "Core area requirement on track.",
                "openAreas": open_areas[:4],
            }
        )
        lean = matrix.get("badgeLean") or []
        badges = program.get("badges") or []
        lean_badges = [b for b in badges if b.get("id") in lean]
        if badge_names:
            buckets.append(
                {
                    "id": "badge",
                    "title": "Badge",
                    "status": "on-record",
                    "detail": f"Banner lists: {', '.join(badge_names)}. Finish remaining badge courses if any slots are open.",
                }
            )
        else:
            buckets.append(
                {
                    "id": "badge",
                    "title": "Badge lean for this career",
                    "status": "suggested",
                    "detail": "No Banner badge yet. For this career, these badges are a natural lean:",
                    "options": [{"id": b.get("id"), "name": b.get("name")} for b in lean_badges],
                }
            )
        buckets.append(
            {
                "id": "credits",
                "title": "33-credit degree",
                "status": "open",
                "detail": (rules.get("electives") or {}).get("note")
                or "Take electives and a capstone to reach 33 credits.",
            }
        )
        buckets.append(
            {
                "id": "capstone",
                "title": "Capstone",
                "status": "open" if "CIS 693" not in taken and "CIS 695" not in taken else "on-track",
                "detail": "CIS 693 Master’s Project, or CIS 695 Thesis (twice).",
            }
        )
    elif program_id == "cs-bs" and program:
        required = [r for r in (program.get("courses") or []) if r.get("section") == "required"]
        left = [r for r in required if r.get("code") not in taken]
        buckets.append(
            {
                "id": "required",
                "title": "Required CIS courses",
                "status": "complete" if not left else "open",
                "detail": f"{len(required) - len(left)} of {len(required)} required courses on your record.",
                "options": [{"code": r.get("code"), "title": r.get("title")} for r in left[:8]],
            }
        )
        buckets.append(
            {
                "id": "electives",
                "title": "Major electives",
                "status": "open",
                "detail": "Choose four electives; prefer ones linked to your career target.",
            }
        )

    return {
        "programId": program_id,
        "careerId": career_id,
        "buckets": buckets,
        "skillsToDevelop": develop[:8],
        "suggestedCourses": suggested,
        "note": "Complete path sketch from program requirements + career lean. Next-semester packing (prereqs / credit cap) comes later.",
    }


def build_career_path_payload(
    profile: dict[str, Any],
    careers: list[dict[str, Any]],
    programs: list[dict[str, Any]],
    catalog: list[dict[str, Any]],
    *,
    answers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = evidence_summary(profile)
    gate_ok = summary["transcriptPresent"]
    warnings: list[str] = []
    if not summary["hasResumeSignal"]:
        warnings.append(
            "No resume skills, projects, or experience on your profile yet. Upload a resume or add them manually — recommended for a better lean."
        )
    if not gate_ok:
        return {
            "ready": False,
            "gate": {
                "signedIn": True,
                "transcriptPresent": False,
                "programId": resolve_program_id(profile, programs),
            },
            "evidence": summary,
            "warnings": warnings
            + ["Upload a Banner advising transcript on Profile before taking the career survey."],
            "rankings": [],
            "path": None,
            "survey": profile.get("careerSurvey"),
        }

    program_id = resolve_program_id(profile, programs)
    if not program_id:
        warnings.append("Pick Applied CS M.S. or Computer Science B.S. on Profile so the path map can load.")

    survey = answers if answers is not None else (profile.get("careerSurvey") or {}).get("answers")
    rankings = []
    for career in careers:
        cid = career.get("id")
        if cid not in CAREER_MATRICES:
            continue
        scored = score_career(cid, profile, catalog)
        scored["label"] = career.get("label")
        scored["summary"] = career.get("summary")
        rankings.append(scored)
    rankings.sort(key=lambda r: r["match"], reverse=True)
    rankings = apply_tilt_3a(rankings, survey)

    recommended_id = next((r["careerId"] for r in rankings if r.get("recommended")), rankings[0]["careerId"] if rankings else None)
    chosen = profile.get("targetCareer") or recommended_id
    path = None
    chosen_score = next((r for r in rankings if r["careerId"] == chosen), rankings[0] if rankings else None)
    if chosen and chosen_score and program_id:
        path = path_sketch(chosen, profile, programs, catalog, chosen_score)

    return {
        "ready": True,
        "gate": {
            "signedIn": True,
            "transcriptPresent": True,
            "programId": program_id,
            "needsProgramPick": program_id is None,
        },
        "evidence": summary,
        "warnings": warnings,
        "rankings": rankings,
        "recommendedCareerId": recommended_id,
        "selectedCareerId": profile.get("targetCareer"),
        "path": path,
        "survey": profile.get("careerSurvey"),
        "attribution": "Approximate Match % from your StudentOS profile and the public catalog. Not official SIS or job placement.",
    }
