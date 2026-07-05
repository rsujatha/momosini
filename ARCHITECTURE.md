# Architecture

Three layers, deliberately separated so each does one job and only one of them is an agent.

## 1. Deterministic tracker (`tracker/`)
Plain app code: day-blocks, checkboxes, streaks. No model. This is most of what the user
touches, and it is intentionally *not* agentic — predictable beats clever for a daily tool.

## 2. The agent (`agent/`) — the ONE agent
The only place the model drives control flow. On onboarding or a nap-transition restructure
it: reads the goal → decides which knowledge tools to call → observes results → runs a short
**interview** (one question at a time, up to 5–6 follow-ups, only when they change the day) →
composes the day's blocks. It loads the `compose-baby-day` Skill for the *method*; it gets
*facts* only from tools.

**Persona:** the voice is a warm, authoritative clinician centred on the **parent's** wellbeing
(offers a *minimum day* when the parent sounds overwhelmed/unwell), while everything about the
**baby** stays pediatrically grounded in tool facts. Lives in `agent/instructions.py`; the 5–6
question cap and the "ask one question OR emit the day each turn" rule live there + in the Skill.

**Model is env-switchable (`ADK_MODEL`).** Gemini is the default and the documented submission
model (a bare model string → ADK's native Gemini path). Any non-Gemini value (e.g.
`deepseek/deepseek-chat`) is routed through ADK's `LiteLlm` wrapper by `resolve_model()` in
`agent/agent.py` — used for dev when Gemini's free-tier daily cap gets in the way. Switching is a
one-line `.env` change; no code edit.

**Litmus (why it's an agent):** the model chooses the tool calls and loops toward a goal.
If we had written the exact call sequence by hand, it would be a pipeline, not an agent.

## 3. The MCP server (`mcp_server/`) — tools, not an agent
A local stdio subprocess exposing two deterministic lookups over `knowledge/*.json`.
Bundled in the deployed container; no network, small attack surface, private by design.

## The eval harness (`eval/`) — infrastructure, not an agent
Verifies a property ("every developmental fact in the output traces to a tool result").
Deterministic on purpose — a model-based checker would reintroduce the non-determinism we
built it to catch. Soft qualities (tone) may optionally use LLM-as-judge; still not an agent.

## The web seam (`web/app.py`) — local glue, two endpoints
The FastAPI app serves the tracker at `/` and exposes the agent:
- **`POST /converse`** — the conversational onboarding. One turn at a time; returns either the
  agent's next question (`done:false`) or the composed day (`done:true`). It holds a long-lived
  in-memory ADK session keyed by `session_id`, so the interview carries context across turns
  (`start_conversation` / `send_message` in `agent/runner.py`). This statefulness is why the
  backend needs a persistent container host, not serverless (see `deploy/`).
- **`POST /compose`** — the original one-shot path (all fields at once); still supported.

Transient Gemini errors (503 overload / 429) self-heal via exponential backoff that also honors
the server's suggested retry delay (`_backoff_sleep` in `runner.py`).

## Data flow
```
parent's day (free text)  ─POST /converse─▶ agent (LlmAgent) ──McpToolset(stdio)──▶ mcp_server ──reads──▶ knowledge/*.json
   one question at a time  ◀── interview ──┘   └─ composes blocks JSON ──▶ tracker renders (sanitizeWindows guards the contract)
```

The tracker's `applyComposedDay` runs `sanitizeWindows()` before rendering — a deterministic guard
that drops zero-length and duplicate time slots no matter what the model emits, so two blocks can
never share a clock slot.

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
