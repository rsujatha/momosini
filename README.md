# Momosini — Agent

A privacy-first daily organiser for new parents that structures the day around a baby's
developmental stage. It pairs a deterministic tracker app with **one ADK agent** and a **local
MCP knowledge server**, so the schedule adapts to the baby's sleep and milestones while every
developmental fact stays grounded in curated, sourced data. Kaggle "Vibecoding Agents" capstone.

> **Read next:** `ARCHITECTURE.md` (how the pieces fit) → `docs/DECISIONS.md` (why it's built this way).

## At a glance

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
  eval/ harness ──▶ proves the agent never invents a fact
```

**Onboarding is a conversation.** The tracker opens with a warm, one-question-at-a-time interview
(birthday → "tell me about your day" → agent-led follow-ups → composed day), driven by the agent
through `POST /converse`. The voice centres on the **parent's** wellbeing (it offers a *minimum day*
when they're overwhelmed); baby facts stay tool-grounded. See
`docs/PLAN-conversational-onboarding.md`.

**What it is, stated plainly:** 1 agent · 1 MCP server (2 tools) · 1 Skill · 1 deterministic app ·
1 eval harness. See `ARCHITECTURE.md` for the reasoning behind that count.

## How it works

- **The agent (ADK).** A single `LlmAgent` in `agent/` runs the show: it reads the parent's free
  text, decides which tools to call, asks a gentle follow-up only when a real gap remains, and
  composes the day. Its procedural method — the interview policy and the day-blocks contract — is a
  runtime-loadable **Agent Skill** (`agent/skills/compose-baby-day/`), kept separate from the
  system persona in `agent/instructions.py`.
- **The MCP server (facts).** `mcp_server/` exposes two deterministic tools, `get_nap_guidance` and
  `get_milestone_checkin`, over stdio. They read curated JSON in `knowledge/`, where every record is
  tagged with a source and an evidence tier. The model may generate *play ideas* (bounded by an
  infant-safety rule) but never originates a developmental number.
- **The tracker (UI).** `tracker/` is the deterministic front-end. It renders the agent's day-blocks
  JSON and runs `sanitizeWindows()` to guard against overlapping or zero-length blocks. The parent's
  schedule and the baby's birthday live only in the browser's `localStorage` — the backend stores
  nothing.
- **The web seam.** `web/app.py` (FastAPI) serves the tracker and the `/converse` and `/compose`
  endpoints, and spawns the MCP server as a local subprocess.
- **The eval harness.** `eval/` verifies the facts discipline — it fails if the agent ever states a
  developmental number that the tools didn't return, and checks the blocks JSON against the tracker's
  contract.

## Project layout

| Directory | What it is |
|---|---|
| `knowledge/` | curated developmental data (`naps.json`, `milestones.json`), sourced and evidence-tiered |
| `mcp_server/` | the local stdio MCP tool server (`get_nap_guidance`, `get_milestone_checkin`) |
| `agent/` | the single ADK agent, its instructions, and the `compose-baby-day` Skill |
| `web/` | FastAPI app — serves the tracker and the `/converse` · `/compose` endpoints |
| `tracker/` | the deterministic front-end (`mom-day-tracker.html`) |
| `eval/` | anti-hallucination + contract test harness (`pytest eval/`) |
| `deploy/` | Cloud Run deployment notes (the deploy `Dockerfile` lives at the repo root) |
| `docs/` | architecture, decisions, and planning notes |

## Quickstart (local)

```bash
cp .env.example .env          # then fill in your own key locally — never commit .env
pip install -r requirements.txt

python -m mcp_server.server   # (optional) smoke-test the tool server on its own
python -m agent.agent         # (optional) prove the agent sees the MCP tools, no model call
pytest eval/                  # deterministic facts + contract harness (4 passed, 1 skipped)

uvicorn web.app:app --reload  # run the app: open http://127.0.0.1:8000 for the conversation
```

### Choosing the model (`ADK_MODEL`)

Gemini is the default and the submission model.

- **Local (API key):** set `GOOGLE_API_KEY` and `GOOGLE_GENAI_USE_VERTEXAI=FALSE`.
- **Local (Vertex):** set `GOOGLE_GENAI_USE_VERTEXAI=TRUE` and run `gcloud auth application-default login`.
- **DeepSeek (optional, for dev):** any non-Gemini `ADK_MODEL` routes via LiteLLM —
  ```bash
  ADK_MODEL=deepseek/deepseek-chat
  DEEPSEEK_API_KEY=...            # and: pip install litellm
  ```

Leave `ADK_MODEL` blank (or a `gemini-*` value) to use Gemini. No code change needed either way.

### Optional checks

```bash
RUN_TONE_JUDGE=1 pytest eval/test_tone_judge.py   # LLM-as-judge for the persona/voice (uses a key)
python -m eval.smoke_two_turn                      # live two-turn agent run (needs a key + network)
```

## Deploy

The whole app — FastAPI web layer, the ADK agent, and the bundled stdio MCP server — ships as **one
container** (the `Dockerfile` at the repo root) and is deployed to **Google Cloud Run**. Because the
backend keeps interview sessions in memory and spawns the MCP server as a subprocess, it runs with
`--max-instances=1 --min-instances=1` to pin a live conversation to one warm instance. On Cloud Run
the agent reaches Gemini via Vertex AI using the service account's credentials (no API key to inject).
See `deploy/README.md` for the full step-by-step.
