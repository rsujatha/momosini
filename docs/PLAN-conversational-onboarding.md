# Plan — conversational onboarding (interview, not a form)

Status: **PROPOSED, not started.** Per START-HERE guardrail 2, this is scoped and waiting on
Sujatha's review before any code changes. It also touches `agent/instructions.py` and the
`compose-baby-day` Skill, both of which are protected (guardrail 1) — so the prompt/method
changes below are *proposals*, called out explicitly, not edits made in this pass.

---

## 1. What's wrong now (current state)

Onboarding today is a **single static form** (`tracker/mom-day-tracker.html`, `#onboard`). Every
field is on screen at once: birth date, a free-text "tell me about your day", day-start time,
repeatable childcare-help rows, repeatable nap rows, an evening/bedtime toggle, and a goal field.
The parent fills the whole thing, hits Compose, and the page makes **one** `POST /compose` call
with all fields pre-structured (`composeWithAgent()` → `web/app.py` → `runner.compose_day()`).

Two consequences:

- **It doesn't feel like a conversation.** It's a wall of inputs — the opposite of the warm,
  guided experience you want. The free-text box is just one field among many, not the centre.
- **The agent never actually interviews.** Because the form pre-extracts everything, the model
  rarely needs to ask anything. And when it *does* return a clarifying question, the frontend
  treats it as an error (`"The assistant needs a bit more — …"`) and stops — it does **not**
  continue the conversation. The session machinery to do so already exists in `runner.py`
  (`run_turn`, `session_id`) but the web layer throws the session away after one shot.

So the raw materials for a conversation are present; the product just isn't wired to use them.

## 2. Target experience

An onboarding that feels like **one calm, authoritative clinician taking a history**, one step at
a time:

