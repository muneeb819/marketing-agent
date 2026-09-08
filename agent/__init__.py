"""Agent orchestrator: routes commands to modules or general chat."""
from __future__ import annotations

import json
import os
import re
import time

from .config import Config
from .llm import LLM
from .memory import Memory
from .profiles import Profiles
from .drafts import Drafts
from .scheduler import Reminders, parse_when, to_ics
from .modules.analytics import Analytics
from .modules.content import Content
from .modules.proposals import Proposals
from .modules.research import Research
from .modules.growth import Growth


TOOLS = {
    "fiverr_gig": "Write a Fiverr gig (title, description, packages).",
    "upwork_proposal": "Write an Upwork cover letter from a job brief.",
    "bid_strategy": "Advise bid range, connects, and whether to apply.",
    "social_post": "Draft a social media post for a platform.",
    "content_calendar": "Build a multi-day content calendar.",
    "repurpose": "Turn long content into posts/email/title ideas.",
    "ad_copy": "Write paid-ad copy variants.",
    "competitor_brief": "Analyze a competitor's positioning (knowledge-based).",
    "keyword_gaps": "Find high-intent marketplace keywords.",
    "pricing_analysis": "Recommend pricing for a service.",
    "trend_scan": "Identify emerging trends + actions (knowledge-based).",
    "web_research": "Live web research brief on a topic.",
    "live_competitor": "Live competitor lookup via web search.",
    "live_trend_scan": "Live trend scan via web search.",
    "upwork_jobs": "Search live Upwork jobs (read-only) + bid suggestions.",
    "analytics_report": "Interpret performance data into a report.",
    "kpi_template": "Produce a KPI tracking template.",
    "funnel_diagnosis": "Diagnose a marketing funnel's weak stage.",
    "blog_post": "Write an SEO blog post / article.",
    "seo_keywords": "Build an SEO keyword plan with intent + difficulty.",
    "meta_tags": "Write SEO title / meta description / focus keywords.",
    "email_newsletter": "Write an email newsletter (with A/B subjects).",
    "email_sequence": "Write a multi-email nurture sequence.",
    "ad_pack": "Write a paid-ad pack (Meta + Google + TikTok variants).",
    "landing_page": "Write a high-converting landing page.",
    "social_strategy": "Build a per-platform social media strategy.",
}


