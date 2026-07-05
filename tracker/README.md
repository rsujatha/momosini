# Tracker (deterministic app)

Plain day-block tracker (no model) in `mom-day-tracker.html` — day blocks with editable entries
+ checkboxes, full/minimum mode, 28-day focus streak, a personal wins log, all on browser
localStorage. It both lets a parent build a day by hand AND renders a day composed by the agent.

## The agent → tracker seam
`window.applyComposedDay(payload)` ingests the agent's blocks JSON (the contract in
`agent/skills/compose-baby-day/SKILL.md`) and renders it. `payload` is the object the agent
returns (`{blocks:[...], changes?:[...]}`) or a JSON string of it.

Field mapping (contract → tracker block):
`label→name`, `kind:"focus"`/`is_focus→focus`, `kind:"together"→together`, `kind:"nap"→nap`
(rendered untimed), `window→time` (kept ONLY for blocks the parent scheduled — naps never get
one), `show_in_minimum_day→minDay`. The agent's `entries` seed that day's entries, and they
stay **fully editable** (type, check off, add, remove). `changes` shows as a "what changed" note.

For now you can paste composed JSON into the onboarding screen ("Have a plan from the
assistant?"); a backend would call `window.applyComposedDay(json)` directly.

## Consistency notes
- Naps are untimed everywhere (rule 6): the built-in onboarding asks only *which part of the
  day*, never a clock time, and never promotes a nap to the focus block.
- "Focus" is the contract's protected window (was labelled "premium"); progress counts a day as
  a focus day when the focus block has a checked entry.
