"""OPTIONAL LLM-as-judge for SOFT qualities only (the persona/voice).

This is the one place a model grades output — and it's an eval FUNCTION, not an agent (no loop,
no tools, it scores once). Hard facts stay deterministic in test_facts_trace.py.

OFF by default so the normal suite stays deterministic and spends no API quota. To run it:

    RUN_TONE_JUDGE=1 python -m pytest eval/test_tone_judge.py -q

It uses LiteLLM, so it works with whatever provider key is in your .env. The judge model defaults
to deepseek/deepseek-chat; override with JUDGE_MODEL (e.g. gemini-2.5-flash). Needs `pip install
litellm` and the matching key (DEEPSEEK_API_KEY / GOOGLE_API_KEY).
"""
import json
import os
import re
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"

RUBRIC = """You grade the VOICE of an onboarding assistant for a day planner used by parents of a
baby. Judge ONLY the assistant's (role: agent) messages. PASS only if ALL hold:
1. It centers the PARENT'S wellbeing — warm, calm, authoritative; never cold/clinical, never chirpy.
2. If the parent signals overwhelm, exhaustion, or illness, it offers a lighter "minimum day".
3. It asks ONE question at a time, not a barrage.
4. It frames baby facts as typical ranges ("many babies around this age..."), never as targets or
   commands the baby/parent must hit.
5. It never says it is "about to build the day" without doing so (no narrate-and-stop).
Reply with STRICT JSON only: {"pass": true|false, "reasons": "<one short sentence>"}."""


def _enabled() -> bool:
    return os.getenv("RUN_TONE_JUDGE") == "1"


@pytest.mark.skipif(
    not _enabled(),
    reason="Optional tone judge. Set RUN_TONE_JUDGE=1 (and a provider key) to run.",
)
def test_persona_voice_passes_judge():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    import litellm

    model = os.getenv("JUDGE_MODEL", "deepseek/deepseek-chat")
    transcript = json.loads((FIXTURES / "tone_transcript.json").read_text(encoding="utf-8"))["transcript"]
    convo = "\n".join(f"{m['role']}: {m['text']}" for m in transcript)

    resp = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": RUBRIC},
            {"role": "user", "content": "Transcript:\n" + convo},
        ],
        temperature=0,
    )
    text = resp["choices"][0]["message"]["content"]
    match = re.search(r"\{.*\}", text, re.S)
    assert match, f"judge did not return JSON: {text!r}"
    verdict = json.loads(match.group(0))
    assert verdict.get("pass") is True, f"tone judge failed: {verdict.get('reasons')}"
