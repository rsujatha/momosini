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
import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import MODEL, build_mcp_toolset
from .instructions import SYSTEM_INSTRUCTION

APP_NAME = "mom-day-organiser"
SKILL_PATH = Path(__file__).resolve().parent / "skills" / "compose-baby-day" / "SKILL.md"


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
        model=MODEL,
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


async def compose_day(*, session_id: str | None = None, **inputs) -> dict:
    """One-shot entry: build the compose agent + runner, run a turn from structured inputs.

    Reuse the returned session_id with run_turn() to answer a clarifying question in the same
    session (the loop's continuation). Requires GOOGLE_API_KEY.
    """
    agent = build_compose_agent()
    session_service = InMemorySessionService()
    runner = Runner(app_name=APP_NAME, agent=agent, session_service=session_service)
    user_id = "local-parent"
    session_id = session_id or "compose-1"
    await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)

    message = format_parent_message(**inputs)
    result = await run_turn(runner, user_id=user_id, session_id=session_id, message=message)
    result["session_id"] = session_id
    return result


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
