# MarketingOps Agent

A professional, **assisted** AI agent for marketing operations. It helps you run
Fiverr, Upwork, and other marketing activities **safely and within platform rules**:
it *drafts, plans, researches, and analyzes* — you review and post/apply with one click.
It does **not** log into platforms as a bot (that violates Fiverr/Upwork ToS and risks bans).

Built in Python. Runs on desktop, laptop, a server, and your phone (via the built-in
mobile web UI).

## What it does
- **Proposals** — Fiverr gig copy + packages, Upwork cover letters, bid strategy.
- **Content & Social** — platform posts, content calendars, repurposing, ad copy.
- **Market Research** — competitor briefs, keyword gaps, pricing analysis, trend scans.
- **Analytics** — performance reports, KPI templates, funnel diagnosis.

## New: drafts, live web research, profiles, auth

### Live web research (no API key)
The agent can fetch **real, current** data:
- `web research <topic>` / `live trend scan <topic>` — searches the web and synthesizes a brief.
- `live competitor <name>` — looks up a competitor via live search.
Under the hood it uses DuckDuckGo HTML + page extraction (`agent/tools/web.py`).
Set `LLM_PROVIDER=openai|anthropic` for best synthesis quality (Ollama also works offline-only for these).

### Multi-account profiles
Keep separate contexts for different gigs/brands and switch instantly:
```bash
python cli.py profile add "Fiverr-Logo" --niche "logo design" --voice "bold, punchy"
python cli.py profile use "Fiverr-Logo"
python cli.py profile list
```
In the web UI: **Profiles** tab → add, then use the dropdown in the header.
An active profile overrides niche / brand voice / currency used in every generation.

### Draft workspace (review before you post)
Every gig, post, proposal, or report is **saved as a draft** for your approval — the agent
never auto-posts to your accounts. Review, copy, mark "ready", or delete:
```bash
python cli.py drafts                 # list
python cli.py draft <ID>             # show full content
python cli.py draft <ID> --approve   # mark ready-to-post
python cli.py draft <ID> --delete
```
In the web UI: **Drafts** tab → Copy to clipboard, Mark ready, Delete.

### Web UI auth
Set a password so only you can open the agent from your phone:
```bash
WEB_PASSWORD=yourStrongPassword python cli.py web
```
The UI shows a login screen; a session token is issued and stored in the browser.
Leave `WEB_PASSWORD` empty to disable auth (only safe on a trusted/local network).

> Note: the draft workflow is intentional. The agent prepares content locally for you to
> post manually — it does **not** log into Fiverr/Upwork to publish automatically, which
> would violate their Terms of Service.

## More: export, reminders, Upwork feed

### One-click Markdown export
Every draft can be exported as a clean Markdown file (with type/profile/status metadata):
```bash
python cli.py draft <ID> --export md                 # print to terminal
python cli.py draft <ID> --export md --out post.md  # save file
```
In the web UI: open **Drafts** → **Export .md** downloads `draft-<ID>.md`. **Copy** puts the
text on your clipboard for pasting into Fiverr/Upwork/social composers.

### Scheduled draft reminders
Never let a ready draft go stale. Set a nudge and the agent reminds you:
```bash
python cli.py remind <ID> 2h "post before noon"   # 30m / 2h / 3d / HH:MM
python cli.py reminders                            # list due + upcoming
```
In the web UI: **Remind** tab → pick a draft id + time → the server also runs a background
check that logs due reminders to the console.

### Official Upwork API (read-only job feed)
Pull **real** job listings and get bid suggestions — no auto-apply:
1. Create an app at https://www.upwork.com/developer/api (OAuth2).
2. Fill `UPWORK_CLIENT_ID`, `UPWORK_CLIENT_SECRET`, `UPWORK_REDIRECT_URI` in `.env`.
3. Run `python cli.py upwork-auth` → open the URL → paste the `code`:
   ```bash
   python cli.py upwork-auth <code-from-redirect>
   ```
   This prints an access token to paste into `UPWORK_ACCESS_TOKEN`.
4. Search:
   ```bash
   python cli.py upwork "Shopify store build"
   ```
   In the web UI: **Remind** tab → Upwork search box. Results are saved as a draft.

> The integration only **reads** the job feed (ToS-safe). It never applies, messages, or
> posts on your behalf.

## Minimize your load: Buffer scheduling, calendar reminders, digest

