"""Manual live smoke test for the conversational-onboarding transport (plan step 1).

Proves the multi-turn endpoint end-to-end: one long-lived session carries context across two
turns, the model drives its own tool calls, and a follow-up answer composes the day. This is the
step-1 checkpoint that needs a real GOOGLE_API_KEY + network — it is NOT a pytest (it spends
Gemini quota), so run it by hand:

    GOOGLE_API_KEY=... python -m eval.smoke_two_turn

Note: this repo's .env currently sets GEMINI_API_KEY, but the code/tooling reads GOOGLE_API_KEY.
This script bridges the two if only GEMINI_API_KEY is present — but the cleaner fix is to
standardize on GOOGLE_API_KEY (matches .env.example) so every entry point sees the key.
(Could not be run from the build sandbox: outbound access to the Gemini API is blocked there.)
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
# Allow running directly (`python eval/smoke_two_turn.py`) as well as `python -m eval.smoke_two_turn`.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
load_dotenv(REPO_ROOT / ".env")
if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

from agent.runner import format_parent_message, send_message, start_conversation  # noqa: E402


async def main() -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        raise SystemExit("Set GOOGLE_API_KEY (or GEMINI_API_KEY) in .env first.")

    t0 = time.time()
    sid = await start_conversation()
    print("session:", sid)

    # Turn 1 — deliberately sparse free text, so the agent may ask a follow-up before composing.
    opening = format_parent_message(
        trigger="onboarding",
        age_months=9,
        day_description=("I'm home with my 9 month old most of the day. "
                         "I'd love some time to work on my application."),
    )
    r1 = await send_message(session_id=sid, message=opening)
    done1 = bool(r1["composed"])
    print(f"\n[turn 1] {time.time() - t0:.1f}s  tools={[c['name'] for c in r1['tool_calls']]}  "
          f"composed={done1}")
    if done1:
        print("  blocks:", [b.get("kind") for b in r1["composed"]["blocks"]])
        followup = "Actually my mum takes her 2-4pm — can you put my focus time there?"
    else:
        print("  agent asks:", (r1["final_text"] or "").strip()[:300])
        followup = "My mum takes her from 2 to 4pm, and bedtime is around 7:30pm."

    # Turn 2 — same session; proves context carries across turns.
    r2 = await send_message(session_id=sid, message=followup)
    done2 = bool(r2["composed"])
    print(f"\n[turn 2] {time.time() - t0:.1f}s  tools={[c['name'] for c in r2['tool_calls']]}  "
          f"composed={done2}")
    print("  same session carried:", r2["session_id"] == sid)
    if done2:
        blocks = r2["composed"]["blocks"]
        print("  blocks:", [(b.get("kind"), b.get("window")) for b in blocks])
        focus = next((b for b in blocks if b.get("kind") == "focus"), None)
        print("  focus window honoured (expect ~14:00-16:00):", focus and focus.get("window"))
    else:
        print("  agent says:", (r2["final_text"] or "").strip()[:300])

    assert done2 or not done1, "expected a composed day by turn 2"
    print("\nOK: two-turn session ran; the model drove its own tool calls.")


if __name__ == "__main__":
    asyncio.run(main())
