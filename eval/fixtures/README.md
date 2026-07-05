# Fixtures = recorded agent runs

Each file captures a recorded run for the deterministic eval harness (`pytest eval/`).

## `*_run.json` — facts-trace (test_facts_trace.py)
Asserts no developmental number appears in the agent's output that a tool didn't return. Two shapes:

- **Single-shot:** `{ "tool_returns": [...], "agent_output": "...", "allowed_user_numbers": [...] }`
- **Multi-turn:** `{ "turns": [ { "tool_returns": [...], "output": "..." }, ... ], "allowed_user_numbers": [...] }`
  Later turns are justified by tool returns from that turn or any earlier one (tools stay in context).

`allowed_user_numbers` whitelists clock times the parent supplied (e.g. childcare/bedtime), which
are legitimately in the output but don't come from a tool.

## `composed_*.json` — blocks contract (test_blocks_contract.py)
A `{ "blocks": [...] }` composed day. Asserts the contract: valid `kind`, naps carry no window,
no zero-length or duplicate time slots, and the minimum-day set contains the focus block.

## `tone_transcript.json` — optional persona judge (test_tone_judge.py)
A `{ "transcript": [ {role, text}, ... ] }` conversation, graded by an LLM-as-judge for voice.
Off by default; run with `RUN_TONE_JUDGE=1`.

To add a case: run the agent, save its tool calls + output(s) here, and `pytest eval/`.
