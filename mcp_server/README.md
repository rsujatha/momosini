# mcp_server — local stdio knowledge server

Two deterministic, age-keyed lookup tools over `knowledge/*.json`, exposed via MCP (FastMCP)
over **stdio**. No network, no inbound access; the agent spawns this as a subprocess and talks
MCP on stdin/stdout. This is the facts layer — the developmental numbers reach the agent from
*here* (code, from curated files), never from the model.

## Tools
- `get_nap_guidance(age_months: int) -> dict` — typical nap/sleep band + source + tier.
- `get_milestone_checkin(age_months: int) -> dict` — typical milestones by domain + source + tier.

> Two tools, not three: play activities are *generated* by the agent from the milestones this
> server returns, not served as a tool (see `docs/DECISIONS.md`). `CONTRIBUTING.md`'s "3 tools"
> predates that decision.

## Layout
- `loader.py` — the age→band lookup (deterministic; one age in, one band out, or a no-guess note).
- `tools/naps.py`, `tools/milestones.py` — thin wrappers naming the contract.
- `server.py` — the MCP protocol layer: registers the tools (with their anti-hallucination
  descriptions) and runs the stdio loop.

## Run
```bash
pip install -r requirements.txt          # needs mcp==1.28.0
python -m mcp_server.server               # starts the stdio server (speaks MCP, not for humans)
```

## Verify
```bash
pytest mcp_server/tests -q                # deterministic lookup tests
python -m mcp_server.smoke_stdio          # live end-to-end: spawn server, list + call both tools
```
Definition of Done (per `CONTRIBUTING.md`): tools callable, lookups deterministic, pytest green.