1. **Open with the birth date.** A single question on screen. Everything keys off age, so this is
   first (matches the Skill's procedure step 1).
2. **Invite the parent to speak freely.** One open prompt — "Tell me about your day in your own
   words" — as the centre of the screen, not a field in a stack. The parent types as much or as
   little as they like.
3. **Drill down only where needed.** The agent reads the free text, calls its tools, and asks
   **targeted follow-ups one at a time** for whatever is still missing or ambiguous (when help
   windows are, whether there's an evening block, what the focus time is for). If the parent
   already covered it, skip it.
4. **Compose** once it has enough, and hand the blocks JSON to the existing tracker unchanged.

One question per screen throughout. The tone is the differentiator: present, unhurried, never
interrogating — see the persona decision in §5.

## 3. Scope — what changes, what doesn't

**Changes (proposed):**

- **UI (`tracker/mom-day-tracker.html`).** Replace the static multi-card form with a single-step
  conversational view: one prompt + one input visible at a time, a running transcript above it,
  a typing/thinking state while the agent works. Reuse the existing styling tokens and the
  birth-date → age helper. The structured pickers (help-window rows, nap rows, evening toggle)
  become *fallbacks the agent can surface as a direct question* rather than the default surface.
- **Web layer (`web/app.py`).** Add a **multi-turn endpoint** that holds the ADK session across
  turns instead of one-shot `compose_day`. It returns either the agent's next question *or* the
  composed day. The session-keyed plumbing already exists in `runner.py`; this exposes it.
- **Agent method (`compose-baby-day` Skill — PROPOSAL, protected).** Raise the clarifying-question
  cap from one to **5–6**, one at a time, only for day-changing gaps (§5 decision B). Change to a
  protected file — make the edit only after this plan is approved.
- **System prompt (`agent/instructions.py` — PROPOSAL, protected).** The persona/voice lives here:
  a clinician who looks after the **parent's** wellbeing (offer a minimum day on overwhelm/illness)
  while keeping anything about the baby pediatrically grounded (§5 decision A). Proposed, not made
  in this pass (guardrail 1).

**Explicitly unchanged:**

- `knowledge/` — untouched. Facts discipline is unaffected: the interview still gets every
  nap/milestone number from the tools; the model just *phrases the questions* conversationally.
- The blocks JSON **output contract** and the deterministic tracker that renders it — unchanged,
  so this is a front-of-funnel change only.
- Architecture: still **one agent**, still MCP-for-facts. Multi-turn was always allowed by the
  design (decide → call → observe → *ask* → compose); we're finally using the "ask" loop.

## 4. Build steps (ordered, each independently reviewable)

1. **Web: multi-turn compose endpoint.** Expose `run_turn` + session persistence so a turn can
   return a follow-up question and the next turn answers it in the same session. Keep the existing
   one-shot path working. *Checkpoint:* a scripted two-turn exchange composes a day.
2. **UI: conversational shell.** One-question-at-a-time view with transcript + thinking state,
   driving the endpoint from step 1. Birth date → free text → agent-led follow-ups → compose.
   *Checkpoint:* full onboarding completable by typing, no wall-of-form.
3. **Persona + interview method (PROPOSED edits, after approval).** The parent-wellbeing clinician
   voice with pediatric grounding (`instructions.py`) and the 5–6-question interview policy
   (`compose-baby-day` Skill), per §5 A & B. *Checkpoint:* tone reads as the intended persona;
   follow-ups are targeted, not redundant; overwhelm/illness cues trigger a minimum-day offer.
4. **Guard the protective principles.** Verify the interview still respects "protective, not
   throughput-maximising" — the 5–6 cap is a ceiling, not a target; it must stop early once it has
   enough and never interrogate a depleted parent. Add a "skip, assume sensible defaults" escape.
   *Checkpoint:* a one-line free-text answer still yields a usable day without nagging.
5. **Eval.** Extend `eval/` so the facts-trace test still passes across a multi-turn session, and
   (optional) a tone check for the persona. *Checkpoint:* a hallucinated fact in any turn fails a test.

## 5. Decisions — settled

**A. Persona — a combination (SETTLED).** The voice centres on **the parent's wellbeing**: warm,
authoritative, attentive to how they're coping — if they signal overwhelm or illness, it offers a
**minimum day** rather than a full one. That's the psychiatrist-style care you asked for, aimed at
the parent, not the baby. But anything *about the baby* — naps, play ideas — stays **pediatrically
grounded** (facts from the tools, age-appropriate play under the safety fence). So: a clinician who
looks after the parent, with a pediatrician's grounding for the child's routine. This blend goes in
`instructions.py` (proposed edit, after this plan is approved). It also strengthens the §2.5
"protective, not throughput-maximising" pitch — the persona *is* the differentiator made audible.

**B. Interview length — cap raised to 5–6 questions (SETTLED).** The old "one question maximum"
(brief §4 + the `compose-baby-day` Skill) is replaced by **up to 5–6 targeted follow-ups**, asked
one at a time, only for things that change the day, always skippable. To log:
- Update the `compose-baby-day` Skill's clarifying-question policy: one → max 5–6.
- Soften brief §4 / Skill wording accordingly.
- Record the change in `docs/DECISIONS.md` so it isn't re-litigated.
Keep the protective guard from step 4: a short free-text answer must still yield a usable day —
the cap is a ceiling, not a target, and the agent stops as soon as it has enough.

**C. Privacy framing.** Free-text histories may carry more personal detail (including how the parent
is feeling) than the old discrete fields. The rule still holds — only `age_months` reaches a tool —
but the on-screen note should reassure that what they type, including wellbeing cues, stays local.
No architectural change, just copy.

## 6. Guardrail check

- **knowledge/ untouched** — yes; facts still flow from tools.
- **instructions.py / Skill** — flagged as *proposals* (§3, §5), not edited in this pass.
- **No scope creep** — this is the existing "onboarding" flow done better, not a new domain or
  feature; the output contract and tracker are unchanged. Anything beyond it stays future work.
