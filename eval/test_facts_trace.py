"""Anti-hallucination harness — DETERMINISTIC. The differentiator, made checkable.

Property: every developmental number in the agent's output must trace to a value the tools
actually returned. A model-based judge is deliberately NOT used here — it would reintroduce the
non-determinism we're trying to catch. (Tone, a soft quality, is the one model-graded thing, in
test_tone_judge.py.)

Handles BOTH fixture shapes:
  - single-shot:  {tool_returns:[...], agent_output:"...", allowed_user_numbers:[...]}
  - multi-turn:   {turns:[{tool_returns:[...], output:"..."}, ...], allowed_user_numbers:[...]}
For a multi-turn session, a number in a later turn is justified if any tool returned it on that
turn OR an earlier one (tools stay in the model's context across the interview), so we check each
turn's output against the cumulative tool returns up to and including that turn.
"""
import json
import re
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def numbers_in(text: str) -> set[str]:
    return set(re.findall(r"\d+", text))


def _turns(run: dict) -> list[tuple[list, str]]:
    """Normalise either fixture shape to [(tool_returns, output), ...]."""
    if "turns" in run:
        return [(t.get("tool_returns", []), t.get("output", "")) for t in run["turns"]]
    return [(run.get("tool_returns", []), run.get("agent_output", ""))]


def invented_numbers(run: dict) -> set[str]:
    """Numbers stated in any turn's output that no tool justified (cumulatively) and that weren't
    user-supplied (clock times the parent gave). Empty set == clean: no fabricated facts."""
    allowed = set(run.get("allowed_user_numbers", []))
    cumulative_tool: set[str] = set()
    invented: set[str] = set()
    for tool_returns, output in _turns(run):
        cumulative_tool |= numbers_in(json.dumps(tool_returns))
        invented |= numbers_in(output) - cumulative_tool - allowed
    return invented


def test_every_output_number_traces_to_a_tool_return():
    """Every recorded run (single-shot or multi-turn) must be free of fabricated numbers."""
    fixtures = list(FIXTURES.glob("*_run.json"))
    assert fixtures, "no *_run.json fixtures found"
    for fx in fixtures:
        run = json.loads(fx.read_text(encoding="utf-8"))
        bad = invented_numbers(run)
        assert not bad, f"{fx.name}: numbers not traceable to any tool return: {sorted(bad)}"


def test_harness_catches_a_hallucinated_number():
    """The checkpoint from the brief: a hallucinated fact is caught. A fabricated nap count (5)
    that no tool returned must be flagged — proving the harness actually detects hallucination."""
    bad_run = {
        "tool_returns": [{"tool": "get_nap_guidance", "result": {"typical_naps": "2"}}],
        "agent_output": "Your baby should now be on 5 naps a day.",
        "allowed_user_numbers": [],
    }
    assert "5" in invented_numbers(bad_run)
