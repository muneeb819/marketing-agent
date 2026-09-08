"""FastAPI web server with a mobile-friendly UI, auth, profiles, and drafts."""
from __future__ import annotations

import os
import secrets
import threading
import time

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from agent import Agent
from agent.config import Config
from agent.scheduler import parse_when

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
INDEX = os.path.join(STATIC_DIR, "index.html")


def create_app() -> FastAPI:
    config = Config.load()
    agent = Agent(config)

    web_password = os.environ.get("WEB_PASSWORD", "")
    session_token = secrets.token_hex(16)
    app = FastAPI(title=config.agent_name)

    def require_auth(request: Request):
        if not web_password:
            return
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {session_token}":
            raise HTTPException(status_code=401, detail="unauthorized")

    @app.get("/api/status")
    def status():
        return {
            "agent": config.agent_name,
            "llm_provider": config.llm_provider,
            "llm_ready": agent.llm.models_available(),
            "niche": config.business_niche,
            "auth_required": bool(web_password),
            "profiles": agent.profiles.list(),
            "active_profile": agent.profiles.active(),
        }

    @app.post("/api/login")
    def login(payload: dict):
        pw = (payload or {}).get("password", "")
        if web_password and pw != web_password:
            raise HTTPException(status_code=401, detail="wrong password")
        return {"token": session_token, "auth_required": bool(web_password)}

    @app.post("/api/chat", dependencies=[Depends(require_auth)])
    def chat(payload: dict):
        text = (payload or {}).get("text", "")
        if not text:
            return JSONResponse({"reply": "Empty message."}, status_code=400)
        try:
            reply = agent.chat(text)
        except Exception as e:
            reply = f"[Agent error: {e}]"
        return {"reply": reply}

    # ---- profiles ----
    @app.get("/api/profiles", dependencies=[Depends(require_auth)])
    def get_profiles():
        return {"profiles": agent.profiles.list(), "active": agent.profiles.active()}

    @app.post("/api/profiles", dependencies=[Depends(require_auth)])
    def add_profile(payload: dict):
        name = payload.get("name")
        if not name:
            raise HTTPException(status_code=400, detail="name required")
        msg = agent.add_profile(
            name,
            niche=payload.get("niche", ""),
            voice=payload.get("voice", ""),
            currency=payload.get("currency", ""),
            handles=payload.get("handles", {}),
        )
        return {"msg": msg}

    @app.post("/api/profiles/use", dependencies=[Depends(require_auth)])
    def use_profile(payload: dict):
        return {"msg": agent.use_profile(payload.get("name", ""))}

    # ---- drafts ----
    @app.get("/api/drafts", dependencies=[Depends(require_auth)])
    def list_drafts():
        return {"drafts": agent.drafts.list()}

    @app.get("/api/drafts/{draft_id}", dependencies=[Depends(require_auth)])
    def get_draft(draft_id: int):
        d = agent.drafts.get(draft_id)
        if not d:
            raise HTTPException(status_code=404, detail="not found")
        return d

    @app.post("/api/drafts/{draft_id}/approve", dependencies=[Depends(require_auth)])
    def approve_draft(draft_id: int):
        return {"msg": agent.drafts.set_status(draft_id, "ready")}

    @app.delete("/api/drafts/{draft_id}", dependencies=[Depends(require_auth)])
    def delete_draft(draft_id: int):
        return {"msg": agent.drafts.delete(draft_id)}

    # ---- reminders ----
    @app.get("/api/reminders", dependencies=[Depends(require_auth)])
    def get_reminders():
        now = time.time()
        out = []
        for r in agent.scheduler.list():
            d = agent.drafts.get(r["draft_id"])
            out.append(
                {
                    "id": r["id"],
                    "draft_id": r["draft_id"],
                    "draft_title": d["title"] if d else "(deleted draft)",
                    "due": r["due"],
                    "due_label": time.strftime("%Y-%m-%d %H:%M", time.localtime(r["due"])),
                    "is_due": r["due"] <= now,
                    "note": r["note"],
                }
            )
        return {"reminders": out}

    @app.post("/api/reminders", dependencies=[Depends(require_auth)])
    def add_reminder(payload: dict):
        try:
            due = parse_when(payload.get("when", ""))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        rid = agent.scheduler.add(int(payload.get("draft_id")), due, payload.get("note", ""))
        return {"msg": f"Reminder #{rid} set.", "id": rid}

    @app.post("/api/reminders/{rid}/done", dependencies=[Depends(require_auth)])
    def done_reminder(rid: int):
        return {"msg": agent.scheduler.complete(rid)}

    @app.get("/api/reminders/ics", dependencies=[Depends(require_auth)])
    def reminders_ics():
        blocks = []
        for r in agent.scheduler.list():
            ics = agent.reminder_ics(r["id"])
            if ics:
                blocks.append(ics)
        return Response("\n".join(blocks) or "BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n",
                        media_type="text/calendar")

    # ---- buffer (official scheduling) ----
    @app.get("/api/buffer", dependencies=[Depends(require_auth)])
    def buffer_profiles():
        return {"profiles": agent.buffer_profiles()}

    @app.post("/api/push", dependencies=[Depends(require_auth)])
    def push(payload: dict):
        pids = [x.strip() for x in str(payload.get("profile_ids", "")).split(",") if x.strip()]
        res = agent.push_to_buffer(int(payload.get("draft_id")), pids, payload.get("when"))
        return {"result": res}

    # ---- morning digest ----
    @app.get("/api/digest", dependencies=[Depends(require_auth)])
    def digest():
        return {"digest": agent.digest()}

    @app.post("/api/brief", dependencies=[Depends(require_auth)])
    def brief():
        return {"digest": agent.morning_brief(save=True, notify=True)}

    @app.post("/api/campaign", dependencies=[Depends(require_auth)])
    def campaign(payload: dict):
        ids = agent.campaign(payload.get("goal", ""))
        return {"ids": ids}

    @app.post("/api/full_kit", dependencies=[Depends(require_auth)])
    def full_kit(payload: dict):
        ids = agent.full_marketing(
            payload.get("goal", ""),
            payload.get("niche"),
            payload.get("channels", "Instagram, TikTok, LinkedIn, X, Facebook"),
        )
        return {"ids": ids}

    # ---- upwork (read-only) ----
    @app.post("/api/upwork", dependencies=[Depends(require_auth)])
    def upwork(payload: dict):
        query = (payload or {}).get("query", "")
        result, draft_id = agent.generate("upwork_jobs", {"query": query})
        return {"reply": result, "draft_id": draft_id}

    @app.get("/")
    def index():
        return FileResponse(INDEX)

    # ---- background reminder nudge (logs to server console) ----
    def _reminder_loop():
        while True:
            time.sleep(30)
            try:
                due = agent.scheduler.due()
                for r in due:
                    d = agent.drafts.get(r["draft_id"])
                    title = d["title"] if d else f"draft {r['draft_id']}"
                    print(f"[REMINDER] #{r['id']} due now: {title} — {r['note']}")
                    agent.scheduler.complete(r["id"])
            except Exception:
                pass

    threading.Thread(target=_reminder_loop, daemon=True).start()

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


def run_server(host: str, port: int):
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port)


app = create_app()
