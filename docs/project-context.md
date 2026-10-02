# Project briefing: StudentOS

This briefing is a faithful reading of the 7-page PDF *Master's Final Semester Project Proposal* at [`docs/masters-proposal.pdf`](masters-proposal.pdf). It covers what the document specifies and flags what it does not. Nothing below is invented to fill missing fields.

**Source file.** Google Docs–rendered PDF (`Producer: Skia/PDF m153 Google Docs Renderer`). PDF metadata title: `Master's Final Semester Project Proposal`. Seven pages. No Author, Creator, Subject, Keywords, or dates in the PDF metadata.

---

## 1. Title

**Document type (PDF title / heading):** Master's Final Semester Project Proposal

**Project title:** StudentOS: A Data-Driven Student Decision Intelligence Platform

The product name used throughout is **StudentOS**. The document also calls it:

- a “data-driven web application”
- a “student decision intelligence platform”
- a “unified data platform”
- a “web-based platform”
- a “unified data ecosystem”
- a “student decision support platform” (research question 1)
- a “decision-support system”
- both “a practical student-facing web application and a research-oriented Data Engineering project”

---

## 2. Authors, supervisors, institution

**Not stated in the PDF.**

| Field | In the PDF? |
| --- | --- |
| Student / author name | No |
| Student ID | No |
| Supervisor / advisor | No |
| Committee | No |
| Course / program name (beyond “Master's Final Semester Project Proposal”) | No |
| Department, college, or university letterhead | No, except the later scope phrase “GVSU’s CS department” |
| Date, semester, or year | No |
| Contact information | No |

**Context outside the PDF (not a PDF claim):** this Project is for Muhammad Bilal Ali Khan. That name does not appear in the proposal text or metadata.

**Institutional mention that *is* in the PDF:** Section 9 says the “initial implementation may focus on **GVSU’s CS department**,” and that the data architecture “can eventually support multiple institutions and different academic disciplines.” The PDF does not spell out “GVSU.”

---

## 3. Problem

Students must make many academic and career decisions during a degree, including:

- selecting courses
- planning semesters
- identifying suitable career paths
- developing relevant skills
- choosing projects
- preparing for employment

The information needed for those decisions is “scattered across university course catalogs, degree requirements, student reviews, job postings, career websites and other disconnected sources.”

Three concrete challenges (Section 2):

1. **Courses are presented independently.** A catalog may describe content and prerequisites, but “does not necessarily explain how that course contributes to a student's long-term career objectives.”
2. **Limited visibility** into relationships among courses, skills, projects, and employment opportunities. Example: a student aiming to become a Data Engineer “may know that they should learn SQL or Python, but may not know which courses, projects or technologies would best prepare them for that career.”
3. **Job-description skill demand is rarely connected to curriculum.** Students “may graduate with a degree but discover that their skill profile does not fully align with the current job market.”

Intended remedy: a “unified data ecosystem connecting:”

> Students -> Courses -> Skills -> Projects -> Technologies -> Careers -> Job Opportunities

The system will turn “disconnected sources into actionable recommendations and visual insights.”

---

## 4. Motivation

Existing tools are split in a way that forces students to do the joining work themselves:

- “Most existing student platforms focus primarily on **administrative functions** such as course registration, grades, attendance or access to learning materials.”
- “Career platforms on the other hand, generally focus on **job searching** and do not consider a student's academic history and completed coursework in sufficient depth.”
- Result: students “manually connect their academic experiences with their future career goals.”

The primary framing question StudentOS tries to answer (Section 9), quoted:

> “Given what I have studied, what I know, what I want to become and what employers currently require, what should I do next?”

versus the narrower question “What course should I take?”

The research motivation (Section 7) is whether “integrating academic data with real-world employment data can produce more useful student recommendations than traditional course-planning systems.”

---

## 5. Goals and objectives

**Primary objective (Section 1), quoted:**

> “The primary objective is not to replace university systems but to create an intelligent layer on top of existing information that helps students understand what they have already achieved, what they are missing and what they should do next.”

**Solution-level goal (Section 3):** “evidence-based recommendations rather than generic career advice.”

**Data-engineering objective (Section 5):** StudentOS must not be “simply a conventional web application with a recommendation algorithm.” The “core of the project will be a data engineering architecture capable of collecting, processing, integrating and analyzing heterogeneous datasets.”

**Research objective (Section 7):** investigate whether academic + employment data integration yields more useful recommendations than traditional course-planning systems.

**Four potential research questions:**

1. How can heterogeneous academic and employment datasets be integrated into a unified student decision support platform?
2. Can a knowledge graph effectively represent relationships between university courses, technical skills, projects and career opportunities?
3. Can student-specific skill-gap analysis provide more relevant course and career recommendations than generic recommendations?
4. How accurately can the system identify the skills required for a student's selected career based on current job-market data?

**Expected outcome (Section 8):** a “functional web application” / “completed prototype” through which students understand “academic and professional development through a single platform.”

**Conclusion-level aim:** “improving academic and career decision-making for university students” via “personalized insights into their academic and professional development.”

---

## 6. Scope and non-goals

### In scope (as specified)

- A **web-based** student-facing platform.
- Student **academic profiles** (create, upload, and/or import — wording varies; see gaps).
- A **structured knowledge base**: course information, prerequisite relationships, skills associated with courses, current job-market requirements.
- **Course intelligence**: relationships among courses, prerequisites, topics, and skills; exploration of how courses contribute to desired career paths.
- **Career and skill analysis** from job-market data, including proficiency-style gap labels.
- **Course recommendation** using completed coursework, prerequisites, career objectives, existing skills, skill gaps, and potential workload.
- **Career Match Score**: “approximate compatibility” with career paths, with an explanation of contributing factors.
- **Batch-oriented data pipeline** over heterogeneous sources.
- A **student academic and career knowledge graph** used to traverse relationships and answer questions such as: “I want to become a Data Engineer. Which courses should I take to close my current skill gaps?”
- Prototype capabilities listed in Section 8 (see Deliverables).
- Combined technical surface: “Web Development, Data Engineering, Data Analytics, Knowledge Graphs and Recommendation Systems.”
- **Initial academic focus (tentative):** “GVSU’s CS department.”
- **Extensibility (eventual, not claimed as the first slice):** “multiple institutions and different academic disciplines.”

### Non-goals / explicit boundaries

- **Not a replacement for university systems** — an “intelligent layer on top of existing information.”
- **Not generic career advice** — recommendations must be “evidence-based.”
- **Not “simply a conventional web application with a recommendation algorithm”** — data engineering is the core.
- **Not an unexplained black-box score** — Career Match Score “will be accompanied by an explanation of the factors contributing to it rather than being presented as an unexplained prediction.”
- **Not (initially) a multi-institution / multi-discipline product** — that is described as eventual extensibility. The first implementation “may focus on GVSU’s CS department.”
- Course recommendation is meant to be “more personalized than simply displaying a university course catalog.”

### Not scoped in the PDF (do not assume)

The PDF does not say the system will: register students for courses, store official grades as a system of record, scrape private student data, automate job applications, provide counseling/advising certification, support mobile-native apps, run real-time streaming pipelines (architecture is batch-oriented), or serve non-student users (advisors, faculty, employers) as first-class roles.

---

## 7. Proposed solution (how it is supposed to work)

Students “create or import an academic profile” with degree, completed courses, grades, technical skills, projects, interests, and career objectives.

The system “analyze[s] this information against a structured knowledge base containing course information, prerequisite relationships, skills associated with courses and current job-market requirements.”

**Worked example (Data Engineering):** a student who has completed courses in databases, cloud computing, and machine learning. StudentOS “could identify that the student already possesses strong SQL and cloud-related knowledge but has limited exposure to technologies such as Apache Kafka, Apache Airflow or Terraform.”

The platform “could subsequently recommend”:

- Courses that address the student's skill gaps
- Projects that would strengthen the student's portfolio
- Technologies that should be learned
- Career paths that match the student's existing profile
- Job categories for which the student is currently qualified
- Skills that would increase their employability

---

## 8. Key features (as specified)

### 8.1 Student Academic Profile

Students “create/upload a profile containing”:

- Degree and major
- Completed and planned courses
- Academic performance
- Technical skills
- Projects
- Certifications
- Career interests
- Target career

The system converts this into a “structured student profile.”

### 8.2 Course Intelligence

The platform maintains relationships among “courses, prerequisites, topics and skills.”

Example chain (quoted as given):

> Data Engineering -> Distributed Systems -> Cloud Computing -> Data Engineer

Students “explore how individual courses contribute to their desired career paths.”

### 8.3 Career and Skill Analysis

Analyzes “job-market data to identify the skills commonly requested for different positions.”

Illustrative analysis for **Target Career: Data Engineer**:

| Skill | Stated level |
| --- | --- |
| SQL | Strong |
| Python | Strong |
| Cloud Computing | Strong |
| Apache Spark | Moderate |
| Redis | Weak |
| Airflow | Weak |
| Snowflake | Missing |

Then: “recommend learning activities based on these gaps.”

The PDF does not define how Strong / Moderate / Weak / Missing are computed.

### 8.4 Course Recommendation

Recommendations based on:

- Completed coursework
- Prerequisites
- Career objectives
- Existing skills
- Skill gaps
- Potential workload

### 8.5 Career Match Score

“Approximate compatibility with different career paths based on their skills, coursework, projects and job-market requirements.”

Illustrative table:

| Career | Estimated Match |
| --- | --- |
| Data Engineer | 87% |
| Cloud Engineer | 76% |
| Backend Engineer | 71% |
| ML Engineer | 64% |

Must include “an explanation of the factors contributing to it.”

The PDF does not define the scoring formula, weights, or calibration of these percentages. They are an example.

---

## 9. Methodology

The document does not use a formal methods section (no Gantt, no evaluation protocol, no user-study design). Methodology is implied by Sections 5–8:

1. **Collect** heterogeneous academic and employment data (APIs, CSV files, publicly available datasets).
2. **Clean, validate, normalize, and de-duplicate**; combine sources; transform raw data into structured datasets.
3. **Store** in PostgreSQL; create relationships among courses, skills, projects, and careers.
4. **Model** those relationships in a knowledge graph and traverse them for questions such as skill-gap course selection.
5. **Generate** data required by a recommendation engine.
6. **Serve** personalized insights through a web application.
7. **Update** datasets “when new information becomes available” (refresh is stated; cadence is not).
8. **Investigate** the four research questions, including whether skill-gap analysis beats generic recommendations and how accurately job-market skills can be identified.

User-facing method: profile in → knowledge-base / graph analysis → recommendations, scores, and visualizations out.

Testing data explicitly mentioned: “Synthetic academic records for testing.” No other evaluation method is specified.

---

## 10. Architecture

**Proposed architecture:** “a simple **batch-oriented data pipeline**”:

> Data Sources -> Python Data Ingestion -> Data Cleaning & Transformation -> PostgreSQL Database -> Recommendation Engine -> Web Application

Pipeline responsibilities:

- Data collection from APIs, CSV files and publicly available datasets
- Data cleaning and validation
- Schema normalization
- Duplicate detection
- Combining information from different sources
- Transforming raw data into structured datasets
- Updating datasets when new information becomes available
- Creating relationships between courses, skills, projects, and careers
- Generating data required by the recommendation system

**Knowledge graph (Section 6)** is called “one of the distinctive components.” Example relations:

- Course -> teaches -> Skill
- Skill -> required by -> Job
- Course -> prerequisite of -> Course
- Project -> demonstrates -> Skill
- Student → completed → Course

The graph is how the system answers more complex questions by traversing “the student's existing skills, university courses and job requirements.”

**Storage note:** the pipeline diagram ends at PostgreSQL. The PDF does not say whether the knowledge graph is implemented *inside* PostgreSQL (tables/edges), as a separate graph store, or both.

---

## 11. Tech stack

**Stated as the primary implementation stack:**

- Python
- PostgreSQL
- “a web development framework” (unnamed)
- Pandas
- SQL
- Docker — **optional**, “to simplify deployment and development”

**Named in the pipeline, not as products:** Python Data Ingestion; Data Cleaning & Transformation; Recommendation Engine; Web Application.

**Not named:** specific web framework (React, Next.js, Django, Flask, etc.), graph database, orchestrator, cloud provider, job-board API, auth, hosting, or CI.

**Conclusion (Section 10) lists Data Engineering concepts the project “provides substantial opportunities to investigate”:**

- data pipelines
- distributed processing
- data lakehouses
- data integration
- knowledge graphs
- data quality
- recommendation systems

**Tension (do not collapse these):** the proposed architecture is a *simple batch-oriented* pipeline into PostgreSQL. “Distributed processing” and “data lakehouses” appear only in the conclusion’s concept list, not in the architecture diagram or primary stack. Treat them as research/investigation interests unless a later document commits to them.

---

## 12. Datasets and data sources

Section 5 lists **potential** data sources (not a committed catalog of named datasets):

- University course catalogs
- Degree requirements
- Course prerequisites
- Public job postings
- Technology/skill taxonomies
- Student-generated course feedback
- Public career information
- Synthetic academic records for testing

Ingestion modes mentioned: “APIs, CSV files and publicly available datasets.”

No specific catalog URL, job board, taxonomy (e.g. O\*NET, ESCO), API vendor, license, volume, or refresh schedule is given.

Student profile fields that become data (create/import/upload): degree, major, completed and planned courses, grades / academic performance, technical skills, projects, certifications, interests, career objectives / target career.

---

## 13. Deliverables

The PDF’s completion bar is a **functional web application** / **completed prototype** that lets a student:

1. Build an academic profile
2. Select a target career
3. Analyze their existing skills
4. Identify skill gaps
5. Explore relevant university courses
6. Receive personalized recommendations
7. Explore projects and technologies relevant to their career
8. Understand how their coursework connects to employment opportunities
9. Visualize their academic and career progression

The “final product will be both a practical student-facing web application and a research-oriented Data Engineering project.”

The document does **not** list: a written thesis/report, presentation, dataset package, API spec, deployment target, user-study write-up, or source-code repository as separate deliverables — only the prototype/system and the research investigation implied by Section 7.

---

## 14. Timeline and milestones

**Not specified.** No dates, semester calendar, weekly plan, or phased milestones.

The only temporal language is:

- “initial implementation may focus on GVSU’s CS department”
- architecture “can eventually support multiple institutions and different academic disciplines”
- datasets should be updated “when new information becomes available”

---

## 15. Evaluation and success criteria

**No dedicated evaluation section, metrics, thresholds, or user-study protocol.**

What can be treated as success *signals* because the PDF states them:

| Signal | Source | Hardness |
| --- | --- | --- |
| Prototype supports the nine student actions | Section 8 | Stated completion criterion (“should allow”) |
| Recommendations are evidence-based, not generic | Section 3 | Qualitative |
| Career Match Score is explained, not an “unexplained prediction” | Section 4.5 | Qualitative |
| System is not “simply a conventional web application with a recommendation algorithm”; data engineering architecture is the core | Section 5 | Qualitative / architectural |
| Knowledge graph can be traversed for skill-gap course questions | Section 6 | Qualitative / example question |
| Research questions 1–4, especially accuracy of job-market skill identification and relevance vs generic recommendations | Section 7 | Questions only; no accuracy target, baseline, or dataset for measuring them |
| Example match percentages (87%, 76%, 71%, 64%) | Section 4.5 | **Illustrative only**, not targets |

Research question 4 asks “How accurately…?” but does not define a metric (precision/recall, expert agreement, etc.).

---

## 16. Risks, constraints, and other requirements

**No risks, constraints, ethics, privacy, IRB, budget, or limitations section.**

Constraints that *can* be read from wording without adding new ones:

- **Optional Docker** — deployment tooling is not required by the proposal.
- **Web framework unnamed** — only that one will be used.
- **Batch-oriented** pipeline — not specified as streaming or real-time.
- **Public / synthetic data orientation** for several sources (public job postings, public career information, synthetic academic records). Student-generated course feedback is listed but collection/consent is unspecified.
- **Approximate** Career Match Score — the document itself frames compatibility as approximate.
- **Initial CS-department focus** is tentative (“may focus”).
- Profile creation is described as create **or** import (Section 3) and create/upload (Section 4.1) — both appear; official SIS integration is not specified.

---

## 17. Other requirements and distinctive claims

**Running example domain.** Data Engineer / Data Engineering is the recurring illustration (courses, skills, technologies, match scores, knowledge-graph question). Other example careers in the match table: Cloud Engineer, Backend Engineer, ML Engineer. Example technologies: SQL, Python, Apache Kafka, Apache Airflow, Terraform, Apache Spark, Redis, Snowflake, cloud computing.

**Innovation claim (Section 9):** connecting information “normally separated across different systems,” and answering the fuller “what should I do next?” question.

**Extensibility claim:** underlying data architecture should be able to support more institutions and disciplines later.

**Sentence fragment in Section 1 (quote faithfully):** “This project StudentOS, a data-driven web application designed to act as a student decision intelligence platform.” A verb such as “proposes” or “is” is missing in the source.

**Bookmark oddity (not a project requirement):** PDF outline jumps from “8. Expected Outcome” to “10. Conclusion”; Section 9 exists in the body as “Significance and Innovation.”

---

## 18. Gaps and ambiguities (do not fill these in implementation guesses)

1. **People and program:** no author, supervisor, program, course code, or submission date in the PDF.
2. **GVSU:** acronym used once; full official name, campus, and degree program are not written.
3. **Web framework and frontend/backend split:** unspecified.
4. **Knowledge-graph implementation:** relations are specified; storage engine is not (PostgreSQL vs dedicated graph DB).
5. **Distributed processing / data lakehouses:** listed as investigation concepts in the conclusion, not in the architecture or primary stack.
6. **Named datasets, APIs, licenses, volumes, and refresh cadence:** unspecified.
7. **How profiles are obtained:** “create or import” vs “create/upload”; no SIS/API import design.
8. **Scoring and gap labels:** Strong/Moderate/Weak/Missing and match percentages are examples without formulas.
9. **“Potential workload”** as a course-recommendation input: undefined (credits, hours, difficulty?).
10. **Course Intelligence example chain** `Data Engineering -> Distributed Systems -> Cloud Computing -> Data Engineer` mixes what look like a track/area, courses/topics, and a job title; the PDF does not label each node type.
11. **Student-generated course feedback:** listed as a source; no collection, privacy, or moderation rules.
12. **Recommendation algorithm:** existence of a “Recommendation Engine” is specified; model type (rules, graph traversal, ML, hybrid) is not, except that graph traversal is described for the Data Engineer skill-gap question.
13. **Users other than students:** not specified.
14. **Timeline, milestones, budget, ethics/privacy, and formal evaluation:** absent.
15. **Academic deliverable beyond the prototype** (thesis, paper, defense): not listed.
16. **Auth, multi-user accounts, and deployment environment:** not specified.
17. **Official vs synthetic student records:** synthetic records are for testing; whether real GVSU student data will be used is not stated.

---

## 19. One-paragraph summary (only PDF content)

StudentOS is a proposed master’s final-semester project: a data-driven web application that acts as a student decision intelligence platform. It would sit as an intelligent layer on top of existing university information (not a replacement for university systems), unify academic, course, skill, and career-market data, and give students evidence-based recommendations and visual insights—what they have achieved, what they are missing, and what to do next. The core is a batch data-engineering pipeline (Python ingestion and cleaning, PostgreSQL, recommendation engine, web app; optional Docker; Pandas/SQL) plus a knowledge graph of courses, skills, projects, jobs, and students. Features include academic profiles, course intelligence, job-market skill-gap analysis, course recommendations, and an explained Career Match Score. A completed prototype should let a student build a profile, pick a target career, analyze skills and gaps, explore courses/projects/technologies, get personalized recommendations, see how coursework maps to jobs, and visualize progression. Research would ask whether academic–employment integration, knowledge graphs, and skill-gap analysis outperform traditional/generic course planning, and how accurately job-market skills can be identified. Initial implementation may focus on GVSU’s CS department, with later extensibility to other institutions and disciplines.
