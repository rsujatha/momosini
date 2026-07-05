"""Arc 3 — the agent loop (SCAFFOLD, co-owned).

Drives the one agent through decide -> call tool -> observe -> (maybe ask one question) ->
compose. This is the piece that makes it an AGENT rather than a pipeline: we do NOT script the
tool calls here — we hand the model the parent's goal + the compose method, and the MODEL chooses
to call get_nap_guidance / get_milestone_checkin and loops toward a composed day.

What's deliberately left for the owners:
  - agent/instructions.py — the facts-discipline system prompt. OWNED BY SUJATHA. Imported, not
    edited. (The compose METHOD is layered on at runtime below; the RULES stay in that file.)
  - the final compose output handling / tracker hand-off — co-owned (arc 3 finish + integration).

Verified against google-adk 2.3.0:
  Runner(app_name=, agent=, session_service=InMemorySessionService())
  await session_service.create_session(app_name=, user_id=, session_id=)
  runner.run_async(user_id=, session_id=, new_message=types.Content(role="user", parts=[...]))
    -> async stream of Events; tool calls appear as part.function_call, results as
       part.function_response, final answer as the model's text parts.

Run (needs a key):  GOOGLE_API_KEY=... python -m agent.runner
Without a key it does a construction-only self-check and exits.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import re
import uuid
from pathlib import Path

from dotenv import load_dotenv  # ships with google-adk
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import MODEL, build_mcp_toolset, resolve_model
from .instructions import SYSTEM_INSTRUCTION

APP_NAME = "mom-day-organiser"
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = Path(__file__).resolve().parent / "skills" / "compose-baby-day" / "SKILL.md"

# Honor the key in .env even when run as `python -m agent.runner` (which, unlike `adk run`,
# does not auto-load .env). Loads GOOGLE_API_KEY from the repo-root .env if present.
load_dotenv(REPO_ROOT / ".env")


# --- the compose-baby-day Skill: the METHOD, loaded on demand (not the facts, not the rules) ---
def load_compose_skill() -> str:
    """Return the Skill body (procedure + output contract), with YAML frontmatter stripped."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    if text.startswith("---"):
        # drop the first frontmatter block: ---\n ... \n---\n
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]
    return text.strip()


def build_compose_agent() -> LlmAgent:
    """The agent for an onboarding/restructure turn: facts-discipline RULES first, then the
    compose METHOD appended at runtime. instructions.py is never modified — the method is a
    separate doc the prompt already tells the model to follow ('Follow the compose-baby-day Skill').
    """
    runtime_instruction = (
        SYSTEM_INSTRUCTION
        + "\n\n--- compose-baby-day Skill (method + output contract) ---\n"
        + load_compose_skill()
    )
    return LlmAgent(
        name="mom_day_organiser",
        model=resolve_model(),
        instruction=runtime_instruction,
        tools=[build_mcp_toolset()],
    )


def format_parent_message(
    *,
    day_description: str | None = None,
    age_months: int | None = None,
    help_windows: str | None = None,
    goal: str | None = None,
    evening: str | None = None,
    trigger: str = "onboarding",
) -> str:
    """Turn the structured inputs the SKILL expects into the parent's turn. Personal data stays
    in this message (local); only age_months is ever passed onward to a tool, by the model."""
    lines = [f"trigger: {trigger}"]
    if age_months is not None:
        lines.append(f"age_months: {age_months}")
    if day_description:
        lines.append(f"day_description: {day_description}")
    if help_windows:
        lines.append(f"help_windows: {help_windows}")
    if goal:
        lines.append(f"goal: {goal}")
    if evening:
        lines.append(f"evening/bedtime: {evening}")
    lines.append("\nCompose (or restructure) my day per the compose-baby-day method. "
                 "Return the blocks JSON from the output contract.")
    return "\n".join(lines)