class Agent:
    def __init__(self, config: Config):
        self.config = config
        self.llm = LLM(config)
        self.memory = Memory(config.db_path)
        self.profiles = Profiles(self.memory)
        self.drafts = Drafts(self.memory)
        self.scheduler = Reminders(self.memory)
        self._apply_profile()

        self.proposals = Proposals(self.llm, config)
        self.content = Content(self.llm, config)
        self.research = Research(self.llm, config)
        self.analytics = Analytics(self.llm, config)
        self.growth = Growth(self.llm, config)

    # ---- profiles ----
    def _apply_profile(self):
        p = self.profiles.active_dict()
        if not p:
            return
        if p.get("niche"):
            self.config.business_niche = p["niche"]
        if p.get("voice"):
            self.config.brand_voice = p["voice"]
        if p.get("currency"):
            self.config.currency = p["currency"]

    def use_profile(self, name: str) -> str:
        msg = self.profiles.set_active(name)
        self._apply_profile()
        return msg

    def add_profile(self, name: str, niche: str = "", voice: str = "", currency: str = "",
                    handles: dict = None) -> str:
        msg = self.profiles.add(name, niche, voice, currency, handles)
        self._apply_profile()
        return msg

    # ---- draft-saving dispatch ----
    def generate(self, tool: str, args: dict) -> tuple[str, int | None]:
        result = self._dispatch(tool, args)
        draft_id = self.drafts.add(
            kind=tool,
            title=self._draft_title(tool, args),
            content=result,
            profile=self.profiles.active() or "",
        )
        return result, draft_id

    def _draft_title(self, tool: str, args: dict) -> str:
        a = args or {}
        for key in ("service", "job_title", "topic", "goal", "competitor", "product",
                    "niche", "data", "source", "funnel"):
            if a.get(key):
                return f"{tool}: {str(a[key])[:60]}"
        return tool

    # ---- export ----
    def export_draft(self, draft_id: int, fmt: str = "md") -> str | None:
        d = self.drafts.get(draft_id)
        if not d:
            return None
        if fmt == "md":
            md = f"# {d['title']}\n\n"
            md += (
                f"- **Type:** {d['kind']}\n"
                f"- **Profile:** {d['profile'] or '—'}\n"
                f"- **Status:** {d['status']}\n"
                f"- **Created:** {time.ctime(d['created'])}\n\n---\n\n"
            )
            md += d["content"] + "\n"
            return md
        return d["content"]

    # ---- upwork auth helpers ----
    def upwork_auth_url(self) -> str:
        from .integrations import upwork as uw

        cid = os.environ.get("UPWORK_CLIENT_ID", "")
        red = os.environ.get("UPWORK_REDIRECT_URI", "http://localhost:8000/callback")
        if not cid:
            return "Set UPWORK_CLIENT_ID in .env first."
        return uw.auth_url(cid, red)

    def upwork_exchange(self, code: str) -> str:
        from .integrations import upwork as uw

        cid = os.environ.get("UPWORK_CLIENT_ID", "")
        sec = os.environ.get("UPWORK_CLIENT_SECRET", "")
        red = os.environ.get("UPWORK_REDIRECT_URI", "http://localhost:8000/callback")
        try:
            resp = uw.exchange_code(cid, sec, code, red)
            token = resp.get("access_token")
            if token:
                os.environ["UPWORK_ACCESS_TOKEN"] = token
                return f"Access token obtained. Set UPWORK_ACCESS_TOKEN={token} in your .env"
            return f"No token in response: {resp}"
        except Exception as e:
            return f"Exchange failed: {e}"

    # ---- Buffer (official scheduling) ----
    def buffer_profiles(self):
        from .integrations import buffer as buf

        token = os.environ.get("BUFFER_ACCESS_TOKEN", "")
        return buf.list_profiles(token)

    def push_to_buffer(self, draft_id: int, profile_ids: list, when: str | None = None):
        from .integrations import buffer as buf

        d = self.drafts.get(draft_id)
        if not d:
            return {"error": "draft not found"}
        token = os.environ.get("BUFFER_ACCESS_TOKEN", "")
        sched = int(parse_when(when)) if when else None
        return buf.create_post(token, d["content"], profile_ids, sched)

    # ---- reminders .ics ----
    def reminder_ics(self, rid: int) -> str | None:
        for r in self.scheduler.list(include_done=True):
            if r["id"] == rid:
                d = self.drafts.get(r["draft_id"])
                title = d["title"] if d else f"draft {r['draft_id']}"
                return to_ics(f"MarketingOps: {title}", r["due"], r["note"], uid=f"rem-{rid}")
        return None

    # ---- morning digest ----
    def digest(self) -> str:
        due = self.scheduler.due()
        ready = [d for d in self.drafts.list() if d["status"] == "ready"]
        pending = [d for d in self.drafts.list() if d["status"] == "draft"]
        lines = ["MORNING DIGEST — " + time.strftime("%Y-%m-%d"), ""]
        lines.append(f"Due reminders: {len(due)}")
        for r in due:
            lines.append(f"  - #{r['id']} draft {r['draft_id']}: {r['note'] or 'post/apply'}")
        lines.append(f"Ready to publish (approved): {len(ready)}")
        for d in ready:
            lines.append(f"  - #{d['id']} [{d['kind']}] {d['title']}")
        lines.append(f"Unapproved drafts: {len(pending)}")
        for d in pending[:10]:
            lines.append(f"  - #{d['id']} [{d['kind']}] {d['title']}")
        lines.append("\nSuggested next action:")
        if due:
            lines.append("  Handle due reminders first, then push 'ready' drafts to Buffer.")
        elif ready:
            lines.append("  Push 'ready' drafts to Buffer (python cli.py push <ID>).")
        else:
            lines.append("  Generate or approve drafts to keep the pipeline moving.")
        return "\n".join(lines)

    def morning_brief(self, save: bool = False, notify: bool = False) -> str:
        from .notify import notify

        text = self.digest()
        if save:
            os.makedirs(self.config.data_dir, exist_ok=True)
            fn = os.path.join(self.config.data_dir, "digest-" + time.strftime("%Y-%m-%d") + ".txt")
            with open(fn, "w", encoding="utf-8") as f:
                f.write(text)
        if notify:
            for status in notify(text):
                text += f"\n[notify] {status}"
        return text

    def campaign(self, goal: str, niche: str | None = None) -> list:
        """Generate a full starter kit for a goal and save each piece as a draft."""
        niche = niche or self.config.business_niche or goal
        ids = []
        for tool, args in [
            ("content_calendar", {"goal": goal, "days": 7}),
            ("social_post", {"topic": goal, "platform": "Instagram"}),
            ("social_post", {"topic": goal, "platform": "LinkedIn"}),
            ("social_post", {"topic": goal, "platform": "X"}),
            ("keyword_gaps", {"niche": niche}),
            ("pricing_analysis", {"service": goal, "tier": "mid"}),
            ("fiverr_gig", {"service": goal}),
        ]:
            try:
                _, did = self.generate(tool, args)
                ids.append(did)
            except Exception as e:
                ids.append(f"{tool}:err:{e}")
        return ids

    def full_marketing(self, goal: str, niche: str | None = None,
                       channels: str = "Instagram, TikTok, LinkedIn, X, Facebook") -> list:
        """Produce a complete digital-marketing kit and save every piece as a draft."""
        niche = niche or self.config.business_niche or goal
        steps = [
            ("social_strategy", {"goal": goal, "platforms": channels}),
            ("content_calendar", {"goal": goal, "days": 14, "platforms": channels}),
            ("social_post", {"topic": goal, "platform": "Instagram", "cta": "Link in bio"}),
            ("social_post", {"topic": goal, "platform": "TikTok", "cta": "Follow for more"}),
            ("social_post", {"topic": goal, "platform": "LinkedIn", "cta": "Connect with us"}),
            ("social_post", {"topic": goal, "platform": "X", "cta": "Follow us"}),
            ("social_post", {"topic": goal, "platform": "Facebook", "cta": "Message us"}),
            ("blog_post", {"topic": goal, "keywords": niche, "length": "long"}),
            ("email_newsletter", {"topic": goal, "goal": "nurture leads"}),
            ("email_sequence", {"topic": goal, "steps": 5}),
            ("ad_pack", {"product": goal, "audience": niche}),
            ("seo_keywords", {"niche": niche}),
            ("landing_page", {"product": goal, "goal": "convert visitors"}),
            ("pricing_analysis", {"service": goal, "tier": "mid"}),
        ]
        ids = []
        for tool, args in steps:
            try:
                _, did = self.generate(tool, args)
                ids.append(did)
            except Exception as e:
                ids.append(f"{tool}:err:{e}")
            time.sleep(1)  # be gentle on rate limits
        # if Buffer is connected, auto-schedule the social posts
        try:
            token = os.environ.get("BUFFER_ACCESS_TOKEN", "")
            if token:
                profs = self.buffer_profiles() or []
                pids = [p.get("id") for p in profs if p.get("id")]
                if pids:
                    for did in ids:
                        if isinstance(did, int):
                            d = self.drafts.get(did)
                            if d and d["kind"] == "social_post":
                                self.push_to_buffer(did, pids, None)
        except Exception:
            pass
        return ids

    def _dispatch(self, tool: str, args: dict) -> str:
        import inspect

        args = args or {}
        fn = getattr(self, f"_t_{tool}", None)
        if fn is None:
            return f"Unknown tool: {tool}"
        try:
            params = list(inspect.signature(fn).parameters)
            aliases = {
                "content": "topic", "text": "topic", "subject": "topic",
                "message": "topic", "description": "job_description",
                "buyer": "target_buyer", "audience": "target_buyer",
            }
            clean = {}
            for k, v in args.items():
                if k in params:
                    clean[k] = v
                elif k in aliases and aliases[k] in params:
                    clean[aliases[k]] = v
            return fn(**clean)
        except TypeError as e:
            return f"Tool '{tool}' argument error: {e}"

    # ---- tool implementations ----
    def _t_fiverr_gig(self, service, target_buyer="", packages=True):
        return self.proposals.fiverr_gig(service, target_buyer, packages)

    def _t_upwork_proposal(self, job_title="", job_description="", your_value=""):
        return self.proposals.upwork_proposal(job_title, job_description, your_value)

    def _t_bid_strategy(self, job_description=""):
        return self.proposals.bid_strategy(job_description)

    def _t_social_post(self, topic, platform="Instagram", cta=""):
        return self.content.post(topic, platform, cta)

    def _t_content_calendar(self, goal, days=7, platforms="Instagram, LinkedIn, X"):
        return self.content.calendar(goal, int(days), platforms)

    def _t_repurpose(self, source=""):
        return self.content.repurpose(source)

    def _t_ad_copy(self, product, audience="", platform="Facebook"):
        return self.content.ad_copy(product, audience, platform)

    def _t_competitor_brief(self, competitor, what="offerings and positioning"):
        return self.research.competitor_brief(competitor, what)

    def _t_keyword_gaps(self, niche=""):
        return self.research.keyword_gaps(niche)

    def _t_pricing_analysis(self, service, tier="mid"):
        return self.research.pricing_analysis(service, tier)

    def _t_trend_scan(self, topic=""):
        return self.research.trend_scan(topic)

    def _t_web_research(self, topic=""):
        return self.research.web_research(topic)

    def _t_live_competitor(self, competitor=""):
        return self.research.live_competitor(competitor)

    def _t_live_trend_scan(self, topic=""):
        return self.research.live_trend_scan(topic)

    def _t_upwork_jobs(self, query=""):
        return self.research.upwork_feed(query)

    def _t_analytics_report(self, data, period="last month"):
        return self.analytics.report(data, period)

    def _t_kpi_template(self):
        return self.analytics.kpi_dashboard_template()

    def _t_funnel_diagnosis(self, funnel=""):
        return self.analytics.funnel_diagnosis(funnel)

    # ---- growth / full-funnel digital marketing ----
    def _t_blog_post(self, topic, keywords="", length="medium"):
        return self.growth.blog_post(topic, keywords, length)

    def _t_seo_keywords(self, niche):
        return self.growth.seo_keywords(niche)

    def _t_meta_tags(self, page, keywords=""):
        return self.growth.meta_tags(page, keywords)

    def _t_email_newsletter(self, topic, goal=""):
        return self.growth.email_newsletter(topic, goal)

    def _t_email_sequence(self, topic, steps=5):
        return self.growth.email_sequence(topic, steps)

    def _t_ad_pack(self, product, audience=""):
        return self.growth.ad_pack(product, audience)

    def _t_landing_page(self, product, goal=""):
        return self.growth.landing_page(product, goal)

    def _t_social_strategy(self, goal, platforms="Instagram, TikTok, LinkedIn, X, Facebook"):
        return self.growth.social_strategy(goal, platforms)

    # ---- routing ----
    def agentic_run(self, user_text: str) -> str:
        self.memory.add_message("user", user_text)
        tools_desc = "\n".join(f"- {k}: {v}" for k, v in TOOLS.items())
        sys = (
            f"You are {self.config.agent_name}, a marketing operations assistant for "
            f"{self.config.business_niche or 'a freelance/marketing business'}. "
            "If the user's request clearly matches one of the tools below, respond with ONLY a "
            "JSON object of the form {\"tool\": \"name\", \"args\": {..}} using the argument "
            "names implied by the tool. Otherwise, respond with a helpful answer in plain text "
            "(no JSON). Do not invent tools. Keep args concise.\n\nTools:\n" + tools_desc
        )
        decision = self.llm.chat(
            [
                {"role": "system", "content": sys},
                {"role": "user", "content": user_text},
            ],
            temperature=0.2,
            max_tokens=600,
        )
        tool_call = self._extract_json(decision)
        if tool_call:
            result, draft_id = self.generate(tool_call.get("tool"), tool_call.get("args"))
            result = f"{result}\n\n— saved as draft #{draft_id} (review in 'drafts')."
        else:
            result = decision if not decision.startswith("[") else self._general(user_text)
        self.memory.add_message("assistant", result)
        return result

    def _general(self, user_text: str) -> str:
        sys = (
            f"You are {self.config.agent_name}, a marketing operations assistant. Be concise and "
            "actionable. If you need more detail to use a tool, ask for it."
        )
        return self.llm.chat(
            [
                {"role": "system", "content": sys},
                {"role": "user", "content": user_text},
            ]
        )

    @staticmethod
    def _extract_json(text: str) -> dict | None:
        try:
            return json.loads(text)
        except Exception:
            pass
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None

    def chat(self, user_text: str) -> str:
        return self.agentic_run(user_text)
