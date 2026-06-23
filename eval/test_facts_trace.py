"""Anti-hallucination harness — DETERMINISTIC. The differentiator, made checkable.

Property: every developmental number in the agent's output must trace to a value the
tools actually returned on that run. A model-based judge is deliberately NOT used here —
it would reintroduce the non-determinism we're trying to catch.
"""
import re
import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def numbers_in(text: str) -> set[str]:
    return set(re.findall(r"\d+", text))


def load_run(name: str) -> dict:
    """A recorded run: {'tool_returns': [...], 'agent_output': '...'}."""
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_every_output_number_traces_to_a_tool_return():
    for fixture in FIXTURES.glob("*.json"):
        run = json.loads(fixture.read_text(encoding="utf-8"))
        tool_numbers = numbers_in(json.dumps(run["tool_returns"]))
        out_numbers = numbers_in(run["agent_output"])
        # allow trivially-safe numbers (clock times the parent gave); refine the allow-list
        # as needed. The core assertion: no developmental number appears that a tool didn't return.
        invented = out_numbers - tool_numbers - set(run.get("allowed_user_numbers", []))
        assert not invented, f"{fixture.name}: numbers not from any tool: {invented}"
