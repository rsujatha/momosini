"""Local web app that wires the tracker UI to the agent — the demo glue.

GET  /          -> serves the deterministic tracker (tracker/mom-day-tracker.html)
POST /compose   -> runs the ONE agent (agent/runner.compose_day), returns clean blocks JSON

Same-origin, so the page calls /compose with a plain fetch (no CORS). The agent still gets its
facts from the bundled MCP server; this layer only carries the parent's inputs in and the
composed day out. Personal data (age, day description) stays on this local app — only age_months
reaches a knowledge tool, inside the agent.

Run:
  pip install -r requirements.txt
  GOOGLE_API_KEY in .env  (see .env.example)
  uvicorn web.app:app --reload      # then open http://127.0.0.1:8000
  # or:  python -m web.app
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from agent.runner import (
    compose_day,
    format_parent_message,
    send_message,
    start_conversation,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
TRACKER_HTML = REPO_ROOT / "tracker" / "mom-day-tracker.html"

app = FastAPI(title="mom-day-organiser")


class ComposeRequest(BaseModel):
    age_months: int
    day_description: str
    help_windows: str | None = None
    goal: str | None = None
    evening: str | None = None
    trigger: str = "onboarding"


class ConverseRequest(BaseModel):
    """One turn of the conversational onboarding.

    First turn: no session_id; send age_months + the parent's free-text reply as `message`.
    Later turns: include the session_id from the previous response and the parent's answer.
    """
    message: str
    session_id: str | None = None
    age_months: int | None = None
    trigger: str = "onboarding"


def _quota_hint(msg: str) -> str:
    if "503" in msg or "UNAVAILABLE" in msg or "high demand" in msg:
        return " (Gemini is momentarily overloaded — wait a few seconds and try again, or set ADK_MODEL to gemini-2.5-flash-lite.)"
    if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
        return " (Gemini quota / model — try again, or set ADK_MODEL to a current free-tier model.)"
    if "API_KEY" in msg.upper() or "api key" in msg.lower():
        return " (Set GOOGLE_API_KEY in .env.)"
    return ""


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(TRACKER_HTML.read_text(encoding="utf-8"))


@app.post("/compose")
async def compose(req: ComposeRequest) -> JSONResponse:
    """Run the agent for one compose turn and hand back the parsed blocks JSON."""
    try:
        result = await compose_day(**req.model_dump())
    except Exception as e:  # missing key, 429 quota, model errors — surface, don't crash the page
        msg = str(e)
        return JSONResponse(status_code=502,
                            content={"ok": False, "error": msg[:300] + _quota_hint(msg)})

    composed = result.get("composed")
    if composed and composed.get("blocks"):
        return JSONResponse({
            "ok": True,
            "composed": composed,                       # {blocks:[...], changes?:[...]}
            "tool_calls": [c["name"] for c in result.get("tool_calls", [])],
        })
    # No JSON came back — the model likely asked a clarifying question.
    return JSONResponse({
        "ok": True,
        "composed": None,
        "question": result.get("final_text"),
        "tool_calls": [c["name"] for c in result.get("tool_calls", [])],
    })


@app.post("/converse")
async def converse(req: ConverseRequest) -> JSONResponse:
    """Run one interview turn. Returns the agent's next question OR the composed day.

    The agent drives: it may call its knowledge tools, ask a follow-up (`done: false`, text in
    `question`), or finish (`done: true`, blocks in `composed`). Personal data — including the
    free text — stays on this local app; only age_months ever reaches a knowledge tool.
    """
    try:
        if not req.session_id:
            session_id = await start_conversation()
            opening = format_parent_message(
                trigger=req.trigger,
                age_months=req.age_months,
                day_description=req.message,
            )
            result = await send_message(session_id=session_id, message=opening)
        else:
            result = await send_message(session_id=req.session_id, message=req.message)
    except Exception as e:
        msg = str(e)
        return JSONResponse(status_code=502,
                            content={"ok": False, "error": msg[:300] + _quota_hint(msg)})

    tool_calls = [c["name"] for c in result.get("tool_calls", [])]
    composed = result.get("composed")
    if composed and composed.get("blocks"):
        return JSONResponse({
            "ok": True,
            "done": True,
            "session_id": result["session_id"],
            "composed": composed,
            "tool_calls": tool_calls,
        })
    # No JSON yet — the agent asked a follow-up question; continue the same session next turn.
    return JSONResponse({
        "ok": True,
        "done": False,
        "session_id": result["session_id"],
        "question": result.get("final_text"),
        "tool_calls": tool_calls,
    })


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