async def run_turn(runner: Runner, *, user_id: str, session_id: str, message: str,
                   trace: bool = True) -> dict:
    """Send one user turn; stream the agent's decide/call/observe loop; return what came back.

    Returns {tool_calls: [...], final_text: str|None}. The model may instead return ONE
    clarifying question as final_text (no tool calls / no JSON) — the caller continues the same
    session with the answer to finish composing.
    """
    content = types.Content(role="user", parts=[types.Part(text=message)])
    tool_calls: list[dict] = []
    final_text: str | None = None

    async for event in runner.run_async(user_id=user_id, session_id=session_id,
                                         new_message=content):
        for part in (event.content.parts if event.content else []) or []:
            if getattr(part, "function_call", None):
                fc = part.function_call
                tool_calls.append({"name": fc.name, "args": dict(fc.args or {})})
                if trace:
                    print(f"  → model calls {fc.name}({dict(fc.args or {})})")
            elif getattr(part, "function_response", None) and trace:
                print(f"  ← tool {part.function_response.name} returned (observed)")
        if event.is_final_response() and event.content:
            final_text = "".join(p.text for p in event.content.parts if getattr(p, "text", None))

    return {"tool_calls": tool_calls, "final_text": final_text}


def _first_balanced_object(text: str) -> str | None:
    """Return the first complete {...} object in text (brace-balanced, string-aware)."""
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        start = text.find("{", start + 1)
    return None


def extract_blocks_json(text: str | None) -> dict | None:
    """Pull the blocks JSON out of the model's reply.

    The model wraps its JSON in prose and ```json fences; the tracker needs clean JSON. Returns
    the parsed dict ({"blocks": [...], "changes"?: [...]}) or None if there's no JSON object
    (e.g. the model asked a clarifying question instead).
    """
    if not text:
        return None
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = fence.group(1) if fence else _first_balanced_object(text)
    if not candidate:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


# Transient Gemini errors worth retrying (model overloaded / rate-limited, not our fault).
_TRANSIENT = ("503", "UNAVAILABLE", "high demand", "overloaded",
              "429", "RESOURCE_EXHAUSTED")


def _is_transient(err: Exception) -> bool:
    s = str(err)
    return any(t in s for t in _TRANSIENT)


def _server_retry_delay(err: Exception) -> float | None:
    """Honor Gemini's own suggested wait (e.g. RetryInfo {'retryDelay': '56s'}) when present."""
    m = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", str(err))
    return float(m.group(1)) if m else None


async def _backoff_sleep(err: Exception, attempt: int, base_delay: float,
                         max_attempts: int, *, max_delay: float = 30.0) -> None:
    """Wait before the next retry: the larger of exponential backoff and the server's hint,
    capped, with a little jitter so parallel callers don't sync up. 503 overload spikes can run
    several seconds, so this self-heals rather than failing after one quick retry."""
    backoff = base_delay * (2 ** (attempt - 1))             # 2, 4, 8, 16…
    delay = min(max_delay, max(backoff, _server_retry_delay(err) or 0.0))
    delay += random.uniform(0, 0.5)
    print(f"  … transient model error (attempt {attempt}/{max_attempts}); retry in {delay:.1f}s")
    await asyncio.sleep(delay)


async def _compose_once(*, session_id: str | None = None, **inputs) -> dict:
    agent = build_compose_agent()
    session_service = InMemorySessionService()
    runner = Runner(app_name=APP_NAME, agent=agent, session_service=session_service)
    user_id = "local-parent"
    session_id = session_id or "compose-1"
    await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)

    message = format_parent_message(**inputs)
    result = await run_turn(runner, user_id=user_id, session_id=session_id, message=message)
    result["session_id"] = session_id
    # Parsed blocks JSON for the tracker; None if the model asked a clarifying question instead.
    result["composed"] = extract_blocks_json(result.get("final_text"))
    return result


