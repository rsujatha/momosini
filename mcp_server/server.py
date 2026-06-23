"""Local stdio MCP server exposing the three curated knowledge tools.

Bundled in the deployed container. No network. Verify the exact MCP/FastMCP
registration API against current ADK docs at build time.
"""
from .tools.naps import get_nap_guidance
from .tools.milestones import get_milestone_checkin

# TODO (collaborator, learning goal: the MCP protocol):
#   Register the three functions above as MCP tools over stdio using the
#   current FastMCP/MCP API, then run the server on stdin/stdout.
#   Each tool takes age_months: int and returns the curated dict.

TOOLS = [get_nap_guidance, get_milestone_checkin]

if __name__ == "__main__":
    # Smoke test without the protocol layer:
    print(get_nap_guidance(10))
