# Architecture

Three layers, deliberately separated so each does one job and only one of them is an agent.

## 1. Deterministic tracker (`tracker/`)
Plain app code: day-blocks, checkboxes, streaks. No model. This is most of what the user
touches, and it is intentionally *not* agentic — predictable beats clever for a daily tool.

## 2. The agent (`agent/`) — the ONE agent
The only place the model drives control flow. On onboarding or a nap-transition restructure
it: reads the goal → decides which knowledge tools to call → observes results → asks one
clarifying question if needed → composes the day's blocks. It loads the `compose-baby-day`
Skill for the *method*; it gets *facts* only from tools.

**Litmus (why it's an agent):** the model chooses the tool calls and loops toward a goal.
If we had written the exact call sequence by hand, it would be a pipeline, not an agent.

## 3. The MCP server (`mcp_server/`) — tools, not an agent
A local stdio subprocess exposing two deterministic lookups over `knowledge/*.json`.
Bundled in the deployed container; no network, small attack surface, private by design.

## The eval harness (`eval/`) — infrastructure, not an agent
Verifies a property ("every developmental fact in the output traces to a tool result").
Deterministic on purpose — a model-based checker would reintroduce the non-determinism we
built it to catch. Soft qualities (tone) may optionally use LLM-as-judge; still not an agent.

## Data flow
```
free text / question
   └─▶ agent (LlmAgent) ──McpToolset(stdio)──▶ mcp_server ──reads──▶ knowledge/*.json
        └─ composes blocks JSON ──▶ tracker renders
```

## The contract (the seam between owners)
The interface that lets parallel work happen without constant coordination:
- **Data schema:** `knowledge/SOURCES.md` + the JSON shape in `knowledge/naps.json`.
- **Tool contract:** signatures in `mcp_server/tools/`. Inputs are `age_months` only —
  never personal data. Outputs are typical ranges with a `source` and `tier`.
- **Age-keyed lookup (shared mechanism, not shared edges):** every domain is keyed by
  `age_months` and resolved by the same age→band lookup, but band *granularity is per-domain*.
  Naps use coarse bands; milestones use one band per source age (finer, because infant
  development moves faster than nap structure changes). Domains share the lookup, not identical
  band boundaries — see `docs/DECISIONS.md` ("Milestone bands finer than nap bands").
- **Agent output contract:** the blocks JSON the tracker consumes (see
  `agent/skills/compose-baby-day/SKILL.md`).

## The one rule that crosses every layer
The model never originates a developmental FACT. Nap counts and milestone ages come from a
tool call — the agent phrases, it does not invent. Play activities are the one exception:
they are GENERATED from the retrieved milestones (a game is not a fact), bounded by an
infant-safety fence in agent/instructions.py. Facts retrieved; activities generated from
facts. This is the differentiator.
