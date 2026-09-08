# Install & Run — MarketingOps Agent

One folder, three platforms. The agent is the `marketing-agent/` folder. **Copy or clone that
folder onto each device**, then run the matching one-click launcher. No installers to download
beyond Python (and Termux on Android).

> LLM choice (do this once, on every device):
> - **Easiest, free, private:** local **Ollama** — install https://ollama.com, run `ollama pull llama3.1`.
>   The default `.env` already uses it.
> - **Best quality:** set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `.env` (run `python cli.py init`).

---

## 1) Windows  (one-click)

1. **Get the folder:** unzip `marketing-agent/` (or `git clone` it) to any place, e.g. `C:\marketing-agent`.
2. **Install Python 3.10+** (only if not present): https://www.python.org/downloads — tick
   **"Add python.exe to PATH"** during install.
3. **Double-click `start.bat`.** It will:
   - create an isolated environment,
   - install dependencies (one time),
   - create a default `.env`,
   - launch the web UI and open **http://localhost:8000** in your browser.
4. First time only, to use a paid LLM: open a terminal in the folder and run `python cli.py init`.
5. **Stop:** close the "MarketingOps Agent" window, or `taskkill /f /im python.exe`.

Your phone (same Wi-Fi): open `http://<your-PC-IP>:8000` (find the IP with `ipconfig`).

---

## 2) Android  (Termux, one-click)

Termux is a Linux terminal for Android — it hosts the whole agent and web UI on the phone.

1. Install **Termux** from F-Droid (https://f-droid.org/packages/com.termux/) — *not* the Play Store
   (the Play version is outdated).
2. In Termux, grant storage and install Python:
   ```bash
   termux-setup-storage
   pkg update && pkg upgrade -y
   pkg install -y python git
   ```
3. **Get the folder** onto the phone (pick one):
   - Clone: `git clone <your-repo-url> marketing-agent` (needs `pkg install git`), **or**
   - On your PC, zip `marketing-agent/`, copy it to the phone's storage, then in Termux:
     `cp -r /sdcard/Download/marketing-agent .` (Termux sees phone storage under `/sdcard`).
4. **Run the one-click launcher:**
   ```bash
   cd marketing-agent
   bash start.sh
   ```
   It installs deps, creates `.env`, and starts the UI at `http://localhost:8000`.
5. Open **http://localhost:8000** in the phone browser (Chrome/Fennec).
6. Termux can't run Ollama, so use a paid LLM: `python cli.py init` → choose `openai`/`anthropic`
   and paste your key. (Keys are stored only in the local `.env`.)
7. To keep it running in the background: `termux-wake-lock`, then launch with `nohup bash start.sh &`.

---

## 3) iOS  (a-Shell + a hosted/VPS option)

iOS cannot run a persistent local server easily, and the App Store restricts this. Two practical
paths:

### A) Use it from your iPhone via a host you already run (recommended)
The agent is just a web service — run it on your Windows PC, an Android phone (Termux), or a $5 VPS,
then **open the link in Safari** on the iPhone. Easiest: expose it with a free tunnel:
```bash
# on the machine running the agent:
cloudflared tunnel --url http://localhost:8000     # or: ngrok http 8000
```
Open the `https://….trycloudflare.com` link in Safari. Set `WEB_PASSWORD` in `.env` first so only
you can open it.

### B) Run the CLI on-device with a-Shell
1. Install **a-Shell** (App Store).
2. Copy the `marketing-agent/` folder into a-Shell (use the in-app Files/Shortcuts import, or
   `pythonista3`/Files app).
3. In a-Shell:
   ```bash
   cd marketing-agent
   pip install -r requirements.txt
   python cli.py init          # choose openai/anthropic, paste key
   python cli.py chat
   ```
   The **web UI won't run reliably on iOS**, so the iPhone is best used as a *client* to a hosted
   agent (path A). For a permanent always-on option, deploy the folder to a VPS (Railway / Render /
   Fly.io / DigitalOcean) — it's a standard FastAPI app; set the same `.env` vars.

---

## One-click scripts reference
| File | Platform | What it does |
|---|---|---|
| `start.bat` | Windows | Double-click → venv + deps + `.env` + launches web UI + opens browser |
| `start.sh`  | Linux / macOS / Termux | `bash start.sh` → same, headless-friendly |

Both are **idempotent**: running them again is fast (env and deps already exist).

## Access it from anywhere (public link, any device)

### A) Instant, no account — `tunnel.bat` (keep your PC on)
Double-click **`tunnel.bat`**. It starts the agent and prints a public `https://….trycloudflare.com`
link. Open that link on **any phone or computer with internet** — it just works.
- Before tunneling, set `WEB_PASSWORD` in `.env` so only you can open it.
- Keep the `tunnel.bat` window open while you want the link live.

### B) Permanent public URL (runs even when your PC is off) — 1-click deploy
Push the `marketing-agent/` folder to GitHub, then click-deploy:
- **Render:** import the repo; `render.yaml` is included. Set `ANTHROPIC_API_KEY` and
  `WEB_PASSWORD` when prompted. You get a permanent `https://….onrender.com` URL.
- **Railway:** `railway.json` is included; `railway deploy` → permanent URL.
- **Any Docker host:** `Dockerfile` is included → `docker build -t marketingops . && docker run -p 8000:8000 marketingops`.
In all cases set `ANTHROPIC_API_KEY` and `WEB_PASSWORD` as environment variables in the host
dashboard. The app reads them automatically.

> Either way, the agent is now a bookmark on your phone — open it anywhere, review drafts,
> approve, push to Buffer. You approve the final post/apply (ToS-safe).

## Security checklist before sharing the link
- Set `WEB_PASSWORD` in `.env` (the UI shows a login screen).
- Only expose via a tunnel/VPN you control, or behind Cloudflare Access.
- Your LLM API keys live only in the local `.env` — never commit it.

## What you get after launch
Open the UI → **Digest** tab is your command center: run a campaign, review drafts, push approved
social posts to Buffer, and get the daily brief by email/webhook. The agent writes, researches,
schedules-prep, and reminds; you approve the final post/apply — staying within Fiverr/Upwork/Buffer
Terms of Service.