### Push approved drafts to Buffer (official scheduling)
Buffer is the legitimate way to schedule social posts you've approved — you connect your
accounts to Buffer once, then push a **ready** draft and Buffer publishes it on your schedule.
1. Get a Buffer access token (https://buffer.com/developers) and set `BUFFER_ACCESS_TOKEN`.
2. List connected profiles: `python cli.py buffer`
3. Push a draft: `python cli.py push <ID> --profiles <id1,id2> [--when 2h]`
   - In the web UI: **Drafts** → mark a draft *ready* → **Push Buffer** (enter profile ids).

This is the one-click publish path — still gated on *your* approval (draft must be "ready").

### Reminders as a phone calendar (.ics)
Export reminders so they appear in Google/Apple calendar and ping you automatically:
```bash
python cli.py reminders --ics reminders.ics     # import into your calendar app
```
Web UI: **Remind** tab → **Download reminders .ics**.

### Morning digest (one screen, zero guessing)
See everything pending at a glance:
```bash
python cli.py digest
```
Web UI: **Digest** tab. Shows due reminders, approved-ready drafts, unapproved drafts, and a
suggested next action.

### Suggested daily loop (minimal effort)
1. Open **Digest** → handle due reminders, push any "ready" drafts to Buffer.
2. Open **Chat** → "write a Fiverr gig for X" / "Upwork jobs for Y" → review the draft.
3. Approve drafts you like; push social ones to Buffer; keep the rest for later.

The agent does the writing, research, and scheduling prep. You make the final call.

## Quick start (any desktop OS)

```bash
cd marketing-agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env
```

### Choose an LLM (no key needed to start)
- **Ollama (free, local, private)** — install https://ollama.com, then `ollama pull llama3.1`.
  Leave `LLM_PROVIDER=ollama`.
- **OpenAI** — set `LLM_PROVIDER=openai` and `OPENAI_API_KEY=...`
- **Anthropic** — set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=...`

### Run it
```bash
python cli.py chat                 # interactive terminal chat
python cli.py run "write a Fiverr gig for logo design"
python cli.py web                  # mobile-friendly web UI at http://localhost:8000
```

## Reach it from your phone / anywhere

The `web` server exposes a mobile UI. To access it from a phone:

1. **Same Wi-Fi:** run `python cli.py web` on your computer, then open
   `http://<your-computer-IP>:8000` in your phone browser (find IP with `ipconfig`/`ifconfig`).
2. **From anywhere (no static IP):** expose it with a free tunnel:
   ```bash
   # install cloudflared or ngrok, then:
   cloudflared tunnel --url http://localhost:8000
   ```
   Open the generated `https://…` link on your phone.
3. **Always-on:** deploy on a VPS (Railway, Render, Fly.io, a $5 DigitalOcean droplet).
   The app is a standard FastAPI service — push the repo and set the same env vars.

> Security: the web UI has no auth by default. Only expose it through a tunnel/VPN you control,
> or put it behind a login (e.g. Cloudflare Access) before sharing the link.

## Phone / tablet as the host (Termux on Android)

Install [Termux](https://termux.com), then:
```bash
pkg update && pkg install python git
git clone <your-repo> marketing-agent && cd marketing-agent
pip install -r requirements.txt
# Ollama isn't available in Termux; use OpenAI/Anthropic:
# edit .env: LLM_PROVIDER=openai  + your key
python cli.py web --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000` in the phone browser, or expose via the tunnel method above.

**iOS:** a-Shell / Pythonista can run the CLI, but for the web UI use the tunnel/VPS method
and open the link in Safari.

## Command reference
| Command | Example |
|---|---|
| Chat | `python cli.py chat` |
| One-shot | `python cli.py run "7-day content calendar for a coffee brand"` |
| Fiverr gig | `python cli.py gig "video editing" --buyer "YouTubers"` |
| Upwork proposal | `python cli.py proposal --title "..." --desc "..." --value "..."` |
| Social post | `python cli.py post "new course launch" --platform LinkedIn` |
| Calendar | `python cli.py calendar "grow email list" --days 14` |
| Research | `python cli.py research "DesignPickle"` |
| Keywords | `python cli.py keywords --niche "logo design"` |
| Pricing | `python cli.py price "SEO audit" --tier mid` |
| Report | `echo "12 jobs, $1840, 40 proposals" \| python cli.py report` |
| Campaign | `python cli.py campaign "grow my SEO gig"` |
| Morning brief | `python cli.py brief` / `python cli.py cron --time 08:00` |
| Setup wizard | `python cli.py init` |

## Project layout
```
agent/        core agent, LLM wrapper, memory, modules/
server/       FastAPI web app + mobile UI
cli.py        command-line interface
.env.example  configuration template
```

## Safety & responsibility
This tool is an **assistant**. You remain responsible for what you publish and for complying
with each platform's Terms of Service. Do not use it to automate logged-in account actions,
scrape prohibited data, or misrepresent your identity.

## Even less effort: init, campaigns, auto brief

### First-run setup wizard
No hand-editing `.env`:
```bash
python cli.py init        # interactive prompts, writes .env
```

### One-command campaign
Build a full starter kit (calendar + 3 platform posts + keyword gaps + pricing + a Fiverr gig)
and save every piece as a draft in one go:
```bash
python cli.py campaign "grow my SEO gig"
```
Web UI: **Digest** tab → enter a goal → **Run campaign**. Review the drafts, approve, push.

### Automated morning brief (cron)
Save the daily digest to `data/digest-YYYY-MM-DD.txt` and deliver via webhook/email:
```bash
python cli.py brief                 # run once now (save + notify)
python cli.py cron --time 08:00     # loop daily, auto-deliver
```
Configure delivery in `.env`: `DIGEST_WEBHOOK` (Slack/Discord/etc.) and/or
`DIGEST_EMAIL_TO` + `SMTP_*`. Web UI: **Digest** → **Run brief**.

> Run `cron` headless on a VPS and your whole marketing operation self-manages day-to-day —
> the agent writes, researches, schedules-prep, and reminds; you approve the final post/apply.
