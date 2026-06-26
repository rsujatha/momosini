# Work plan — ordered so the collaborator *learns agentic AI* as she builds

Each chunk: what she'll learn · what it unblocks · rough timebox · your review checkpoint.
Dependency order is also bottom-up build order, so the project assembles as she learns.

## Status — as of 2026-06-25 (commit `d1a402d`)

The base arcs (MCP server, agent↔MCP wiring, agent loop, eval harness) are in. On top of them, a
**conversational-onboarding** stream is now complete — see `docs/PLAN-conversational-onboarding.md`
for the full scope. Summary of what's built and committed:

- **Conversational onboarding (replaces the static form).** One question at a time: birthday →
  "tell me about your day" free text → agent-led follow-ups → composed day. UI in
  `tracker/mom-day-tracker.html`; backend `POST /converse` (multi-turn, session-held) in
  `web/app.py` + `agent/runner.py`.
- **Persona + interview policy (protected files).** Parent-wellbeing clinician voice with pediatric
  grounding; clarifying-question cap raised one → **5–6**, one at a time. In `agent/instructions.py`
  + `agent/skills/compose-baby-day/SKILL.md`. Logged in `docs/DECISIONS.md`.
- **Env-switchable model.** Gemini default; `ADK_MODEL=deepseek/deepseek-chat` routes via `LiteLlm`
  (`resolve_model` in `agent/agent.py`). Verified live on DeepSeek.
- **Deterministic render guard.** `sanitizeWindows()` in the tracker drops zero-length/duplicate
  time slots.
- **Eval extended.** Multi-turn facts-trace + hallucination-detector, blocks-contract checks, and an
  opt-in LLM-as-judge tone test (`RUN_TONE_JUDGE=1`). `pytest eval/` = 4 passed, 1 skipped.

**Open / not done:** still on free-tier vs paid-Gemini decision for submission; deployment (the
`deploy/Dockerfile` is a skeleton — its CMD runs the self-check, not the web server, and it bakes
`.env` in); video + writeup. A quick-share path (Render free tier + keep-alive ping) was discussed
but not built. Protected-file diffs went in via the `d1a402d` auto-commit and are worth a review.

## Collaborator's arc (the agentic-AI learning path)

### 1. MCP server  (`mcp_server/`) — learn the tool layer
- Build the stdio server + shared loader + 3 deterministic tools over `knowledge/*.json`.
- Learns: the MCP protocol, tool schemas, deterministic lookups.
- Unblocks: everything downstream (the agent needs tools to call).
- Timebox: ~4–6h. Checkpoint: tools callable, tests green.

### 2. Agent ↔ MCP wiring  (`agent/agent.py`, McpToolset) — learn agent-meets-tools
- Connect the agent to the server; watch the model *choose* to call a tool.
- Learns: how an agent discovers and invokes external tools.
- Timebox: ~3–4h. Checkpoint: agent lists + calls a tool live.

### 3. The agent loop  (`agent/agent.py`) — learn agent reasoning
- The decide → call → observe → loop + the clarifying-question flow.
- Learns: what makes an agent an agent vs a pipeline (the core idea).
- Co-owned: she builds mechanics; Sujatha owns `instructions.py`.
- Timebox: ~4–6h. Checkpoint: composes a day end-to-end.

### 4. Eval harness  (`eval/`) — learn to verify agent behaviour
- Deterministic facts-trace test; optional LLM-as-judge for tone.
- Learns: agent evaluation — the bridge from her data-science instincts to agentic AI.
- Timebox: ~3–4h. Checkpoint: a hallucinated fact is caught by a failing test.

## Sujatha's track (kept, not delegated)
- `agent/instructions.py` — the system prompt + facts enforcement (learn: prompts → behaviour).
- `tracker/` integration — wire agent output into the existing app.
- `knowledge/` review — provenance gate on milestone data (play is generated, not curated).
- Founder story, writeup, video, final assembly.

## Sequencing against the real calendar
- **Now → Jun 28:** DZA application is higher-stakes — protect it. In the cracks, curate
  milestone data (low-continuous-focus, fragment-friendly; play is generated, no curation). Collaborator starts arc 1–2.
- **Jun 28 → Jul 3:** build blitz — arcs 3–4, integration, instruction layer, deploy.
- **Jul 3 → Jul 6:** video + writeup (these don't compress; reserve the days).
