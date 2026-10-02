# StudentOS

This folder is the copy you run on your PC. Put it at:

`C:\Users\Bilal Khan\Documents\Masters Project`

Then open **START-HERE.md**. You do not need to write code.

StudentOS is a student decision tool for Grand Valley Computer Science. It uses the public course catalog. Each signed-in GVSU Google account has its own academic profile. It is not Banner, not course registration, and not official Grand Valley software.

## Start the demo

1. Install **Docker Desktop** and leave it running.
2. Double-click **Start StudentOS** on the Desktop (or `Start StudentOS.bat` in this folder).
3. Open [http://127.0.0.1:43123](http://127.0.0.1:43123) if the browser does not open itself. Sign in with Google first (`@mail.gvsu.edu` or `@gvsu.edu`), then use the profile and catalog.

If you already started it once, opening Docker Desktop is enough — StudentOS comes back by itself. To shut it down, double-click **Stop StudentOS** (or `Stop StudentOS.bat`).

`docker-compose.yml` is in **this folder** (the same place as this README). Do not nest it inside `app/`.

## What works now

You can:

- Sign in with Google (GVSU student emails only)
- Open **your** academic profile (Google name, current degree, majors, Banner badge if you have one)
- Upload a Banner advising transcript and a resume (parsed into profile fields, then discarded)
- Manually pick Applied CS M.S. or CS B.S. when the degree line is missing
- See the Computer Science B.S. and Applied CS M.S. pathways, including graduate badges
- Take the Career survey for Match % rankings, skill-gap labels, and a complete path sketch (override allowed)
- Browse GVSU computing courses, including credits, descriptions, and prerequisites when the public catalog lists them

Transcript upload lists completed, in-progress, and still-needed catalog courses. Student ID and GPA are not saved. Your name is the Google sign-in name.

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

## This is not ready yet

Next-semester course packing (prereqs / credit cap), job-market ingest, and campus SSO.

## Privacy

Each signed-in GVSU Google account has its own profile (name and email from Google). Banner student ID and GPA are not saved. Never commit transcripts, resumes, or a filled-in `.env` that has secrets.
