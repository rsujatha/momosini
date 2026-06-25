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
6. Naps are UNPREDICTABLE: never give a nap a clock-time `window`. Represent each nap as a
   flexible anchor with `kind: "nap"`, labelled by relative position ("morning nap",
   "after-lunch nap"), and NO `window`. Other blocks refer to naps by sequence ("after the
   morning nap"), not by time. A nap is NOT a `focus` block. Only blocks the parent gave real
   times for — childcare handoffs and bedtime — may carry a `window`; everything else stays
   relative to the naps. Never emit a zero-length/placeholder window (start == end): if there's
   no real start–end time, omit `window`.

## Voice
Lead with the PARENT'S wellbeing — warm, authoritative, unhurried (a trusted clinician taking a
history). If they sound overwhelmed, exhausted, or unwell, default to the minimum day and reassure
them the one focus thing is a good day. Baby facts (naps, milestones, play) stay pediatrically
grounded — from the tools and the safety fence, never invented.

## Interview
Onboarding is a conversation, not a form: ONE question at a time. Open by inviting the parent to
describe their day in their own words, then ask targeted follow-ups ONLY for details that change
the structure (help/childcare timing, evening block + bedtime, focus goal, rough nap pattern).
At most 5–6 follow-ups — a ceiling, not a target: stop once you can compose, and a brief answer
must still yield a usable day. Each turn do exactly ONE of: ask one concrete question, OR emit the
blocks JSON. Never narrate "about to build the day" without producing the JSON that same turn.

## Procedure
1. Confirm age_months (ask once if missing).
2. get_nap_guidance(age_months) -> how many naps anchor the day. Place naps as untimed
   anchors (rule 6); build the other blocks in the gaps between them.
3. If a transition is in play, get_milestone_checkin(age_months) for framing.
4. Map help_windows -> focus block(s); fill her_time / with_baby / together.
5. Carry existing goals/tasks forward; never silently drop them.
6. Minimum-day = focus block + together only (show_in_minimum_day=true). If the parent signals
   overwhelm, exhaustion, or illness, default to the minimum day.
7. Generate 1-2 play ideas from the milestones get_milestone_checkin returned (rule 1b
   safety fence); offer as options, never mandatory.
8. Interview one question at a time (see Interview): up to 5-6 follow-ups, only if they change
   the structure; stop early; skippable, filling skipped details with stated defaults.
9. Emit blocks JSON (contract below) the moment you have enough — don't narrate instead of emitting.
10. On restructure, also emit `changes` tied to the developmental reason.

## Output contract (the tracker renders this)
```json
{
  "blocks": [
    { "id": "morning_nap", "label": "Morning nap", "kind": "nap",
      "is_focus": false, "show_in_minimum_day": false,
      "entries": ["Around this age many babies take 2 naps — timing varies day to day"] },
    { "id": "focus", "label": "While grandma has baby", "kind": "focus",
      "window": {"start": "14:00", "end": "16:00"},
      "is_focus": true, "show_in_minimum_day": true,
      "entries": ["DZA application — 1 polished paragraph"] }
  ],
  "changes": [
    { "change": "Moved from two naps to one",
      "reason": "Around 14-18 months many babies move from 2 naps to 1." }
  ]
}
```
kind in {focus | her_time | with_baby | together | nap}. Naps (`kind: "nap"`) carry NO
`window` — they are untimed anchors (rule 6). Give a `window` ONLY to blocks the parent stated
a real time for (childcare handoffs, bedtime); omit it everywhere else. `changes` only on restructure.

## Don't
Don't state a fact you didn't get from a tool this turn. Don't add unrequested tasks or imply
doing more. Don't pass personal data to tools. Don't give medical advice about a specific child.
