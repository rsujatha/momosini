# Build plan & status

How Momosini was assembled, in dependency order, plus current status. Bottom-up: each layer
unblocks the next.

## Status — as of 2026-06-25 (commit `d1a402d`)

The base layers (MCP server, agent↔MCP wiring, agent loop, eval harness) are in. On top of them, a
**conversational-onboarding** stream is complete — see `docs/PLAN-conversational-onboarding.md`
for the full scope. What's built and committed:

- **Conversational onboarding (replaces the static form).** One question at a time: birthday →
  "tell me about your day" free text → agent-led follow-ups → composed day. UI in
  `tracker/mom-day-tracker.html`; backend `POST /converse` (multi-turn, session-held) in
  `web/app.py` + `agent/runner.py`.
- **Persona + interview policy.** Parent-wellbeing clinician voice with pediatric grounding;
  clarifying-question cap set to **5–6**, one at a time. In `agent/instructions.py` +
  `agent/skills/compose-baby-day/SKILL.md`. Logged in `docs/DECISIONS.md`.
- **Env-switchable model.** Gemini default; `ADK_MODEL=deepseek/deepseek-chat` routes via `LiteLlm`
  (`resolve_model` in `agent/agent.py`). Verified live on DeepSeek.
- **Deterministic render guard.** `sanitizeWindows()` in the tracker drops zero-length/duplicate
  time slots.
- **Eval extended.** Multi-turn facts-trace + hallucination-detector, blocks-contract checks, and an
  opt-in LLM-as-judge tone test (`RUN_TONE_JUDGE=1`). `pytest eval/` = 4 passed, 1 skipped.
- **Deployed.** Packaged as one container (root `Dockerfile`) and deployed to Google Cloud Run
  (`--max-instances=1 --min-instances=1`, Gemini via Vertex AI). See `deploy/README.md`.

## How it was built (in dependency order)

### 1. MCP server (`mcp_server/`) — the tool layer
The stdio server + shared loader + deterministic tools over `knowledge/*.json`. Everything
downstream depends on it, since the agent needs tools to call. Checkpoint: tools callable, tests
green.

### 2. Agent ↔ MCP wiring (`agent/agent.py`, McpToolset) — agent meets tools
Connect the agent to the server so the model *chooses* to call a tool. Checkpoint: the agent lists
and calls a tool live, with no model call needed to prove the seam.

### 3. The agent loop (`agent/agent.py`) — the reasoning
The decide → call → observe loop plus the clarifying-question flow. This is what makes it an agent
rather than a fixed pipeline. Checkpoint: composes a day end-to-end.

### 4. Eval harness (`eval/`) — verifying behaviour
Deterministic facts-trace test plus an optional LLM-as-judge for tone. Checkpoint: a hallucinated
fact is caught by a failing test.

### 5. Onboarding, persona & deploy
The conversational interview, the parent-wellbeing persona and interview policy in
`agent/instructions.py` + the `compose-baby-day` Skill, tracker integration, `knowledge/` provenance
review, and the Cloud Run deployment.
