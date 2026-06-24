# agent — the one agentic flow (ADK)

A single ADK `LlmAgent` wired to the local stdio MCP server (`mcp_server/`) via `McpToolset`.
The model decides when to call `get_nap_guidance` / `get_milestone_checkin`; it never invents a
developmental number. Play activities are the one thing it *generates* (from the milestones the
tool returns), under the safety fence in `instructions.py`.

## Files
- `instructions.py` — the system prompt + facts discipline. **OWNED BY SUJATHA**; reviewed, not
  edited casually. `agent.py` imports `SYSTEM_INSTRUCTION` from it.
- `agent.py` — the wiring: `build_agent()` (live `LlmAgent` + `McpToolset`) and
  `list_mcp_tools()` (proves the agent↔MCP seam with no model call).
- `skills/compose-baby-day/SKILL.md` — the compose/restructure method the agent loads on demand.

## Verify the seam — no API key needed
```bash
pip install -r requirements.txt
python -m agent.agent
```
Spawns the MCP server, lists the two tools the agent can see, and constructs the `LlmAgent`.
This is the arc-2 checkpoint: the agent discovers and can call the server's tools live, with no
Gemini call.

## Run the model-driven loop — needs a key (arc 3)
The decide → call → observe → loop fires the model, so it needs a Gemini key:
```bash
cp .env.example .env          # then put your Google AI Studio key in GOOGLE_API_KEY
# (.env is git-ignored — never commit the key)
```
Then drive `build_agent()` with the ADK runner. Optional: `ADK_MODEL` overrides the default
(`gemini-2.0-flash`) if you want a different free-tier model.

## Status
- **Arc 2 (this) — done:** real `LlmAgent` + real `McpToolset`, seam verified.
- **Arc 3 — next:** the agent loop + clarifying-question flow + composing a day end-to-end
  (co-owned; `instructions.py` stays Sujatha's). See `docs/WORKPLAN.md`.
