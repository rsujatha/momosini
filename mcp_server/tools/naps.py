"""Nap guidance tool. Input is age_months ONLY — never personal data."""
from ..loader import band_for_age


def get_nap_guidance(age_months: int) -> dict:
    """Typical nap count / daytime-sleep range for an age, with source + tier.

    Returns a curated band straight from knowledge/naps.json. The caller (agent)
    must phrase this as typical-not-prescriptive and must not add numbers of its own.
    """
    return band_for_age("naps", age_months)
