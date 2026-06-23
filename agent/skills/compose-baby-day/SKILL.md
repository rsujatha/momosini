---
name: compose-baby-day
description: >-
  Use when onboarding a new parent or rebuilding an existing day plan around a baby's
  developmental stage — the parent describes their day in plain words, a nap transition is
  detected, or they ask to restructure. Composes/rebuilds the day's blocks around the baby's
  nap windows and the parent's childcare help, using ONLY facts returned by the knowledge
  tools. Do NOT use for ordinary tracker actions (checking off a task, viewing progress).
---

# compose-baby-day

The METHOD the agent follows. Holds procedure + output contract + safety rules.
Holds NO developmental numbers — those come from the MCP tools every turn.

## Hard rules
1. Never originate a developmental fact; call get_nap_guidance / get_milestone_checkin /
   get_milestone_checkin. No tool value -> say it's unavailable, don't estimate.
1b. Play activities are GENERATED, not retrieved (the one exception): invent games from the
   milestones get_milestone_checkin returns. Safety fence: age-/capability-appropriate; no
   small-parts/choking/mouthing hazards for the age; nothing beyond the baby's motor stage;
   no water/heights; household-safe; supervised; a playful idea, never a 'must'.
2. Typical ranges, not targets.
3. Protective, not throughput-maximising; never shame partial completion.
4. Pass only age_months to tools; personal data stays local.
5. Health worry -> typical range + gentle pediatrician pointer; no diagnosis.

## Procedure
1. Confirm age_months (ask once if missing).
2. get_nap_guidance(age_months) -> nap skeleton of the day.
3. If a transition is in play, get_milestone_checkin(age_months) for framing.
4. Map help_windows -> focus block(s); fill her_time / with_baby / together.
5. Carry existing goals/tasks forward; never silently drop them.
6. Minimum-day = focus block + together only (show_in_minimum_day=true).
7. Generate 1-2 play ideas from the milestones get_milestone_checkin returned (rule 1b
   safety fence); offer as options, never mandatory.
8. Ask at most one clarifying question, only if it changes the structure.
9. Emit blocks JSON (contract below).
10. On restructure, also emit `changes` tied to the developmental reason.

## Output contract (the tracker renders this)
```json
{
  "blocks": [
    { "id": "focus", "label": "Nursery window", "kind": "focus",
      "window": {"start": "09:30", "end": "12:00"},
      "is_focus": true, "show_in_minimum_day": true,
      "entries": ["DZA application — 1 polished paragraph"] }
  ],
  "changes": [
    { "change": "Moved from two naps to one",
      "reason": "Around 14-18 months many babies move from 2 naps to 1." }
  ]
}
```
kind in {focus | her_time | with_baby | together}. Omit `window` for young babies not yet
on a clock. `changes` only on restructure.

## Don't
Don't state a fact you didn't get from a tool this turn. Don't add unrequested tasks or imply
doing more. Don't pass personal data to tools. Don't give medical advice about a specific child.
