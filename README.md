# Mom Day Organiser — Agent

A privacy-first daily organiser for parents that structures the day around a baby's
developmental stage. A deterministic tracker app + one ADK agent + a local MCP knowledge
server. Kaggle "Vibecoding Agents" capstone.

> **New here? Read in this order:** this README → `ARCHITECTURE.md` → `docs/WORKPLAN.md`
> (who does what, in learning order) → `docs/DECISIONS.md` (why it's built this way).

## The whole project at a glance

```
parent's day, in their     ──▶ ┌──────────────────────────┐
own words (a conversation,     │  AGENT (ADK, 1 of them)  │  ◀── loads compose-baby-day SKILL
 one question at a time)        │  decides · calls tools · │      (the *method*)
 "is my baby behind?"      ──▶  │  observes · interviews · composes
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

  web/app.py  ──▶  POST /converse (multi-turn interview)  ·  POST /compose (one-shot)
  agent emits blocks JSON ──▶ TRACKER (deterministic app; sanitizeWindows guards the contract)
  eval/ harness ──▶ proves the agent never invents a fact (not an agent)
```

**Onboarding is a conversation.** The tracker opens with a warm, one-question-at-a-time interview
(birthday → "tell me about your day" → agent-led follow-ups → composed day), driven by the agent
through `POST /converse`. The voice centres on the **parent's** wellbeing (offers a *minimum day*
when they're overwhelmed); baby facts stay tool-grounded. See
`docs/PLAN-conversational-onboarding.md`.

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

python -m mcp_server.server   # (optional) smoke-test the tool server on its own
python -m agent.agent         # (optional) prove the agent sees the MCP tools, no model call
pytest eval/                  # deterministic facts + contract harness (4 passed, 1 skipped)

uvicorn web.app:app --reload  # run the app: open http://127.0.0.1:8000 for the conversation
```

### Choosing the model (`ADK_MODEL`)

Gemini (Google AI Studio) is the **default** and the submission model — set `GOOGLE_API_KEY`.
To develop without hitting Gemini's free-tier daily cap, switch to DeepSeek in `.env`:

```bash
ADK_MODEL=deepseek/deepseek-chat   # any non-Gemini value routes via LiteLlm
DEEPSEEK_API_KEY=...               # and: pip install litellm
```

Leave `ADK_MODEL` blank (or a `gemini-*` value) to use Gemini. No code change needed either way.

### Optional checks

```bash
RUN_TONE_JUDGE=1 pytest eval/test_tone_judge.py   # LLM-as-judge for the persona/voice (uses a key)
python -m eval.smoke_two_turn                      # live two-turn agent run (needs a key + network)
```

> Class names in `agent/agent.py` (e.g. `McpToolset`, `StdioServerParameters`) must be
> checked against the **current** ADK docs at build time — the API moves.
>
> **Deploy note:** the backend holds in-memory interview sessions and spawns the MCP server as a
> subprocess, so it needs a persistent container host (Render/Fly/Cloud Run/Railway), **not**
> serverless (Vercel is fine only for a static front-end). `deploy/Dockerfile` is a skeleton —
> its CMD must be changed to serve `uvicorn web.app:app` before it will run the app.
