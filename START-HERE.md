# Start here (Windows)

This folder is StudentOS. Keep it at:

`C:\Users\Bilal Khan\Documents\Masters Project`

`docker-compose.yml` must sit in **that folder**, not inside an `app` subfolder.

StudentOS is a local demo. It is not Grand Valley login and not official university software.

You do **not** need to keep a PowerShell window open.

## 1. Install and open Docker Desktop

1. Download **Docker Desktop for Windows**: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Install it. Accept the defaults (including WSL 2 if Windows asks).
3. Restart the PC if the installer asks you to.
4. Open **Docker Desktop** from the Start menu or the Desktop shortcut.
5. Wait until the whale icon is steady and Docker says it is running.

**Leave Docker Desktop running** while you use StudentOS.

## 2. Start StudentOS

Double-click **Start StudentOS** on the Desktop.

That starts Docker Desktop if needed, starts the app in the background, and opens:

[http://127.0.0.1:43123](http://127.0.0.1:43123)

The first run can take several minutes. After that, you can close the Start StudentOS window.

If you already started StudentOS once and did not use **Stop StudentOS**, just open **Docker Desktop**. The site comes back by itself. Then open [http://127.0.0.1:43123](http://127.0.0.1:43123) in Edge or Chrome.

You can also double-click `Start StudentOS.bat` in this folder. It does the same thing.

## 3. Sign in, then use the site

The first screen is **student Google sign-in**. You cannot open the catalog until you sign in.

1. Open [http://127.0.0.1:43123](http://127.0.0.1:43123).
2. Choose **Continue with Google**.
3. Sign in with a GVSU Google account: **@mail.gvsu.edu** or **@gvsu.edu**.
4. After Google finishes, StudentOS opens **your** profile (your Google name) and the catalog.

On **Profile**, upload a Banner advising transcript PDF (the file is read and discarded). Degree, majors, and any post-baccalaureate badge come from that PDF. If the degree line is missing, pick Applied CS M.S. or CS B.S. by hand. Upload a resume there too — StudentOS extracts experience, projects, skills, education, and languages into editable sections (or enter them by hand), then discards the file. Open **Pathways** for the Computer Science B.S. and Applied CS M.S. required courses, electives, and graduate badges. On **Career**, take the short preference survey after a transcript is on file — you get Match % rankings, skill gaps, and a complete path sketch (you can override the suggested career). Browse **Courses**. Use **Sign out** when you are done.

A simple “is the server up?” page: [http://127.0.0.1:43124/health](http://127.0.0.1:43124/health)

### If the Google button says it is not connected

The login page still opens. Google sign-in needs two values on this PC:

1. Copy `.env.example` to a new file named `.env` in this folder (if you do not already have `.env`).
2. Paste your Google client ID and client secret into `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
3. In Google Cloud, set the authorized redirect URI to:

`http://127.0.0.1:43123/api/auth/callback/google`

4. Double-click **Stop StudentOS**, then **Start StudentOS**.

Do not put those secrets in email, chat, or git.

## 4. Stop it

Double-click **Stop StudentOS** on the Desktop, or `Stop StudentOS.bat` in this folder.

That runs `docker compose down` and shuts the app down. Open **Start StudentOS** the next time you want it.

You can also quit Docker Desktop when you are finished. Open Docker Desktop again (or **Start StudentOS**) before you use the site.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| `docker` is not recognized, or Start StudentOS says it cannot find Docker | Docker Desktop is not installed, or it is not running. Start it, wait for the whale icon, try **Start StudentOS** again. |
| Browser says the site refused to connect | Docker Desktop is closed, or the app was stopped. Open Docker Desktop, or double-click **Start StudentOS**. |
| Google button is visible but says it is not connected | Google client ID and secret are missing. Follow the Google steps in section 3. The login page is still the right page. |
| Google says the email is not allowed | Use **@mail.gvsu.edu** or **@gvsu.edu**. Other Gmail addresses are blocked on purpose. |
| You cannot find `docker-compose.yml` | You are in the wrong folder. The compose file must be in `C:\Users\Bilal Khan\Documents\Masters Project`, next to this file. |
| Port already in use | Something else is using 43123 or 43124. Close it, or restart the PC, then start Docker Desktop and **Start StudentOS**. |

More detail: [docs/local-run.md](docs/local-run.md).

Do not put real transcripts, student IDs, GPAs, or resumes into this folder, email, chat, or git. Upload a transcript or resume only on the Profile page; StudentOS does not save those files.
