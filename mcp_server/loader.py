"""Deterministic age-keyed lookup over the curated knowledge JSON.

This is the heart of the facts discipline: the number that reaches the agent is
produced HERE, by code, from a curated file — never by the model.
"""
import json
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def load_domain(domain: str) -> dict:
    """Load one knowledge file, e.g. 'naps' -> knowledge/naps.json."""
    with open(KNOWLEDGE_DIR / f"{domain}.json", encoding="utf-8") as f:
        return json.load(f)


def band_for_age(domain: str, age_months: int) -> dict:
    """Return the matching age band (incl. source + tier), or a graceful out-of-range note.

    Deterministic: same age in -> same band out. No interpolation, no model.
    """
    data = load_domain(domain)
    for band in data["bands"]:
        if band["age_months_min"] <= age_months <= band["age_months_max"]:
            return {"framing": data.get("framing"), **band}
    return {"out_of_range": True, "age_months": age_months,
            "framing": data.get("framing"),
            "note": "No band for this age; do not guess — say guidance isn't available."}
