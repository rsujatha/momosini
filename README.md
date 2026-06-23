# Mom Day Organiser — Agent

A privacy-first daily organiser for parents that structures the day around a baby's
developmental stage. A deterministic tracker app + one ADK agent + a local MCP knowledge
server. Kaggle "Vibecoding Agents" capstone.

> **New here? Read in this order:** this README → `ARCHITECTURE.md` → `docs/WORKPLAN.md`
> (who does what, in learning order) → `docs/DECISIONS.md` (why it's built this way).

## The whole project at a glance

```
parent types their day  ──▶  ┌──────────────────────────┐
                             │  AGENT (ADK, 1 of them)  │  ◀── loads compose-baby-day SKILL
 "is my baby behind?"   ──▶  │  decides · calls tools · │      (the *method*)
                             │  observes · asks · composes
                             └────────────┬─────────────┘
                                          │ McpToolset (stdio)
                                          ▼
                             ┌──────────────────────────┐
                             │  MCP SERVER (tools only)  │  get_nap_guidance(age_months)
                             │  deterministic lookups    │  get_milestone_checkin(...)
                             └────────────┬─────────────┘  (play = generated, not a tool)
                                          │ reads
                                          ▼
                             knowledge/*.json  (curated, sourced, tiered)

           agent emits blocks JSON ──▶ TRACKER (deterministic app, renders it)
           eval/ harness ──▶ proves the agent never invents a fact (not an agent)
```

**Count, stated plainly:** 1 agent · 1 MCP server (2 tools) · 1 Skill · 1 deterministic app ·
1 eval harness (infrastructure, not an agent). See `ARCHITECTURE.md` for why.

## Who owns what

| Directory | What it is | Owner | Learning goal |
|---|---|---|---|
| `knowledge/` | curated data + sources | **You review** | provenance discipline |
| `mcp_server/` | the tool layer | Collaborator | the MCP protocol |
| `agent/` | the ADK agent | Co-own | agent reasoning |
| `agent/instructions.py` | system prompt + facts enforcement | **You** | how prompts drive agents |
| `eval/` | anti-hallucination harness | Collaborator | verifying agent behaviour |
| `tracker/` | the deterministic app | **You** | (your existing code) |
| `deploy/` | container + Cloud Run | Co-own | deployability |

## Quickstart (local)

```bash
cp .env.example .env          # then fill in your own keys locally — never commit .env
pip install -r requirements.txt
python -m mcp_server.server   # smoke-test the tool server on its own
python -m agent.agent         # run the agent (spawns the MCP server via stdio)
pytest eval/                  # run the facts-discipline harness
```

> Class names in `agent/agent.py` (e.g. `McpToolset`, `StdioServerParameters`) must be
> checked against the **current** ADK docs at build time — the API moves.
