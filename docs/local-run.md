# Run StudentOS on a Windows PC

You do not need to write code. You need **Docker Desktop** running, then **Start StudentOS**. You do not need to keep a PowerShell window open.

StudentOS is a local demo. Students sign in with Google. It is not campus SSO and not official university software.

The folder you run from is:

`C:\Users\Bilal Khan\Documents\Masters Project`

`docker-compose.yml` must be in **that folder** (the root), not inside an `app` subfolder.

## 1. Install Docker Desktop

1. On your Windows PC, open: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Download **Docker Desktop for Windows**.
3. Run the installer. Accept the default options (including the WSL 2 backend if Windows asks).
4. Restart the PC if the installer asks you to.
5. Open **Docker Desktop** from the Start menu.
6. Wait until the whale icon in the system tray is steady and Docker says it is running. This can take a minute.

If Windows asks you to install or update **WSL 2**, do that, then open Docker Desktop again.

**Docker Desktop must stay running** while you use StudentOS.

## 2. Put the project on your PC

Copy the **Masters-Project** folder so its contents live here:

`C:\Users\Bilal Khan\Documents\Masters Project`

When you are done, that folder should contain `docker-compose.yml`, `START-HERE.md`, `README.md`, `web`, `api`, `pipeline`, `data`, and `docs` at the top level — not buried under `app/`.

If GitHub later has the project at [https://github.com/bilalkhaniazi/StudentOS](https://github.com/bilalkhaniazi/StudentOS), you can also download the ZIP from the green **Code** button and unzip it to the same folder. Today, use the **Masters-Project** copy from this project.

## 3. Start StudentOS

1. Make sure Docker Desktop is running, or just use the shortcut below (it will start Docker if needed).
2. Double-click **Start StudentOS** on the Desktop.

That runs `Start StudentOS.bat` from this folder. It waits until Docker is ready, starts the app in the background (`docker compose up -d`), and opens the website. You can close that window afterward.

If you already started StudentOS once and did not click **Stop StudentOS**, you can just open **Docker Desktop**. The containers restart on their own. Then open the website.

The first run downloads images and builds the app. That can take several minutes.

If Windows asks to allow Docker or a network, allow it.

## 4. Open it in your browser

- StudentOS (the website): [http://127.0.0.1:43123](http://127.0.0.1:43123)
- A simple “is the server up?” page: [http://127.0.0.1:43124/health](http://127.0.0.1:43124/health)

Those addresses are on **your** PC (`127.0.0.1` means this computer). Use Microsoft Edge or Chrome.

The first screen is Google sign-in. Use a GVSU account (`@mail.gvsu.edu` or `@gvsu.edu`). After that you are on **your** profile (Google name, then degree/majors/badges from a Banner transcript). Choose **Data Engineer** under Career if you want a target, and browse **Courses**. On Profile you can upload a Banner advising transcript and a resume; StudentOS reads each file and does not keep it.

## 5. Stop it

Double-click **Stop StudentOS** on the Desktop, or `Stop StudentOS.bat` in this folder.

That runs `docker compose down`. The next time you want the site, use **Start StudentOS** again.

You can also quit Docker Desktop when you are finished. Start Docker Desktop again (or **Start StudentOS**) before the next session.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| `docker` is not recognized | Docker Desktop is not installed, or it is not running. Install or start it, wait for the whale icon, try **Start StudentOS** again. |
| Browser says the site refused to connect | Docker Desktop is not running, or the app was stopped. Open Docker Desktop, or double-click **Start StudentOS**. |
| Google button says it is not connected | Put `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`, then Stop and Start StudentOS. |
| Google rejects the email | Use `@mail.gvsu.edu` or `@gvsu.edu`. |
| You cannot find `docker-compose.yml` | You are not in `C:\Users\Bilal Khan\Documents\Masters Project`. Compose lives at that root, not inside `app/`. |
| Port already in use | Another program is using 43123 or 43124. Close it, or restart the PC, then start Docker Desktop and **Start StudentOS**. |
| Build looks stuck | The first run is slow. Wait. If it errors, copy the last red lines and keep them for later. |

Do not put real transcripts, student IDs, or GPAs into email, chat, or git. The demo profiles are invented.
