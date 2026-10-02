# StudentOS — Milestone 2 decision memo

**Project:** StudentOS — a data-driven student decision intelligence platform  
**For:** Muhammad Bilal Ali Khan  
**Status:** **LOCKED** — Bilal locked Milestone 2 with amendments (2026-09-18).  
**Milestone 1:** Confirmed — the [build plan](build-plan.md) order and nine-capability done list are the working sequence.  
**This ships:** the eight Milestone 2 locks, including amendments. Diagrams that match these locks are in [architecture.md](architecture.md). **Not yet:** code, dataset downloads at scale, UI chrome.  
**Sources:** [project briefing](project-context.md), [Master's Final Semester Project Proposal](masters-proposal.pdf), confirmed [build plan](build-plan.md).

Kept from the proposal (already stated, not reopened): **Python + PostgreSQL + Pandas/SQL.** Batch pipeline. Graph traversal + explicit rules as the starting recommendation method (the PDF does not require ML).

Not invented here: thesis/report/defense requirements (the PDF does not list them). Research metrics stay in Milestone 9.

**Cost bar:** free sources and free tools only. No paid APIs, no Neo4j, no commercial job-board licenses.

---

## How to read this

Each item is **locked**. Amendments vs the original recommendation are marked. Alternatives below an item were considered and **not chosen**.

---

## 1. Career Match Score and gap labels — LOCKED (as recommended)

**Locked:** An explicit, explainable **evidence-count rule**. The PDF’s 87% / 76% / 71% / 64% table and Strong / Moderate / Weak / Missing labels are **illustrations, not targets**. This formula will not be calibrated to those numbers.

**Student evidence for a skill** (independent sources, counted once each):

| Source | Counts as evidence if… |
| --- | --- |
| Coursework | Student completed a course linked to that skill (grade ≥ 2.0 if a grade is present; otherwise completion counts) |
| Project | A listed project is tagged as demonstrating that skill |
| Certification | A listed certification is tagged to that skill |
| Self-report | The student listed the skill on the profile |

**Gap label** from how many independent sources support the skill, against skills required by the selected career:

| Label | Rule |
| --- | --- |
| **Missing** | 0 sources |
| **Weak** | 1 source, and it is only self-report |
| **Moderate** | 1 source that is a course, project, or certification |
| **Strong** | 2 or more independent sources |

**Career Match Score** (integer 0–100, shown as “approximate %”) for one career:

\[
\text{Match} = 100 \times (0.50\,S + 0.25\,C + 0.15\,P + 0.10\,K)
\]

- **S (skills):** demand-weighted coverage of that career’s required skills. Per skill, Strong = 1.00, Moderate = 0.65, Weak = 0.35, Missing = 0. Demand weights: **core = 3**, **common = 2**, **emerging = 1** (from the job/career source in item 3, not from the PDF examples).
- **C (coursework):** fraction of that career’s linked catalog courses the student has completed.
- **P (projects):** \(\min(1,\ \text{projects demonstrating a required skill}\ /\ 2)\).
- **K (certifications):** 1 if the student has at least one certification tagged to a required skill, else 0.

The UI must show **each factor’s contribution** (and the skills that pulled the score down). Prerequisites affect **recommendations**, not this percentage.

**Why this lock:** Matches the proposal’s “approximate” and “explained, not a black box” bars with a rule a student can audit in one screen.

**Not chosen:** Skills-only score (`100 × S`). A learned model remains out of scope unless added later — the PDF does not require ML.

---

## 2. Knowledge-graph storage — LOCKED (as recommended)

**Locked:** **PostgreSQL node + edge tables** in the same database the pipeline already writes to. No separate graph product. **No Neo4j** (cost and ops; the PDF pipeline ends at PostgreSQL).

Shape (drawn in [Milestone 3](architecture.md)):

- `nodes(id, type, properties)` — types include student, course, skill, project, technology, career, job
- `edges(src, rel, dst, properties)` — the five proposal relations: course–teaches–skill, skill–required_by–job, course–prerequisite_of–course, project–demonstrates–skill, student–completed–course

Traversal for *“I want to become a Data Engineer. Which courses should I take to close my current skill gaps?”* is SQL joins plus a recursive CTE for prerequisite chains.

**Why this lock:** Free; the five named relations do not need a second database to be traversable.

**Not chosen:** Apache AGE (Cypher) inside PostgreSQL. **Not chosen:** Neo4j alongside PostgreSQL.

---

## 3. Named datasets — LOCKED (amended)

**Locked:** four **free** sources. Refresh = **batch, when we rerun the pipeline.** No GVSU SIS. No LinkedIn / Indeed scrape. **No paid APIs.**

**Amendment:** catalog coverage is GVSU CS **B.S. and M.S.** (not B.S. only). A personal transcript may be used for **local import testing**; **never put real transcripts in git**.

GVSU has no standalone catalog degree titled “Computer Science M.S.” The public CS graduate degree we ingest is **Applied Computer Science M.S.** (College of Computing), together with the **Computer Science B.S.**

| Role | Named source | License / use | What we take |
| --- | --- | --- | --- |
| **CS catalog + degree requirements + prerequisites** | Current published GVSU catalog: [CIS subject](https://www.gvsu.edu/catalog/subject/computer-information-systems.htm) + [Computer Science B.S.](https://www.gvsu.edu/catalog/program/bachelor-of-science-in-computer-science.htm) + [Applied Computer Science M.S.](https://www.gvsu.edu/catalog/program/master-of-science-in-applied-computer-science.htm) (program pages also sit under [Computer Science](https://www.gvsu.edu/catalog/department/computer-science.htm) and [Applied Computer Science](https://www.gvsu.edu/catalog/department/master-of-science-in-computer-information-systems.htm)). Related prefixes that appear on those program pages (e.g. CIS, SE) are in scope as **structured catalog fields**, not extra departments. Pin the catalog year at first ingest. | Public catalog pages. Attribute Grand Valley State University. Store **structured fields only** (code, title, credits, prerequisites, description, program required/elective lists). Prototype use, not a republished catalog, not official SIS. | GVSU CS B.S. and Applied CS M.S. courses, credits, prereqs, required/elective lists. Course→skill links are **derived in the pipeline** (title/description vs taxonomy), not official GVSU tags. |
| **Skill taxonomy + public career information** | [O\*NET 31.0 Database](https://www.onetcenter.org/database.html) — especially **Software Skills**, **Essential Skills**, **Occupation Data**, **Job Titles** / Sample of Reported Titles. CC BY 4.0; credit O\*NET 31.0 Database and USDOL/ETA; note our mappings as modifications. | CC BY 4.0 | Canonical skill/technology labels; occupation descriptions; Hot Technology flags used as demand hints. |
| **Public job postings** | Frozen snapshot from **The Muse Public API v2** [`GET https://www.themuse.com/api/public/jobs`](https://www.themuse.com/developers/api/v2), filtered to Engineering / Data Science and to titles matching the four example careers. Store a **dated local snapshot** (title, company, category, location, description, source URL). | Public API; abide by [API terms](https://www.themuse.com/developers/api/v2/terms). We are not a job board: show evidence snippets + link out, do not host a competing apply flow. Anonymous access is enough for a one-shot batch (key optional). **No paid job APIs.** | “Current job-market requirements” text to extract/match skills for research question 4 later. |
| **Student records** | **Synthetic academic records we author** (not a third-party file), covering **both** CS B.S. and Applied CS M.S. First set: **six B.S.** profiles — (1) the proposal’s Data Engineer example (databases + cloud + ML coursework; limited Kafka / Airflow / Terraform), (2) empty/new student, (3) backend-leaning, (4) ML-leaning, (5) missing-prerequisites, (6) heavy remaining credit load — **plus two M.S.** profiles — (7) Applied CS M.S. Data Engineering-track (e.g. CIS 660 / databases / cloud; same Kafka / Airflow / Terraform gap as the PDF example), (8) empty/new M.S. student. | Original synthetic data. No real student PII in the repo. | Test/demo profiles for slices 1–9. |
| **Local-only test transcript (not a repo dataset)** | Optional **personal transcript** the user may supply for import testing. | Private. **Never commit** transcripts, grade reports, or real student identifiers to git. | Exercises transcript import against the ingested catalog. Not a pipeline source. |

**Career ↔ O\*NET-SOC map** (locked, swappable later only if Bilal reopens this item):

| Proposal career | O\*NET-SOC | Why this code |
| --- | --- | --- |
| Data Engineer | **15-1243.00 Database Architects** | Sample of reported titles includes **Data Engineer**. |
| Cloud Engineer | **15-1299.08 Computer Systems Engineers/Architects** | Infrastructure / systems / architect titles; cloud tools appear in Software Skills. |
| Backend Engineer | **15-1252.00 Software Developers** | Application / software engineer titles. |
| ML Engineer | **15-2051.00 Data Scientists** | Includes machine-learning work and tools (e.g. Spark, Kafka, Snowflake). |

**Why this lock:** Every proposal source type the prototype needs is a named, license-usable **free** public or synthetic input; both CS degree levels the prototype must demo are on the public catalog.

**Not chosen:** paid APIs; Lightcast / LinkedIn / Indeed; ESCO as the primary taxonomy; Kaggle/USAJOBS as the primary job source; B.S.-only catalog coverage.

Out of this list on purpose: student-generated course feedback (potential in the PDF; no collection/privacy design).

---

## 4. Web stack — LOCKED (as recommended)

**Locked:** **FastAPI** (Python API next to the pipeline) **+ Next.js / TypeScript / Tailwind** (student UI). shadcn/ui for ordinary controls when we reach screens. Free stack.

**Why this lock:** The PDF names Python and “a web development framework,” not a specific UI library. This split keeps ingestion/scoring in Python and gives the nine student capabilities a normal web app.

**Not chosen:** Django (templates or Django REST). **Not chosen:** FastAPI + server-rendered pages (Jinja/HTMX).

---

## 5. Docker — LOCKED (as recommended)

**Locked:** **Yes — Docker Compose** for local PostgreSQL + API + web.

**Why this lock:** One `compose up` is enough to review slices; Postgres version and ports stay consistent.

**Not chosen:** Install PostgreSQL only on the host and run API + web without Compose.

---

## 6. Profile input — LOCKED (amended)

**Locked:** **UI create/edit PLUS transcript import.** Students can build a profile in the app **and** import a transcript that maps course lines onto the ingested GVSU catalog. **Official SIS live-feed is later, if ever.** Prototype work is **not blocked on SIS.**

**Import format (from the local test print; diagrams in [architecture.md](architecture.md)):** unofficial **Banner Student Self-Service Academic Transcript (Advising)**. Parse **Student Information**, **Awarded** / **Sought**, **Institution Credit** (by `Period`), **Transcript Totals**, and **Course(s) in Progress** (by `Term`). Course join key is `Subject` + `Course` (prefix + 3-digit number). Keep letter **Grade** for the ≥ 2.0 rule. **Do not** commit names, IDs, GPAs, quality points, or the PDF itself.

**Amendment vs original recommendation:** transcript import is in the first profile path, not deferred. File import is a transcript (and the same structured profile fields), not “CSV later, maybe.”

**Why this lock:** The PDF says create or import and create/upload. UI + transcript import unblocks Milestone 4 without university-system access, and still matches “import.”

**Not chosen:** UI-only until much later. **Not chosen:** waiting on official SIS.

**Testing constraint:** a personal transcript may be used locally. **Never put real transcripts in git.**

---

## 7. “Potential workload” in course recommendations — LOCKED (as recommended)

**Locked:** **Catalog credit hours** from the GVSU course page (already on CIS listings, e.g. CIS 162 = 4 credits; graduate CIS courses are typically 3 credits). Recommendations may prefer a set of courses whose credits fit a **soft term cap of 15 credits**. That cap is a ranking preference, not a registration rule.

**Why this lock:** Credits are the only workload figure the public catalog actually publishes; the PDF does not define “potential workload.”

**Not chosen:** Display-only credits with no term-cap preference. A later swap could add a coarse “light / standard / heavy” tag if we encode labs — the catalog does not give a reliable hours field today.

---

## 8. Prototype login — LOCKED (amended)

**Wanted (not implementable in this prototype without university IT):** **GVSU student SSO.**

**Locked for now:** **local demo user + synthetic-profile switcher** (the eight synthetic profiles from item 3, including empty B.S. and M.S. profiles). Anyone running the app locally is that demo user.

**Design constraint (so SSO is not painted out):** keep **identity** separate from **student profile** data. The demo identity is a local stand-in; switching profiles does not become “log in as another password.” When GVSU IT can provide SSO, it should replace only the identity provider, not the profile/graph model.

**Do not:** implement a fake “GVSU password” collection page, a lookalike campus login, or any UI that asks students to type university credentials into this app.

**Why this lock:** Real campus SSO needs university IT. A demo user is enough to walk all nine capabilities. The PDF does not specify auth.

**Not chosen:** shipping campus SSO in the prototype. **Not chosen:** email/password accounts as the first auth. **Not chosen:** fake GVSU login.

---

## Locked picks (chat-ready)

1. **Scoring / gaps:** Evidence-count labels (Missing / Weak / Moderate / Strong) + explained match `100 × (0.50 S + 0.25 C + 0.15 P + 0.10 K)` — PDF percentages are not targets.  
2. **Graph storage:** PostgreSQL node + edge tables (SQL traversal; no Neo4j).  
3. **Datasets:** Free sources only — GVSU public CIS + **CS B.S. and Applied CS M.S.** catalog; O\*NET 31.0 (CC BY 4.0); frozen The Muse public jobs snapshot; synthetic CS B.S. **and** M.S. profiles. Optional personal transcript for local testing only; **never in git**. No paid APIs.  
4. **Web stack:** FastAPI + Next.js / TypeScript / Tailwind.  
5. **Docker:** Yes — Compose for Postgres + API + web.  
6. **Profile input:** UI create/edit **plus** Banner advising-transcript import (map `Subject`+`Course` to catalog). Official SIS live-feed later, if ever; not blocked on SIS. Never commit the PDF or PII.  
7. **Workload:** Catalog credit hours; soft 15-credit term cap as a ranking preference.  
8. **Login:** Want GVSU student SSO (needs university IT). **Now:** local demo user + synthetic-profile switcher; keep identity separate so SSO can slot in later. **No fake GVSU password collection.**

Python + PostgreSQL + Pandas/SQL stay as the proposal already stated.

---

## What this does not decide

Research evaluation design and accuracy metrics (Milestone 9). Multi-institution schema. Lakehouses / distributed processing. Real student data in the repo. Hosting beyond local Docker. Actual GVSU SSO integration (blocked on university IT). Transcript **parser implementation** (PDF library, OCR vs text) — the **section/field layout** to parse is the Banner advising print in [architecture.md](architecture.md); the lock is still the capability, not a vendor.

---

## Immediate next step

**Milestone 3** (diagrams that match these locks) is in [architecture.md](architecture.md): batch pipeline, entities + five graph relations, student path through the nine capabilities, synthetic B.S. / M.S. record shape.

**You (Bilal):** confirm the diagrams match the lock — not visual polish.

**Cursor:** no application code until that review. Another worker owns GitHub; do not push from this thread.
