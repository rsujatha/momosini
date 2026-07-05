"""Deterministic-lookup tests — the facts layer must be exact and repeatable.

These test the lookup functions directly (the facts discipline). The MCP protocol layer
is exercised separately by the stdio smoke test.
"""
import pytest

from mcp_server.tools.naps import get_nap_guidance
from mcp_server.tools.milestones import get_milestone_checkin

TOOLS = [get_nap_guidance, get_milestone_checkin]


# --- determinism: same age in -> same band out, no model in the path ---
@pytest.mark.parametrize("tool", TOOLS)
def test_band_is_deterministic(tool):
    assert tool(10) == tool(10)


# --- every in-range band carries provenance (no bare numbers) ---
@pytest.mark.parametrize("tool", TOOLS)
def test_known_band_has_source_and_tier(tool):
    band = tool(10)
    assert "source" in band and "tier" in band


# --- out of range: say so, never guess ---
@pytest.mark.parametrize("tool", TOOLS)
def test_out_of_range_does_not_guess(tool):
    band = tool(999)
    assert band.get("out_of_range") is True
    # and it must not smuggle in a fabricated figure
    assert "source" not in band


# --- nap-specific content sanity ---
def test_nap_band_shape():
    band = get_nap_guidance(10)
    assert band["age_months_min"] <= 10 <= band["age_months_max"]
    assert "total_sleep_h" in band


# --- milestone-specific: all seven domains present and non-empty ---
def test_milestone_band_has_all_domains():
    band = get_milestone_checkin(9)
    domains = ["gross_motor", "fine_motor", "self_help", "problem_solving",
               "social_emotional", "receptive_language", "expressive_language"]
    for d in domains:
        assert band["milestones"][d], f"{d} should be non-empty"


# --- finer milestone bands: 9mo and 12mo resolve to DIFFERENT bands ---
def test_milestone_bands_are_fine_grained():
    assert get_milestone_checkin(9)["age_label"] != get_milestone_checkin(12)["age_label"]


# --- framing travels with every band so the caller can phrase it safely ---
@pytest.mark.parametrize("tool", TOOLS)
def test_framing_present(tool):
    assert tool(6).get("framing")
