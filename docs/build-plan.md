# StudentOS build plan

**Project:** StudentOS — a data-driven student decision intelligence platform  
**For:** Muhammad Bilal Ali Khan (reviews and decides)  
**Built by:** Cursor (implements)  
**Sources:** [project briefing](project-context.md) and the [Master's Final Semester Project Proposal](masters-proposal.pdf)

This file is the overview and milestone plan. It is the first artifact. Diagrams, code, and research evaluation come later, in that order.

---

## How we work

| Role | Does | Does not |
| --- | --- | --- |
| **Bilal** | Reviews, asks questions, picks among options, says “yes / change this / not yet” | Write code, configure tools, or chase university system access before the prototype needs it |
| **Cursor** | Implements, proposes defaults, flags gaps, ships something reviewable at each milestone | Invent missing formulas, datasets, or architecture choices as if they were already decided |

You do not need to code. At the end of each milestone you get something concrete to look at (this plan, a short decision list, diagrams, or a running slice of the app). Reply with decisions and we continue.

---

## Recommended order (do this, not the reverse)

1. **Overview + milestones** — this file. Agree what “done” means and what ships in what order.
2. **Lock a few technical decisions** — short written choices only. No diagrams that guess, no code that paints us into a corner.
3. **Diagrams that match those decisions** — pipeline, data model, graph relations, student screens.
4. **Thin vertical slices** — small end-to-end pieces of the prototype, using public and synthetic data.
5. **Research evaluation last** — the four research questions, after there is a system that can actually recommend something.

**Why this order.** Milestones first so we do not build the wrong thing. Decisions before diagrams so the pictures match the stack. Diagrams before code so the first slice is not a rewrite. Research last because questions like “is skill-gap analysis more relevant than generic recommendations?” need a working recommender to compare.

We will **not** start with a diagram pack, a full architecture rewrite, GVSU SIS access, or a research protocol.

---

## What “done” means

The proposal’s completion bar is a **functional prototype**, not a university-system replacement. A completed prototype should let a student:

| # | Capability | Student can… |
| --- | --- | --- |
| 1 | Academic profile | Build a structured profile (degree/major, courses, performance, skills, projects, certifications, interests, target career) |
| 2 | Target career | Select a target career |
| 3 | Existing skills | See an analysis of skills they already have |
| 4 | Skill gaps | See gaps vs job-market requirements (the proposal’s Strong / Moderate / Weak / Missing *style* of labels) |
| 5 | Course exploration | Explore relevant university courses and how they relate (prerequisites, topics, skills, career contribution) |
| 6 | Personalized recommendations | Get recommendations that use completed coursework, prerequisites, career objectives, skills, gaps, and workload — not a raw catalog dump |
| 7 | Projects and technologies | Explore projects and technologies relevant to the chosen career |
| 8 | Coursework → employment | See how completed coursework connects to employment opportunities |
| 9 | Progression visualization | Visualize academic and career progression |

**Prototype “done”** = all nine are usable in the web app on **GVSU CS** data (public catalog-style data + synthetic student records), with evidence-based outputs (explained scores, not a black box) and a **batch data pipeline** behind them (Python ingestion → clean/transform → PostgreSQL → recommendation engine → web app).

**Not “done” (and not claimed by the proposal):** replacing Banner/SIS, registering for courses, multi-institution product, advisor/employer portals, real-time streaming, or a written thesis as a separate deliverable. The PDF does not list thesis/report/defense requirements; this plan does not add them.

Qualitative bars the prototype must still meet (from the proposal):

- Intelligent **layer on top of** existing information — not a replacement for university systems.
- Recommendations are **evidence-based**, not generic career advice.
- Career Match Score is **approximate** and **explained**.
- Core is a **data-engineering architecture**, not “a website with a scoring function bolted on.”
- Knowledge graph can be **traversed** for questions such as: *I want to become a Data Engineer. Which courses should I take to close my current skill gaps?*

---

## Scope for the first implementation

**In**

- Student-facing web app
- GVSU CS as the initial academic focus (as the proposal’s tentative first slice)
- Batch pipeline over heterogeneous sources
- Knowledge graph of the relations the proposal names (course–skill, skill–job, course–prerequisite, project–skill, student–course)
- Running example careers from the proposal: Data Engineer, Cloud Engineer, Backend Engineer, ML Engineer

**Out until later (eventual extensibility, not the first slices)**

- Other institutions and non-CS disciplines
- Official GVSU SIS / grade-system integration
- Student-generated course-feedback collection (listed as a *potential* source; no collection/privacy design in the PDF)
- Streaming / real-time pipelines
- Distributed processing and data lakehouses (named only as investigation concepts in the conclusion, not in the architecture)
- Extra user roles (advisors, faculty, employers)
- Mobile-native apps, job-application automation, counseling certification

**Data stance (so we are not blocked):** start with **public and synthetic** data. No GVSU SIS access is required to build or demo the prototype. Public CS course-catalog information, public job postings / career information, public skill taxonomies, and **synthetic academic records** are enough for slices 1–9. Named dataset picks are a Milestone 2 decision, not something this plan invents.

---

## Proposed technical defaults (not locked)

Consistent with the proposal: **Python**, **PostgreSQL**, **Pandas/SQL**, a **web framework** (unnamed in the PDF), **optional Docker**.

| Area | Proposed default | Status |
| --- | --- | --- |
| Pipeline & analytics | Python + Pandas + SQL | Matches PDF — keep |
| Database | PostgreSQL | Matches PDF — keep |
| Web stack | **FastAPI** (Python API next to the pipeline) + **Next.js / TypeScript / Tailwind** (student UI) | **Proposed, not locked.** The PDF only says “a web development framework.” This split lets the data work stay in Python and the nine student screens stay in a normal web app. Alternatives if you prefer one language: Django, or FastAPI + server-rendered pages. |
| Containers | Docker Compose for Postgres + app, used if it reduces setup friction | **Optional** in the PDF — decide in Milestone 2 |
| Knowledge graph storage | *Unspecified in the PDF* | **Do not invent here.** Lock in Milestone 2 (PostgreSQL tables/edges vs a separate graph store vs both) |
| Scoring / gap labels | *Examples only in the PDF* (87% match, Strong/Weak/Missing) | **Do not invent here.** Lock a simple, explainable rule in Milestone 2 |
| Named datasets | *Potential source types only* | **Do not invent here.** Lock a short public/synthetic list in Milestone 2 |
| Recommendation method | Graph traversal + explicit rules is the only method the PDF describes | Treat as the starting point unless Milestone 2 picks otherwise. No ML requirement in the PDF |
| Auth / hosting | Unspecified | Prototype can run locally with a **demo student** until you decide accounts are needed |

Nothing in this table is a locked decision except “keep Python + PostgreSQL + Pandas/SQL,” which the proposal already states.

---

## Milestone 2 — decisions to lock (gaps, not inventions)

These are open in the briefing. We write options, you pick. We do **not** fill them in while coding.

1. **Career Match Score and gap labels** — formula, weights, and how Strong / Moderate / Weak / Missing are computed. The PDF’s percentages are illustrations, not targets.
2. **Knowledge-graph storage** — inside PostgreSQL, a dedicated graph database, or both. The pipeline diagram ends at PostgreSQL; relations are specified, the engine is not.
3. **Named datasets** — which public CS catalog source, which public job/career source, which skill taxonomy, and that synthetic student records are the student-data source for testing. Licenses must be usable. Refresh cadence can stay “batch, when we rerun the pipeline.”
4. **Web stack** — accept the FastAPI + Next.js default, or pick Django / FastAPI-only.
5. **Docker** — yes for local Postgres+app, or install Postgres some other way.
6. **Profile input** — create in the UI first; optional file upload later. Official import from SIS is out of scope until you say otherwise.
7. **“Potential workload”** in course recommendations — what it means (credits, listed hours, or a simple proxy). Undefined in the PDF.
8. **Prototype login** — demo user only vs accounts. Unspecified in the PDF.

Out of Milestone 2 on purpose: research metrics, multi-institution schema, lakehouses, real student data.

**You review:** a one-page decision list with a recommended pick per item.  
**You do not review yet:** diagrams or a running app.

---

## Milestones

Each row: what ships, what you review, what we explicitly skip.

### Milestone 1 — Overview and milestones *(this file)*

| | |
| --- | --- |
| **Ships** | This plan: done-definition, order of work, proposed defaults, slice sequence |
| **You review** | Is this the right order? Any capability or non-goal you want changed before we lock tech? |
| **Not yet** | Decision memo, diagrams, code, SIS access, research protocol |

**Exit:** you say this plan is the working sequence (with any edits).

### Milestone 2 — Lock a few technical decisions

| | |
| --- | --- |
| **Ships** | Short decision memo: the eight items above, each with a recommended pick and a one-line rationale |
| **You review** | Accept / swap each pick. Especially scoring, graph storage, datasets, web stack |
| **Not yet** | Diagrams that assume unchosen storage or scores; dataset downloads at scale; UI chrome |

**Exit:** written lock on stack + graph storage + scoring approach + initial dataset list.

### Milestone 3 — Diagrams that match the locks

| | |
| --- | --- |
| **Ships** | Four pictures only: (1) batch pipeline as in the PDF, with our locked tools named; (2) entities and the five graph relations from the proposal; (3) student path through the nine capabilities; (4) what a synthetic CS student record contains |
| **You review** | “Does this match what we locked?” — not visual polish |
| **Not yet** | Code, extra diagram types, multi-institution drawings |

**Exit:** diagrams you would be willing to show a supervisor as the intended shape.

### Milestone 4 — Slice A: profile + catalog (capabilities 1, 2, 5-partial)

| | |
| --- | --- |
| **Ships** | Batch ingest of a **public GVSU CS–style course catalog** (and prerequisites if present) into PostgreSQL; **synthetic** student records; web UI to create/edit a demo profile, pick a target career, browse courses |
| **You review** | Can a demo CS student enter a profile, pick “Data Engineer,” and see real-looking courses? |
| **Not yet** | Skill gaps, match %, recommendations, job data, visualizations 8–9 |

**Exit:** first running vertical slice. Data is public/synthetic only.

### Milestone 5 — Slice B: graph + course intelligence (capability 5)

| | |
| --- | --- |
| **Ships** | Locked graph storage populated with course–prerequisite–skill–career links; UI to explore how a course contributes to a path (the proposal’s Course Intelligence idea) |
| **You review** | Can you walk from a course to skills to a career without a spreadsheet? |
| **Not yet** | Job-market skill extraction quality study; match scores |

**Exit:** the graph is queryable for the Data Engineer example question *structure* (even if recommendations are still naive).

### Milestone 6 — Slice C: skills, gaps, jobs (capabilities 3, 4, 7, 8-partial)

| | |
| --- | --- |
| **Ships** | Batch ingest of the **locked public job/career + taxonomy** sources; skill analysis and gap labels using the **locked** formula; projects/technologies tied to the target career; a first “this course ↔ this job skill” view |
| **You review** | For the synthetic Data Engineer student, do Strong/Weak/Missing (or whatever we locked) and the job links look explainable? |
| **Not yet** | Ranked course recommendations; match % across many careers; research accuracy study |

**Exit:** gap analysis is visible and traceable to sources.

### Milestone 7 — Slice D: recommendations + match score (capabilities 6, 8, score)

| | |
| --- | --- |
| **Ships** | Recommendation engine on pipeline output: courses (including prerequisite and workload inputs as locked), plus projects/technologies/skills to learn; Career Match Score **with factor explanation** for the example careers |
| **You review** | Compared with a plain catalog, is this personalized? Can you see *why* a score is not 100%? |
| **Not yet** | User study, accuracy metrics, extra careers beyond the first set |

**Exit:** capabilities 1–8 work on synthetic CS students.

### Milestone 8 — Slice E: progression visualization (capability 9) + prototype polish

| | |
| --- | --- |
| **Ships** | Visualization of academic and career progression; empty/error states; enough UI consistency to demo the nine capabilities in one sitting |
| **You review** | Walk the nine-item list as a student. Anything missing or confusing? |
| **Not yet** | Research write-up; production hosting; real student data |

**Exit:** prototype meets the Section 8 “should allow” list.

### Milestone 9 — Research evaluation (last)

| | |
| --- | --- |
| **Ships** | Evaluation of the four proposal questions **against the working system**: (1) how we integrated sources; (2) whether the graph representation is usable for the skill-gap course question; (3) skill-gap recommendations vs a generic baseline (e.g. catalog / popularity); (4) accuracy of extracted job-market skills on a **labeled public sample** — metric chosen here, not invented earlier. Synthetic students + public jobs remain the default data. |
| **You review** | Are the comparisons understandable? What would you show a supervisor? |
| **Not yet** | Unless you add them later: IRB, live student study, lakehouses, distributed processing |

**Exit:** research questions have an evidence trail. The PDF gives no accuracy target; we will not pretend 87% is a goal.

---

## Slice map (nine capabilities → when they first appear)

| Capability | First appears | Solid at |
| --- | --- | --- |
| 1 Profile | M4 | M4 |
| 2 Target career | M4 | M4 |
| 5 Explore courses | M4 (browse) | M5 (intelligence) |
| 3 Analyze existing skills | M6 | M6 |
| 4 Identify skill gaps | M6 | M6 |
| 7 Projects & technologies | M6 | M7 |
| 8 Coursework → jobs | M6 (partial) | M7 |
| 6 Personalized recommendations | M7 | M7 |
| Career Match Score (explained) | M7 | M7 |
| 9 Progression visualization | M8 | M8 |
| Research questions 1–4 | M9 | M9 |

---

## What we will not do yet (even if it comes up)

- Wait on GVSU SIS, official transcripts, or private student records
- Draw architecture diagrams before Milestone 2 locks
- Implement a scoring formula or graph database “for now” that we have not locked
- Build multi-institution or non-CS coverage
- Stand up distributed processing or a lakehouse because they appear in the conclusion’s concept list
- Collect live student course reviews
- Add thesis/report/presentation work the PDF did not list
- Optimize hosting, CI, or auth beyond what a local demo needs

---

## Immediate next step

**You (Bilal):** read this plan. Say whether the order and the nine-capability “done” list are correct. If yes, we go to **Milestone 2** (decision memo only).

**Cursor:** wait for that confirmation; then write the Milestone 2 decision list with recommended picks — still no code, still no diagrams.
