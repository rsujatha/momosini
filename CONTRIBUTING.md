# Working together

Lightweight on purpose — there are two of us and a deadline.

## Flow
- `main` is always runnable. Don't push to it directly.
- One short-lived branch per work item (name it after the `docs/WORKPLAN.md` task).
- Small PRs. Review each other's. Merge when the Definition of Done is met.

## Two review gates (these are non-negotiable, everything else is light)
1. **Curation** — any change under `knowledge/` is reviewed for provenance: every figure
   has a source and a `tier` ([A] consensus / [B] research / [C] convention). No bare numbers.
2. **Instruction layer** — `agent/instructions.py` is reviewed by Sujatha. It's where the
   facts-discipline lives; it doesn't get changed casually.

## Definition of Done
- `mcp_server/`: 2 tools callable (nap + milestone; play is generated, not a tool — see
  `docs/DECISIONS.md`), lookups deterministic, `pytest mcp_server/tests` green.
- `agent/`: real `LlmAgent` instantiated + `McpToolset` wired + loop runs (not import-only).
- `eval/`: facts-trace test passes against recorded runs.
- Each PR: updates the relevant doc if it changes behaviour.

## Secrets (also our Security concept)
- Never commit keys. `.env` is git-ignored. `.env.example` holds key *names* only.
- The agent reads keys from the environment, not from code.

## Before you start a task
Agree the contract first (schema + tool signatures). That one document is what lets the
MCP server and the data curation proceed in parallel without waiting on each other.
