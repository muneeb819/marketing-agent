#!/usr/bin/env python3
"""Command-line interface for the MarketingOps Agent."""
from __future__ import annotations

import argparse
import json
import sys
import time

from agent import Agent
from agent.config import Config
from agent.scheduler import parse_when


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="marketing-agent",
        description="AI marketing operations agent (assisted Fiverr/Upwork + social/research/analytics).",
    )
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("chat", help="Interactive chat with the agent.")
    sub.add_parser("setup", help="Show current configuration.")
    sub.add_parser("drafts", help="List saved drafts.")

    run_p = sub.add_parser("run", help="Run a single natural-language command.")
    run_p.add_argument("text", nargs="+", help="Command text")

    web_p = sub.add_parser("web", help="Launch the mobile-friendly web server.")
    web_p.add_argument("--host", default=None)
    web_p.add_argument("--port", type=int, default=None)

    # profiles
    prof = sub.add_parser("profile", help="Manage multi-account profiles.")
    psub = prof.add_subparsers(dest="pcmd")
    psub.add_parser("list")
    pshow = psub.add_parser("show")
    pshow.add_argument("name")
    puse = psub.add_parser("use")
    puse.add_argument("name")
    prm = psub.add_parser("remove")
    prm.add_argument("name")
    padd = psub.add_parser("add")
    padd.add_argument("name")
    padd.add_argument("--niche", default="")
    padd.add_argument("--voice", default="")
    padd.add_argument("--currency", default="")
    padd.add_argument("--handles", default="", help="key=value,key2=value2")

    # drafts management
    dshow = sub.add_parser("draft", help="Show/approve/delete a draft.")
    dshow.add_argument("id", type=int)
    dshow.add_argument("--approve", action="store_true", help="Mark as ready-to-post")
    dshow.add_argument("--delete", action="store_true")
    dshow.add_argument("--export", choices=["md", "clip"], default=None, help="Export as Markdown or copy")
    dshow.add_argument("--out", default=None, help="Write Markdown export to this file path")

    # reminders
    remp = sub.add_parser("reminders", help="List draft reminders (due + upcoming).")
    remp.add_argument("--ics", default=None, help="Export all reminders to an .ics file")
    rm = sub.add_parser("remind", help="Set a reminder on a draft.")
    rm.add_argument("id", type=int, help="draft id")
    rm.add_argument("when", help="e.g. 30m, 2h, 3d, or HH:MM")
    rm.add_argument("note", nargs="?", default="", help="optional note")

    # buffer (official scheduling)
    sub.add_parser("buffer", help="List connected Buffer profiles.")
    push = sub.add_parser("push", help="Push an approved draft to Buffer (official scheduling).")
    push.add_argument("id", type=int, help="draft id")
    push.add_argument("--profiles", default="", help="comma-separated Buffer profile ids")
    push.add_argument("--when", default=None, help="schedule time: 30m/2h/3d/HH:MM")

    # morning digest
    sub.add_parser("digest", help="One-screen overview of pending work.")
    sub.add_parser("brief", help="Run morning brief (save + notify if configured).")
    cronp = sub.add_parser("cron", help="Run the morning brief daily at a set time.")
    cronp.add_argument("--time", default="08:00", help="HH:MM daily")
    camp = sub.add_parser("campaign", help="Build a full draft kit for a goal in one command.")
    camp.add_argument("goal", nargs="+", help="campaign goal, e.g. 'grow my SEO gig'")
    sub.add_parser("init", help="First-run setup wizard (writes .env).")

    # upwork (read-only)
    sub.add_parser("upwork-auth", help="Show OAuth URL / exchange code for Upwork.")
    uw = sub.add_parser("upwork", help="Search live Upwork jobs (read-only).")
    uw.add_argument("query")

    # direct module shortcuts
    gig = sub.add_parser("gig", help="Fiverr gig")
    gig.add_argument("service")
    gig.add_argument("--buyer", default="")

    prop = sub.add_parser("proposal", help="Upwork proposal")
    prop.add_argument("--title", default="")
    prop.add_argument("--desc", default="")
    prop.add_argument("--value", default="")

    post = sub.add_parser("post", help="Social post")
    post.add_argument("topic")
    post.add_argument("--platform", default="Instagram")
    post.add_argument("--cta", default="")

    cal = sub.add_parser("calendar", help="Content calendar")
    cal.add_argument("goal")
    cal.add_argument("--days", type=int, default=7)
    cal.add_argument("--platforms", default="Instagram, LinkedIn, X")

    rep = sub.add_parser("research", help="Competitor brief (knowledge)")
    rep.add_argument("competitor")

    rep2 = sub.add_parser("keywords", help="Keyword gaps")
    rep2.add_argument("--niche", default="")

    price = sub.add_parser("price", help="Pricing analysis")
    price.add_argument("service")
    price.add_argument("--tier", default="mid")

    report = sub.add_parser("report", help="Analytics report")
    report.add_argument("--period", default="last month")
    report.add_argument("--data", default="")

    return p