async def compose_day(*, session_id: str | None = None, max_attempts: int = 5,
                      retry_base_delay: float = 2.0, **inputs) -> dict:
    """One-shot entry: build the compose agent + runner, run a turn from structured inputs.

    Retries transient model errors (503 overloaded / 429 rate-limit) with exponential backoff that
    also honors Gemini's suggested retry delay, so a momentary blip self-heals instead of failing
    the page. Reuse the returned session_id with run_turn() to answer a clarifying question in the
    same session. Requires GOOGLE_API_KEY.

    Note: a 429 daily-quota exhaustion (free tier ~20 req/day/model) won't clear by retrying —
    switch ADK_MODEL (e.g. gemini-2.5-flash-lite) or wait for the daily reset.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return await _compose_once(session_id=session_id, **inputs)
        except Exception as e:
            if _is_transient(e) and attempt < max_attempts:
                await _backoff_sleep(e, attempt, retry_base_delay, max_attempts)
                continue
            raise


# --- multi-turn conversation (step 1: transport for the conversational onboarding) ---
# The one-shot compose_day() above builds a fresh session per call, so it cannot carry an
# interview across turns. These helpers keep ONE long-lived runner + session service alive so the
# agent can ask a follow-up on one turn and read the parent's answer on the next, in the same
# session. This is plumbing only — HOW MANY questions the agent asks (the 5–6 interview policy)
# and the persona live in the protected files and the Skill, changed separately (see
# docs/PLAN-conversational-onboarding.md, steps 2–3).
_CONV_USER = "local-parent"
_conv_runner: Runner | None = None
_conv_session_service: InMemorySessionService | None = None


def _ensure_runner() -> tuple[Runner, InMemorySessionService]:
    """Lazily build the single shared runner + in-memory session service (no model call here)."""
    global _conv_runner, _conv_session_service
    if _conv_runner is None:
        _conv_session_service = InMemorySessionService()
        _conv_runner = Runner(
            app_name=APP_NAME,
            agent=build_compose_agent(),
            session_service=_conv_session_service,
        )
    return _conv_runner, _conv_session_service


async def _session_exists(svc: InMemorySessionService, session_id: str) -> bool:
    try:
        existing = await svc.get_session(
            app_name=APP_NAME, user_id=_CONV_USER, session_id=session_id
        )
        return existing is not None
    except Exception:
        return False


async def start_conversation() -> str:
    """Create a new interview session and return its id. No API key needed (in-memory only)."""
    _, svc = _ensure_runner()
    session_id = f"conv-{uuid.uuid4().hex[:12]}"
    await svc.create_session(app_name=APP_NAME, user_id=_CONV_USER, session_id=session_id)
    return session_id


async def send_message(*, session_id: str, message: str, max_attempts: int = 5,
                       retry_base_delay: float = 2.0) -> dict:
    """Run ONE turn in an existing interview session and return what came back.

    Returns {session_id, tool_calls, final_text, composed}. `composed` is the parsed blocks JSON
    when the agent has finished, or None when it replied with a follow-up question (in final_text).
    Auto-creates the session if it's unknown (e.g. the server restarted and lost in-memory state).
    Retries transient Gemini errors, same policy as compose_day().
    """
    runner, svc = _ensure_runner()
    if not await _session_exists(svc, session_id):
        await svc.create_session(app_name=APP_NAME, user_id=_CONV_USER, session_id=session_id)

    for attempt in range(1, max_attempts + 1):
        try:
            result = await run_turn(runner, user_id=_CONV_USER, session_id=session_id,
                                    message=message)
            result["session_id"] = session_id
            result["composed"] = extract_blocks_json(result.get("final_text"))
            return result
        except Exception as e:
            if _is_transient(e) and attempt < max_attempts:
                await _backoff_sleep(e, attempt, retry_base_delay, max_attempts)
                continue
            raise


# --- demo / self-check ---
SAMPLE = dict(
    trigger="onboarding",
    age_months=9,
    day_description="I'm home with the baby. She naps mid-morning and after lunch. I get a "
                    "couple of hours when my mom takes her in the afternoon.",
    help_windows="14:00-16:00 (grandma)",
    goal="work on my DZA application",
    evening="bath around 18:30, bed by 19:30",
)


async def _amain() -> None:
    if os.getenv("GOOGLE_API_KEY"):
        print("Running compose_day() on a sample onboarding...\n")
        out = await compose_day(**SAMPLE)
        print("\nTools the model chose:", [c["name"] for c in out["tool_calls"]])
        print("\nAgent output:\n", out["final_text"])
    else:
        # No key: prove the scaffold constructs end-to-end without a model call.
        agent = build_compose_agent()
        skill = load_compose_skill()
        msg = format_parent_message(**SAMPLE)
        Runner(app_name=APP_NAME, agent=agent, session_service=InMemorySessionService())
        print("Construction self-check (no GOOGLE_API_KEY, no model call):")
        print(f"  compose agent built: {agent.name} on {MODEL}, {len(agent.tools)} toolset(s)")
        print(f"  skill method loaded: {len(skill)} chars (frontmatter stripped: "
              f"{not skill.startswith('---')})")
        print(f"  parent message formatted: {len(msg.splitlines())} lines")
        print("\nSet GOOGLE_API_KEY (see .env.example) to run the actual decide/observe loop.")


if __name__ == "__main__":
    asyncio.run(_amain())
