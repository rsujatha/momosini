"""Milestone check-in tool. Input is age_months ONLY."""
from ..loader import band_for_age


def get_milestone_checkin(age_months: int) -> dict:
    """Typical developmental framing for an age, with source + tier (curated)."""
    return band_for_age("milestones", age_months)