def _print_draft(result, draft_id):
    print(result)
    if draft_id:
        print(f"\n— saved as draft #{draft_id} (review with: python cli.py drafts)")


def run_init():
    print("First-run setup. Press Enter to accept the [default].")
    if sys.stdin.isatty():
        def ask(q, default):
            try:
                v = input(f"{q} [{default}]: ").strip()
            except EOFError:
                v = ""
            return v or default
    else:
        def ask(q, default):
            return default

    provider = ask("LLM provider (openai / anthropic / ollama)", "ollama")
    lines = [f"LLM_PROVIDER={provider}"]
    if provider == "openai":
        lines += [
            f"OPENAI_API_KEY={ask('OpenAI API key', '')}",
            f"OPENAI_MODEL={ask('OpenAI model', 'gpt-4o-mini')}",
        ]
    elif provider == "anthropic":
        lines += [
            f"ANTHROPIC_API_KEY={ask('Anthropic API key', '')}",
            f"ANTHROPIC_MODEL={ask('Anthropic model', 'claude-3-5-sonnet-latest')}",
        ]
    else:
        lines += [
            "OPENAI_API_KEY=",
            "OPENAI_MODEL=gpt-4o-mini",
            "ANTHROPIC_API_KEY=",
            "ANTHROPIC_MODEL=claude-3-5-sonnet-latest",
            "OLLAMA_BASE_URL=http://localhost:11434",
            "OLLAMA_MODEL=llama3.1",
        ]
    lines += [
        f"AGENT_NAME={ask('Agent name', 'MarketingOps Agent')}",
        f"BUSINESS_NICHE={ask('Business niche', '')}",
        f"BRAND_VOICE={ask('Brand voice', 'professional, friendly, concise')}",
        f"CURRENCY={ask('Currency', 'USD')}",
        "DATA_DIR=data",
        "DB_PATH=data/memory.db",
        f"HOST={ask('Web host', '0.0.0.0')}",
        f"PORT={ask('Web port', '8000')}",
        f"WEB_PASSWORD={ask('Web password (empty = disabled)', '')}",
        f"BUFFER_ACCESS_TOKEN={ask('Buffer access token (empty = skip)', '')}",
        "UPWORK_CLIENT_ID=",
        "UPWORK_CLIENT_SECRET=",
        "UPWORK_REDIRECT_URI=http://localhost:8000/callback",
        "UPWORK_ACCESS_TOKEN=",
    ]
    with open(".env", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n.env written. Next: python cli.py web   (or: python cli.py init again to redo)")


def main(argv=None):
    args = build_parser().parse_args(argv)
    config = Config.load()
    agent = Agent(config)

    if args.cmd == "setup":
        print(json.dumps(config.as_dict(), indent=2))
        print("\nLLM reachable:", agent.llm.models_available())
        print("Profiles:", agent.profiles.list(), "| active:", agent.profiles.active())
        return

    if args.cmd == "chat":
        active = agent.profiles.active()
        print(f"{config.agent_name} ready. Active profile: {active or '(none)'}. Type 'exit'.\n")
        while True:
            try:
                text = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not text:
                continue
            if text.lower() in {"exit", "quit"}:
                break
            print("\nagent>", agent.chat(text), "\n")
        return

    if args.cmd == "run":
        print(agent.chat(" ".join(args.text)))
        return

    if args.cmd == "web":
        from server.app import run_server

        host = args.host or config.host
        port = args.port or config.port
        run_server(host, port)
        return

    if args.cmd == "profile":
        if args.pcmd == "list":
            print("Profiles:", agent.profiles.list(), "| active:", agent.profiles.active())
        elif args.pcmd == "show":
            print(json.dumps(agent.profiles.get(args.name), indent=2))
        elif args.pcmd == "use":
            print(agent.use_profile(args.name))
        elif args.pcmd == "remove":
            print(agent.profiles.remove(args.name))
        elif args.pcmd == "add":
            handles = {}
            if args.handles:
                for kv in args.handles.split(","):
                    k, _, v = kv.partition("=")
                    handles[k.strip()] = v.strip()
            print(agent.add_profile(args.name, args.niche, args.voice, args.currency, handles))
        else:
            print("Use: profile list|show|use|remove|add")
        return

    if args.cmd == "drafts":
        for d in agent.drafts.list():
            print(f"#{d['id']}  [{d['kind']}] {d['status']:8} {d['title']}  ({d['profile'] or 'no profile'})")
        return

    if args.cmd == "draft":
        d = agent.drafts.get(args.id)
        if not d:
            print("Draft not found.")
            return
        if args.delete:
            print(agent.drafts.delete(args.id))
            return
        if args.approve:
            print(agent.drafts.set_status(args.id, "ready"))
            return
        if args.export == "md":
            md = agent.export_draft(args.id, fmt="md")
            if args.out:
                with open(args.out, "w", encoding="utf-8") as f:
                    f.write(md)
                print(f"Exported Markdown to {args.out}")
            else:
                print(md)
            return
        if args.export == "clip":
            try:
                import pyperclip

                pyperclip.copy(d["content"])
                print("Copied to clipboard.")
            except Exception:
                print(d["content"])
            return
        print(f"#{d['id']} [{d['kind']}] {d['status']} — {d['profile']}\n")
        print(d["content"])
        return

    if args.cmd == "reminders":
        rems = agent.scheduler.list()
        if args.ics:
            blocks = []
            for r in rems:
                d = agent.drafts.get(r["draft_id"])
                title = d["title"] if d else f"draft {r['draft_id']}"
                blocks.append(agent.reminder_ics(r["id"]) or "")
            with open(args.ics, "w", encoding="utf-8") as f:
                for b in blocks:
                    f.write(b + "\n")
            print(f"Exported {len(blocks)} reminders to {args.ics}")
            return
        for r in rems:
            due = time.strftime("%Y-%m-%d %H:%M", time.localtime(r["due"]))
            flag = "DUE" if r["due"] <= time.time() else "   "
            print(f"[{flag}] #{r['id']} draft {r['draft_id']} @ {due}  {r['note']}")
        return

    if args.cmd == "buffer":
        profs = agent.buffer_profiles()
        if isinstance(profs, list) and profs and "error" not in profs[0]:
            for p in profs:
                print(f"{p.get('id')}  {p.get('service')}/{p.get('service_username')}  {p.get('formatted_username','')}")
        else:
            print("Buffer:", profs)
        return

    if args.cmd == "push":
        pids = [x.strip() for x in args.profiles.split(",") if x.strip()]
        res = agent.push_to_buffer(args.id, pids, args.when)
        if "error" in res:
            print("Push failed:", res["error"])
        else:
            print("Pushed to Buffer:", res.get("success", True))
        return

    if args.cmd == "digest":
        print(agent.digest())
        return

    if args.cmd == "brief":
        print(agent.morning_brief(save=True, notify=True))
        return

    if args.cmd == "cron":
        import datetime

        hh, mm = (int(x) for x in args.time.split(":"))
        print(f"Morning-brief cron started for {args.time} daily. Ctrl+C to stop.")
        last = None
        try:
            while True:
                now = datetime.datetime.now()
                if now.hour == hh and now.minute == mm and now.strftime("%Y-%m-%d") != last:
                    print(agent.morning_brief(save=True, notify=True))
                    last = now.strftime("%Y-%m-%d")
                time.sleep(30)
        except KeyboardInterrupt:
            print("\nStopped.")
        return

    if args.cmd == "campaign":
        ids = agent.campaign(" ".join(args.goal))
        print("Campaign drafts created:", ids)
        return

    if args.cmd == "init":
        run_init()
        return

    if args.cmd == "remind":
        try:
            due = parse_when(args.when)
        except ValueError as e:
            print(e)
            return
        rid = agent.scheduler.add(args.id, due, args.note)
        print(f"Reminder #{rid} set for draft {args.id}.")
        return

    if args.cmd == "upwork-auth":
        if args.code:
            print(agent.upwork_exchange(args.code))
        else:
            print("1) Open this URL and authorize:\n")
            print(agent.upwork_auth_url())
            print("\n2) Then run:  python cli.py upwork-auth <code-from-redirect>")
        return

    if args.cmd == "upwork":
        r, did = agent.generate("upwork_jobs", {"query": args.query})
        _print_draft(r, did)
        return

    # ---- module shortcuts (also saved as drafts) ----
    if args.cmd == "gig":
        r, did = agent.generate("fiverr_gig", {"service": args.service, "target_buyer": args.buyer})
        _print_draft(r, did); return
    if args.cmd == "proposal":
        r, did = agent.generate("upwork_proposal", {"job_title": args.title, "job_description": args.desc, "your_value": args.value})
        _print_draft(r, did); return
    if args.cmd == "post":
        r, did = agent.generate("social_post", {"topic": args.topic, "platform": args.platform, "cta": args.cta})
        _print_draft(r, did); return
    if args.cmd == "calendar":
        r, did = agent.generate("content_calendar", {"goal": args.goal, "days": args.days, "platforms": args.platforms})
        _print_draft(r, did); return
    if args.cmd == "research":
        r, did = agent.generate("competitor_brief", {"competitor": args.competitor})
        _print_draft(r, did); return
    if args.cmd == "keywords":
        r, did = agent.generate("keyword_gaps", {"niche": args.niche})
        _print_draft(r, did); return
    if args.cmd == "price":
        r, did = agent.generate("pricing_analysis", {"service": args.service, "tier": args.tier})
        _print_draft(r, did); return
    if args.cmd == "report":
        data = args.data or sys.stdin.read()
        r, did = agent.generate("analytics_report", {"data": data, "period": args.period})
        _print_draft(r, did); return

    build_parser().print_help()


if __name__ == "__main__":
    main()
