# START HERE — first session setup

This repo is the source of truth for the project (and its Cowork sessions). A new
session starts blank — it remembers nothing from earlier work. These docs ARE that memory.
Read them before doing anything.

## Step 1 — orientation (do this before writing or changing ANY code)

Paste this as your first message to Cowork:

> Read `ARCHITECTURE.md`, `docs/DECISIONS.md`, and the project brief
> (`mom-day-organiser-agent-brief.md`), then `docs/WORKPLAN.md`. Don't write or change any
> code yet. Confirm back to me, in your own words:
> 1. How many agents this project has, and why.
> 2. Where developmental facts come from (and the ONE exception).
> 3. The infant-safety rule for generated play activities.
> 4. The two things you must never change without careful review.

If the read-back is wrong on any point, correct it before proceeding. That read-back is the
cheapest possible check that the discipline loaded.

## Step 2 — pick ONE task, not the project

Open `docs/WORKPLAN.md` and take a single item. Give Cowork: the task, its Definition of Done
(from `CONTRIBUTING.md`), and "make this a reviewable change" — not "build the repo." Small,
reviewable steps.

## Step 3 — the two standing guardrails (state them in every session)

1. **Do not change `knowledge/` or `agent/instructions.py` without careful review.** These
   are the curation gate and the facts-enforcement layer — the differentiator. AI edits are
   exactly where a fabricated source or a softened rule slips in.
2. **Do not expand scope.** Anything beyond the current task and the brief's §11 scope —
   new domains, deployment, fact tables — gets *proposed*, not implemented.

## The discipline in one line

Facts are retrieved from tools (nap, milestone). Play activities are generated from those
facts under a safety fence. The model phrases and creates; it never invents a fact. One agent.
If the session re-litigates a settled question, add the answer to `docs/DECISIONS.md` so it
persists — don't just re-explain it in chat.
