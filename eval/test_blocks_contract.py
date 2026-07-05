"""Deterministic checks on the composed-day CONTRACT — the invariants steps 3 & 4 hardened.

These are model-free (no API, no quota). They lock in the rules so a prompt tweak or a model swap
can't quietly regress them:
  - kind is one of the allowed values
  - a nap never carries a clock window (naps are untimed anchors)
  - no zero-length window (start == end)
  - no two blocks share the same time slot
  - the minimum-day set always contains the focus block

The tracker enforces the window rules at runtime too (sanitizeWindows in mom-day-tracker.html);
this is the Python-side regression net for the same contract.
"""
import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ALLOWED_KINDS = {"focus", "her_time", "with_baby", "together", "nap"}


def contract_violations(blocks: list[dict]) -> list[str]:
    problems: list[str] = []
    seen_slots: dict[tuple, str] = {}
    for b in blocks:
        bid = b.get("id", "?")
        kind = b.get("kind")
        if kind not in ALLOWED_KINDS:
            problems.append(f"bad kind '{kind}' on {bid}")
        w = b.get("window")
        if kind == "nap" and w:
            problems.append(f"nap has a window: {bid}")
        if w:
            start, end = w.get("start"), w.get("end")
            if not start or not end:
                problems.append(f"incomplete window on {bid}")
            elif start == end:
                problems.append(f"zero-length window on {bid}")
            else:
                slot = (start, end)
                if slot in seen_slots:
                    problems.append(f"duplicate slot {start}-{end}: {bid} & {seen_slots[slot]}")
                else:
                    seen_slots[slot] = bid
    min_blocks = [b for b in blocks if b.get("show_in_minimum_day")]
    if min_blocks and not any(b.get("is_focus") or b.get("kind") == "focus" for b in min_blocks):
        problems.append("minimum-day set has no focus block")
    return problems


def test_composed_fixtures_honor_contract():
    fixtures = list(FIXTURES.glob("composed_*.json"))
    assert fixtures, "no composed_*.json fixtures found"
    for fx in fixtures:
        blocks = json.loads(fx.read_text(encoding="utf-8"))["blocks"]
        assert not contract_violations(blocks), f"{fx.name}: {contract_violations(blocks)}"


def test_contract_catches_each_violation():
    """A deliberately broken day must trip every rule — proving the checks actually detect them."""
    bad = [
        {"id": "n", "kind": "nap", "window": {"start": "09:00", "end": "10:00"}},   # nap w/ window
        {"id": "f", "kind": "focus", "window": {"start": "14:00", "end": "16:00"},
         "is_focus": True, "show_in_minimum_day": False},
        {"id": "d", "kind": "with_baby", "window": {"start": "14:00", "end": "16:00"}},  # dup slot
        {"id": "z", "kind": "her_time", "window": {"start": "19:30", "end": "19:30"}},   # zero-length
        {"id": "x", "kind": "weird"},                                                    # bad kind
        {"id": "t", "kind": "together", "show_in_minimum_day": True},                    # min-day, no focus
    ]
    v = contract_violations(bad)
    assert any("nap has a window" in p for p in v)
    assert any("duplicate slot" in p for p in v)
    assert any("zero-length" in p for p in v)
    assert any("bad kind" in p for p in v)
    assert any("minimum-day set has no focus block" in p for p in v)
