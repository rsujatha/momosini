"""OPTIONAL: LLM-as-judge for SOFT qualities only (tone warmth, gentleness, non-prescriptive).

This is the one place a model grades output — and it's an eval FUNCTION, not an agent
(no loop, no tools, scores once). Hard facts stay in test_facts_trace.py.
"""
import pytest

pytest.skip("Optional tone judge — enable once a judge model + rubric are wired.",
            allow_module_level=True)
