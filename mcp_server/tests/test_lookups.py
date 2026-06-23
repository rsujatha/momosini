"""Deterministic-lookup tests — the facts layer must be exact and repeatable."""
from mcp_server.tools.naps import get_nap_guidance


def test_band_is_deterministic():
    assert get_nap_guidance(10) == get_nap_guidance(10)


def test_known_band_has_source_and_tier():
    band = get_nap_guidance(10)
    assert "source" in band and "tier" in band


def test_out_of_range_does_not_guess():
    band = get_nap_guidance(999)
    assert band.get("out_of_range") is True
