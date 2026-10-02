# StudentOS

This folder is the copy you run on your PC. Put it at:

`C:\Users\Bilal Khan\Documents\Masters Project`

Then open **START-HERE.md**. You do not need to write code.

StudentOS is a student decision tool for Grand Valley Computer Science. It uses the public course catalog and invented demo students. It is a local demo. It is not Banner, not course registration, and not official Grand Valley software. Students sign in with Google using a GVSU email.

## Start the demo

1. Install **Docker Desktop** and leave it running.
2. Double-click **Start StudentOS** on the Desktop (or `Start StudentOS.bat` in this folder).
3. Open [http://127.0.0.1:43123](http://127.0.0.1:43123) if the browser does not open itself. Sign in with Google first (`@mail.gvsu.edu` or `@gvsu.edu`), then use the profile and catalog.

If you already started it once, opening Docker Desktop is enough — StudentOS comes back by itself. To shut it down, double-click **Stop StudentOS** (or `Stop StudentOS.bat`).

`docker-compose.yml` is in **this folder** (the same place as this README). Do not nest it inside `app/`.

## What works now (Slice A)

You can:

- Sign in with Google (GVSU student emails only)
- Open an academic profile (degree, major, courses with letter grades, interests, skills)
- Switch among eight invented CS students (six B.S., two Applied CS M.S.)
- Pick a target career: Data Engineer, Cloud Engineer, Backend Engineer, or ML Engineer
- Browse GVSU CIS courses, including credits and prerequisites when the public catalog lists them

Transcript upload reads a Banner advising PDF in memory and discards it. Completed, in-progress, and still-needed catalog courses are listed on Profile. Name, student ID, and GPA are not saved.

## Folder layout

| Item | What it is |
| --- | --- |
| `START-HERE.md` | Windows steps: Docker Desktop, then double-click Start StudentOS |
| `docker-compose.yml` | Starts the database, API, and website together |
| `.env.example` | Sample settings (copy to `.env` only if you change them) |
| `web/` | The website |
| `api/` | The server |
| `pipeline/` | Catalog ingest and invented demo records |
| `data/` | Saved public-catalog snapshot and demo students |
| `docs/` | Supervisor-facing documents (architecture, decisions, build plan, proposal) |

## Documents

See [docs/README.md](docs/README.md) for the readable list. Short version:

- [Architecture](docs/architecture.md)
- [Decision memo](docs/decision-memo.md)
- [Build plan](docs/build-plan.md)
- [Project context](docs/project-context.md)
- [How to run locally](docs/local-run.md)
- [Master’s proposal (PDF)](docs/masters-proposal.pdf)

## This is not in Slice A yet

Skill-gap labels, Career Match Score, personalized recommendations, job-market ingest, and campus SSO.

## Privacy

Demo profiles are invented. They do not contain real names, IDs, or GPAs. Never commit transcripts or a filled-in `.env` that has secrets.
