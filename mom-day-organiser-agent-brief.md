# Momosini Agent — Project Brief

## How to use this file
Drop this into Claude Cowork (or Claude Code) as the project brief. It captures the goals, architecture, scope, and constraints decided so far. Build to this spec, and hold the scope discipline in section 11 given the deadline.

---

## 1. What this is
A privacy-first daily organiser for parents of young babies. A parent describes their day in plain words; an **agent** turns it into a personalised day structure built around the baby's routine and the parent's childcare help, and nudges them to restructure as the baby hits developmental transitions. Submitted to the Kaggle "Vibecoding Agents" capstone.

## 2. Target & success criteria
- **Competition:** Kaggle Vibecoding Agents Capstone. **Deadline: July 6, 2026, 11:59 PM PT** (confirm on the competition Timeline tab).
- **Track:** Concierge Agents (personal/family assistant that keeps personal data safe). Alternate: Agents for Good.
- **Must demonstrate at least 3 course concepts.** We target **four** for margin: ADK agent, MCP server, Security features, Deployability.
- **Scoring weight:** Implementation 70 (Technical 50 + Documentation 20), Pitch 30 (Concept 10 + Video 10 + Writeup 10). Invest accordingly.

## 2.5 Differentiation & positioning (feeds the pitch)
**Thesis:** the edge is not "a planner for moms" (that's a generic planner with a sticker). It's that the whole model is built on assumptions a new parent's life actually has, which generic planners structurally get wrong:
- **Time you don't control.** Available time is defined by the baby's naps + childcare handoffs, not a calendar the user owns. Generic planners slot tasks into your own time; this is built around caregiving windows — "her time" vs "with-baby time."
- **Dynamic, not static.** The structure that works at 4 months breaks at 6 and again at 9 (nap drops). This *knows* the transitions and proactively restructures; generic planners are static and never nudge about a developmental shift.
- **Protective, not throughput-maximising.** Built for depleted executive function: minimum-day mode, one-thing-counts, forgiving streak, calm glanceable surface. Generic planners optimise output, which shames an exhausted parent ("3 of 12 done").
- **Domain knowledge + privacy.** Encoded age-appropriate knowledge a generic tool lacks; on-device personal data that parents guard more than a knowledge worker guards their meetings.

**Honest moat (don't overclaim):** a generic frontier model can produce a passable plan on demand, so raw capability is not the edge. The durable differentiation is the combination of (1) encoded, compounding domain knowledge, (2) proactivity — it reaches out at the right developmental moment rather than waiting to be asked, and (3) trust — built for this user, private by design, shared mom-to-mom. The moat is depth in a narrow, high-need, underserved niche: being deeply right for one parent's actual life beats being generically okay for everyone.

**Positioning line** (use in the writeup's Core Concept & Value, 10 pts, and in the video):
> A generic planner helps you spend the time you control; this one organises around the time you don't — your baby's — and changes as your baby does.

## 3. Architecture — three layers
1. **Deterministic app (the tracker).** Day blocks, checkboxes, progress strip, milestone banner, local storage. No model. Reliable, cheap, private. **Keep this as plain code — do not agent-ify it.**
2. **The agent (ADK).** The one genuinely agentic flow: onboarding + restructure. Given a goal, the *model* decides which tools to call, calls them, observes results, asks a clarifying question when needed, and composes the day.
3. **MCP knowledge server (local, stdio, bundled).** Curated, age-keyed developmental knowledge exposed as tools the agent calls.

**Core principle across all layers: rules hold the facts; the model only phrases them.** Factual values come from the curated data / MCP tools, never from the model's memory.

## 4. The agent — what makes it an agent (not a coded app)
The agent must genuinely orchestrate, not run a fixed script:
- The **model decides** which tools to call and in what order — do NOT hardcode the tool calls in a fixed pipeline.
- It **uses tools and reacts** to their results.
- It **loops:** decide → call tool → observe → decide again → (sometimes) ask the parent a clarifying question → compose.
- It is **goal-directed:** given "set up or adjust this parent's day," it works out the steps, handling descriptions you didn't script for.

**Litmus:** if you wrote the exact sequence, it's app code. It's an agent only when the model drives.

**Agent capabilities/tools:**
- `get_nap_guidance(age_months)`
- `get_milestone_checkin(age_months)` — also the grounded input for game generation (see §6.5)
- `propose_day_structure(help_windows, naps, ...)` — assembles blocks from the parent's help windows + nap guidance
- **generate play activities** from the milestones the tool returns — the one place the model *creates* rather than retrieves (bounded by retrieved facts + a safety fence; see §6.5)
- ask the parent a clarifying question when the description is ambiguous (e.g., bedtime unclear)

**Packaged as a Skill:** the restructure/compose-a-day *method* the agent follows is codified in the `compose-baby-day` Skill (Appendix C), loaded on demand at onboarding/restructure. Facts stay in MCP; the Skill holds only the procedure, output contract, and safety rules. This optionally ticks a fifth gradable concept (Agent skills) — treat it as margin, not core, since a runtime-specific Skills mechanism may pull Antigravity into scope.

## 5. MCP server — spec
- **Local stdio transport**, bundled in the same deployment as the agent (the agent spawns it as a subprocess). **Not remote.** No exposed network endpoint.
- **One server, multiple per-domain tools**, backed by a **shared loader** over **per-domain data files**.
- **v1 curated domains: nap, milestone.** (Play is *generated*, not curated — see §6.5.) Designed to extend (feeding, sleep, safety, motor) by dropping in a data file + registering a thin tool — no rewrite of existing tools.
- **Everything keyed by age** (months / age bands) — the shared index across domains.
- Tools are deterministic lookups returning structured data only.

## 6. Knowledge data — curation rules
- Each curated domain is its own age-keyed data file (e.g. `naps.json`, `milestones.json`).
- Curate from **authoritative sources** (AAP, Bright Futures, established child-development references). Record sources.
- Frame everything as **typical patterns, not prescriptions** ("babies around this age often…"), with an every-baby-varies tone.
- Sanity-check the content where possible — this is child-development guidance.
- **Tier every figure by evidence strength** and record the source per field: [A] consensus guideline (AASM/AAP, WHO), [B] research literature (systematic review / longitudinal reference study), [C] practical convention (widely used but thin primary-literature backing). Do not present a [C] figure with the same authority as an [A] one — that discipline is the differentiator (see §2.5).
- **Worked example: Appendix B** instantiates these rules for the nap domain (the `naps.json` content), with sources, tiers, and the honest handling of fields guidelines won't cover. The milestone domain follows the same pattern.

### 6.5 Play activities — generated, not curated (deliberate boundary)
Play games are **not** a curated domain and **not** a tool. They are the one place the model
*creates* rather than retrieves — and that is consistent with the facts discipline, because a
game is not a fact. The split:
- **Grounded input:** the milestones the baby is working toward come from `get_milestone_checkin`
  (a fact — retrieved, sourced, never invented). The model does NOT invent which milestones matter.
- **Generated output:** the model invents play activities that exercise *those specific* milestones.
  Many valid answers exist; this is creative generation, not hallucination.
- **Safety fence (required — this is where "make it up" needs a limit):** a generated activity
  isn't human-vetted like a curated list, so the instruction MUST constrain it to be
  age-/capability-appropriate, with **no small-parts/choking/mouthing hazards** for that age, no
  activity beyond the baby's motor stage (e.g. unsupported sitting/standing they can't do), no
  water/heights, household-safe materials, **caregiver-supervised**, framed as a *playful idea*
  (never something the baby "must" do), with a light "these are ideas — supervise your child" note.
- **Positioning:** describe this as *facts retrieved, activities generated from those facts* —
  NOT as "hallucinated games." Calling it hallucination undercuts the §2.5 differentiator; framing
  it as bounded generation strengthens it (it shows you know where generation belongs).

## 7. Anti-hallucination — why the agent uses the tool (DESIGN REQUIREMENT)
A model given a tool will still answer from memory unless forced. Enforce tool use:
- **System-prompt rule:** the agent MUST NOT answer developmental facts (naps, milestones, ages) from its own knowledge; it MUST call the relevant tool and use only the returned values. **Play activities are the sole exception** — generated from the retrieved milestones under the §6.5 safety fence, never presented as facts.
- **Clear tool descriptions** stating exactly when to use each tool.
- **Architectural guarantee:** factual values flow through the tools into the model's context as grounded data; the model phrases, it does not originate numbers. Where feasible, verify model output against tool values and override mismatches.
- **Agency stays in orchestration** (which tools, what order, composition, clarifying questions); **determinism stays in the facts.**

## 8. Model & secrets
- Model: **Gemini via Google AI Studio** (free tier is sufficient — the agent fires sparsely, at onboarding and restructure).
- **API keys in environment variables / server-side only. NEVER in code or the repo.**

## 9. Deployment
- **Containerised agent** with the **stdio MCP server bundled inside the same container.** Deploy to **Cloud Run** (course path) or any container host (Fly/Render/Railway). Vercel is fine for the tracker front-end.
- A live public endpoint is NOT required for judging — but if deployed, **document reproducible deploy steps** in the README.
- **Demonstrate deployability in the video.**

## 10. Privacy & security
- **Personal data (each parent's schedule, baby's birth date) stays on-device** (browser/local storage). It does NOT enter the MCP server.
- The **MCP server holds only general, public-knowledge facts** (nap/milestone by age) — nothing personal.
- **Local-only stdio server** (no inbound access); **no keys in code.**
- Make **precise privacy claims:** state exactly what stays local (tracker data, knowledge lookups) versus what calls out (the Gemini agent sends prompts to Google). Do not claim "100% local" if the agent uses cloud Gemini.

## 11. Scope for the deadline — ship THIS, not more
- **One genuinely agentic flow:** onboarding + restructure.
- **Two curated knowledge domains:** nap, milestone. **Play is generated** from milestones under a safety fence (§6.5).
- **Reuse the existing tracker** UI and logic.
- Everything else — feeding/sleep/safety domains, cross-device sync, accounts/backend — is **"future work"** in the writeup. Designing the extensible structure counts; building it all does not.

## 12. Submission checklist
- [ ] Kaggle **Writeup** (≤2,500 words), **Track = Concierge Agents**: problem, solution, architecture, journey.
- [ ] **Cover image** (required to submit).
- [ ] **YouTube video ≤5 min:** problem → why agents → architecture diagram → live demo → the build. Show the agent calling tools and the deployment.
- [ ] **Public project link** (working demo, no login/paywall) OR public **GitHub repo** with detailed setup instructions.
- [ ] **README.md:** problem, solution, architecture, setup/deploy steps, diagrams (worth 20 pts).
- [ ] **No API keys or passwords anywhere in the code.**
- [ ] Aware: top-3 winners license the submission + source under **CC-BY 4.0** — submit a version you're comfortable open-sourcing.

## 13. Suggested build order
1. Curate the two age-keyed data files (nap, milestone) with sources. (Play is generated — no data file.)
2. Build the local stdio MCP server: shared loader + three tools.
3. Build the ADK agent: goal + tools + decide/observe/loop + clarifying question + compose; enforce tool-use for facts (section 7).
4. Package the restructure/compose method as the `compose-baby-day` Skill (Appendix C) — the agent loads it on demand; facts still flow from MCP, not the Skill.
5. Wire the agent's output into the existing deterministic tracker.
6. Containerise (agent + bundled MCP server); deploy; document the steps.
7. Record the 5-min video; write the ≤2,500-word writeup + README.

---

## Appendix A — definitions to keep straight
- **Coded app:** you wrote the exact steps; deterministic. (The tracker, milestone banner, day-builder transform.)
- **LLM feature:** a single model call in a fixed flow (e.g. a one-shot parse). Not an agent.
- **Agent:** the model drives — chooses tools, reacts to results, loops toward a goal. (The onboarding/restructure flow.)
- **MCP server ≠ agentic by itself:** calling it from a fixed pipeline is still a coded app. It's agentic only when the *model* decides to call it.

---

## Appendix B — Worked example: the nap knowledge domain, sourced

This is §6's curation discipline applied to the nap domain — the reference content behind
`naps.json` and `get_nap_guidance(age_months)`. It demonstrates the standard the milestone
domain should also meet: every figure tagged with a source and a confidence tier,
lower-evidence fields demoted rather than disguised, and the ranges guidelines deliberately
won't cover left open rather than filled with a guess.

**Framing rule for the whole domain:** these are *typical ranges, not targets*. Wide individual
variation, especially under 4 months. For babies born preterm, use **adjusted age** (age from
due date), not birth age, until ~24 months.

### Confidence tiers
- **[A] Consensus guideline** — AASM/AAP or WHO. Least disputable.
- **[B] Research literature** — systematic review / longitudinal reference study. Strong, but a
  description of what's *typical*, not an official recommendation.
- **[C] Practical convention** — widely used by clinicians and sleep apps, but with limited
  primary-literature backing. Useful, but flagged as lower-evidence.

### Chart

| Age band | Total sleep / 24h | Typical # naps | Daytime sleep | Tier (per column) |
|---|---|---|---|---|
| 0–3 mo (newborn) | 14–17 h | irregular, 4+ short | not yet consolidated | Total **[A]** WHO/NSF · naps **[B]** |
| 4–5 mo | 12–16 h | 3–4 | ~3.5–5 h | Total **[A]** AASM/AAP · naps **[B]** |
| 6–8 mo | 12–16 h | 3 → 2 | ~2.5–3.5 h | Total **[A]** · naps **[B]** |
| 9–12 mo | 12–16 h | 2 | ~2–3 h | Total **[A]** · naps **[B]** |
| 12–18 mo | 11–14 h | 2 → 1 (transition ~14–18 mo) | ~2–3 h | Total **[A]** · naps/transition **[B]** |
| 18–24 mo | 11–14 h | 1 | ~1.5–2.5 h | Total **[A]** · naps **[B]** |
| 2–3 yr | 11–14 h | 1 | ~1.5–2.5 h | Total **[A]** · naps **[B]** |
| 3–5 yr | 10–13 h | 1 → 0 (nap drop, varies widely) | 0–1.5 h if still napping | Total **[A]** · nap drop **[B]** |

Notes on the bands:
- AASM gives **no** recommendation below 4 months — it explicitly excludes that range due to
  the width of normal variation. The 0–3 mo total is from WHO / National Sleep Foundation, which
  do cover it. Flag this gap rather than papering over it.
- AASM's stated bands are 4–12 mo (12–16 h), 1–2 yr (11–14 h), 3–5 yr (10–13 h). The finer age
  splits are for readability; the *total-sleep* figure within each is the AASM band.
- Some healthy children keep napping to ~age 7. The nap-drop age is the most variable cell in
  the table — present it as a wide window, never a deadline.

### Wake windows — handle differently [C]
Specific wake-window durations by age are **practical convention**, not consensus or
systematic-review output. Two honest options:
1. **Label them [C]** as a separate, clearly lower-evidence helper, or
2. **Derive** an implied awake-time band from (24 h − total sleep − night sleep) ÷ naps, so the
   number is a transparent consequence of the [A]/[B] figures rather than a fresh assertion.

Asserting wake windows with the same confidence as total-sleep figures — what most commercial
charts do — is the thing to avoid.

### Sleep-cycle length (physiology, for context) [B]
- Infant sleep cycles run **~50–60 min**, shorter than the adult **~90 min** — why young babies
  surface frequently and short naps are common.
- Organized circadian sleep cycles don't emerge until **~3–6 months**.
- Belongs in the app as *explanation* ("why is my baby's nap only 40 minutes?"), not as a
  schedule column.

### Sources (put real citations behind these in the data file)
- **[A] AASM consensus statement** — Paruthi S, et al. *Recommended Amount of Sleep for Pediatric
  Populations.* J Clin Sleep Med. 2016;12(6):785–786. AAP-endorsed.
- **[A] WHO** — *Guidelines on physical activity, sedentary behaviour and sleep for children under
  5 years of age.* 2019. (Covers the under-4-month range AASM omits.)
- **[B] Galland BC, et al.** — *Normal sleep patterns in infants and children: a systematic review
  of observational studies.* Sleep Med Rev. 2012 — primary source for nap counts/durations by age.
- **[B] Iglowstein I, et al.** — *Sleep Duration From Infancy to Adolescence: Reference Values and
  Generational Trends.* Pediatrics. 2003 — percentile reference curves including naps.
- **[B] Pediatric sleep-medicine texts** — sleep-cycle physiology and nap-transition norms.

### Why this beats the commercial charts (for the writeup)
Popular charts present one undifferentiated table where rock-solid numbers (total sleep) sit
beside unsourced convention (wake windows) with identical visual authority, backed by a reference
list that doesn't underpin the granular cells. This keeps the same parent-friendly shape but
(a) sources every figure, (b) tiers the confidence, (c) refuses to dress convention as evidence,
and (d) is honest about the range guidelines deliberately won't touch (under 4 months). That
provenance discipline — not a prettier table — is the differentiator.

---

## Appendix B-2 — Worked example: the milestone knowledge domain, sourced

§6's curation discipline applied to the milestone domain — the reference content behind
`milestones.json` and `get_milestone_checkin(age_months)`. It meets the same standard as the
nap appendix: a single named source, a confidence tier, an honest tier rationale, and the
same age index as naps so the two domains line up.

**Single source (use this citation in the writeup):**
> Scharf RJ, Scharf GJ, Stroustrup A. **Developmental Milestones.** *Pediatrics in Review.*
> 2016;37(1):25–37. American Academy of Pediatrics. (Table 3, "Developmental Milestones,"
> spanning 1 month to 6 years across seven domains.)

The whole domain is transcribed from this one table — not stitched together from scattered
charts. That single-provenance story is itself part of the pitch.

**The seven domains** carried per age band: gross motor, fine motor, self-help,
problem-solving, social/emotional, receptive language, expressive language. The agent's
play-activity generation (§6.5) targets the milestones in these domains — facts retrieved,
games generated.

**Framing rule for the whole domain:** typical ranges, not targets. A milestone reached later
than its band is common and not, by itself, cause for concern. For babies born preterm, use
**adjusted age** (age from due date), not birth age, until ~24 months — same rule as naps.

### Confidence tier — and the honest rationale

Every band is tagged **[B]**, with the reasoning stated openly rather than rounded up:

- It is **not [A]**. [A] is reserved for a formal consensus practice guideline (AASM/AAP sleep
  statement, WHO). This is a peer-reviewed AAP *educational review* that synthesizes the
  developmental literature into a teaching table — authoritative and clinically standard, but a
  review, not a practice guideline.
- It is **not a primary [B] systematic review** in the way Galland 2012 is for naps; it is a
  secondary synthesis. We still tier it **[B]** (strong, peer-reviewed, AAP-published) and say
  so plainly. Resisting the temptation to stamp it [A] *is* the facts-discipline the pitch sells.
- **Milestone ages carry inherent wide variation** — wider than sleep totals — so the
  typical-not-prescriptive framing matters even more here.

The final tier call is the provenance gate; the file marks [B] pending that review.

### Age banding — finer than naps, deliberately

`milestones.json` uses **one band per age column in the source table** (1, 2, 3, … 16, 18, 20,
22, 24, 28, 30, 33 months, then 3, 4, 5, 6 years) rather than collapsing to `naps.json`'s eight
coarse bands. Reason: infant development moves fast and the source reports it that finely — a
9-month-old and a 12-month-old should not get the same milestones, the way they'd share a nap
band. Bands are contiguous integer-month ranges so every `age_months` maps to exactly one band,
and `get_milestone_checkin(age_months)` does the same age→band lookup `get_nap_guidance` does.

**Trade-off, noted honestly:** this means milestone and nap bands no longer share identical
edges, so the two domains don't literally share one index — they share the same *lookup
mechanism* (age→band), not the same band boundaries. This is a deliberate deviation from
ARCHITECTURE.md's "shared index across domains" line; if kept, that line should be softened to
"shared age-keyed lookup" and the choice logged in `docs/DECISIONS.md`. (Flagged, not yet changed.)

### Red flags — deliberately out of scope (for now)

The same article carries a **Developmental Red Flags** table (Table 5) and a neonatal-reflex
table. These are *not* in `milestones.json`. If added later, red flags would be a separate,
clearly-scoped helper feeding the "is my baby behind?" → *point-to-pediatrician* path (Skill
rule 5) — never a diagnosis the model makes. Logged as future work, consistent with §11 scope
discipline: designing the extensible structure counts; building every table does not.

### Why this matches the nap appendix's bar (for the writeup)

Same four moves as the nap domain: (a) every band sourced to one real citation, (b) confidence
tiered, (c) the tier *demoted honestly* ([B], not a dressed-up [A]), and (d) explicit about what
it deliberately leaves out (red flags, diagnosis). The milestone domain doesn't just copy the
nap pattern — it shows the discipline generalizes, which is the extensibility claim the pitch
makes.

---

## Appendix C — SKILL.md: `compose-baby-day`

The methodology layer for the agent's one agentic flow. Save as
`skills/compose-baby-day/SKILL.md`. The agent loads it on demand at onboarding or
restructure; it holds the *procedure*, the *output contract*, and the *safety rules* —
never any developmental number (those come from the MCP tools).

Everything from the frontmatter down is the file content.

### Frontmatter

```yaml
---
name: compose-baby-day
description: >-
  Use when onboarding a new parent or rebuilding an existing day plan around a baby's
  developmental stage — e.g. the parent describes their day in plain words, a nap
  transition is detected, or the parent asks to restructure their schedule. Composes or
  rebuilds the day's blocks around the baby's nap windows and the parent's childcare help,
  using ONLY facts returned by the knowledge tools. Do NOT use for ordinary tracker
  actions (checking off a task, viewing progress, editing an entry) — the app handles
  those without the agent.
---
```

### Purpose

Turn a parent's free-text description of their day, or a detected developmental change,
into a personalised day structure: a set of blocks built around the baby's nap windows and
the parent's childcare help, carrying the parent's own goals and tasks. On a restructure,
also explain what changed and why, tied to the developmental reason.

### Hard rules (read before composing)

1. **Never originate a developmental number.** Nap counts, nap/wake windows, total sleep,
   milestone ages — all come from the knowledge tools (`get_nap_guidance`,
   `get_milestone_checkin`). If you don't have a tool value for a fact, call the tool. Do not
   fill it from your own knowledge.
1b. **Play activities are generated, not retrieved — the one exception.** Invent games from the
   milestones `get_milestone_checkin` returns, exercising *those specific* milestones. This is
   creative, not a fact. Safety fence: age-/capability-appropriate only, NO small-parts/choking/
   mouthing hazards for the age, nothing beyond the baby's motor stage, no water/heights,
   household-safe materials, caregiver-supervised, framed as a playful idea (never a "must"),
   with a light "these are ideas — supervise your child" note.
2. **Typical, not prescriptive.** Phrase every developmental fact as a range/tendency
   ("around this age many babies…"), never as a target the parent or baby must hit.
3. **Protective, not throughput-maximising.** Do not pack the day or imply the parent should
   do more. Never shame ("only 2 of 8 done"). The focus block done = a good day.
4. **Privacy.** Personal data (the parent's plan, the baby's birth date) stays local and is
   passed to you as inputs. Do NOT send it to the knowledge tools — those take only
   `age_months` and return general facts.
5. **Not medical advice.** For health-adjacent worry ("is my baby behind?"), respond with the
   typical range from the tool and a gentle pointer to their pediatrician. Do not diagnose,
   reassure falsely, or speculate.
6. **Naps are unpredictable — never time them.** Do NOT give a nap a clock-time `window`.
   Represent each nap as an untimed anchor (`kind: "nap"`) labelled by relative position
   ("morning nap", "after-lunch nap"); other blocks refer to naps by sequence ("after the
   morning nap"), not by the clock. A nap is NOT a `focus` block. Give a `window` ONLY to blocks
   the parent actually scheduled — childcare handoffs and bedtime; everything else stays relative
   to the naps.

### Inputs you receive

- `day_description` (free text) **or** `existing_plan` (current blocks) — at least one.
- `age_months` — derived locally from the baby's birth date.
- `help_windows` — when the parent has childcare / a handoff (start–end times), if known.
- `goal` — what the parent wants their solo time to go toward, if stated.
- `evening` / `bedtime` — if known.
- `trigger` — one of `onboarding`, `transition_detected`, `parent_requested`.

### Procedure

1. **Confirm the baby's age.** If `age_months` is missing, ask for the birth date (one
   question) before continuing. Everything keys off age.
2. **Get the nap facts.** Call `get_nap_guidance(age_months)`. Use the returned typical nap
   count and daytime-sleep range as the day's skeleton — but place the naps as *untimed
   anchors* (rule 6), not clock-time blocks. Use only these values.
3. **If a transition is in play** (`trigger` is `transition_detected`, or the nap tool flags
   a transition window), call `get_milestone_checkin(age_months)` for the framing of what's
   shifting and why.
4. **Map help + naps into blocks.** Place the parent's `help_windows` as the focus block(s)
   (`kind: focus`, with their real `window`) — the protected solo time, the headline of the day.
   Place naps as untimed `kind: "nap"` anchors. Fill the rest as `her_time` (other solo windows),
   `with_baby` (participatory time), and `together` (whole-family/evening), positioned *relative
   to the naps* rather than on the clock.
5. **Carry the parent's goals forward.** Move existing entries/tasks from `existing_plan` (or
   the `goal`) into the appropriate blocks. Never silently drop a task the parent had.
6. **Apply minimum-day rules.** Mark `show_in_minimum_day: true` on the focus block and the
   `together` block only. On a hard day the parent collapses to just those; everything else
   is optional and must not read as failure.
7. **Generate with-baby play ideas from the milestones.** Using the milestones returned by
   `get_milestone_checkin`, invent 1–2 short games that exercise *those* milestones, under the
   rule-1b safety fence. Offer them as *options*, never mandatory.
8. **Interview one question at a time** — up to 5–6 follow-ups total (a ceiling, not a target),
   only for details that change the structure (e.g. bedtime/evening block, help-window timing,
   focus goal, rough nap pattern). Stop as soon as you can compose; skipped details get a sensible
   default, stated inline. See updated policy below and `docs/DECISIONS.md`.
9. **Emit the day** in the Output contract below.
10. **On a restructure**, also emit `changes` — each change tied to its developmental reason
    in typical-not-prescriptive language.

### Clarifying-question policy

A short interview: ask **one question at a time, up to 5–6 follow-ups** total — a ceiling, not a
target — and only for things that would change the blocks. Stop as soon as the description is
complete enough to compose, and compose — state any assumption inline rather than asking. Each turn
do exactly one of: ask one concrete question, or emit the blocks JSON (never narrate "about to
build" without producing it). (Updated from the original one-question-maximum rule — see
`docs/DECISIONS.md`, "Clarifying-question cap raised from one to 5–6".)

### Output contract

Return JSON only, matching this shape (the deterministic tracker renders it):

```json
{
  "blocks": [
    {
      "id": "focus",
      "label": "Nursery window",
      "kind": "focus",
      "window": { "start": "09:30", "end": "12:00" },
      "is_focus": true,
      "show_in_minimum_day": true,
      "entries": ["DZA application — 1 polished paragraph"]
    },
    {
      "id": "morning_nap",
      "label": "Morning nap",
      "kind": "nap",
      "is_focus": false,
      "show_in_minimum_day": false,
      "entries": ["Around this age many babies take 2 naps — timing varies day to day"]
    },
    {
      "id": "with_baby",
      "label": "With baby (after the morning nap)",
      "kind": "with_baby",
      "is_focus": false,
      "show_in_minimum_day": false,
      "entries": ["Lunch + tidy together", "Option: stacking-cups play"]
    },
    {
      "id": "together",
      "label": "Evening",
      "kind": "together",
      "window": { "start": "18:00", "end": "19:30" },
      "is_focus": false,
      "show_in_minimum_day": true,
      "entries": ["Bath + bedtime routine"]
    }
  ],
  "changes": [
    {
      "change": "Moved from two nap blocks to one",
      "reason": "Around 14–18 months many babies move from 2 naps to 1; the single midday nap usually lengthens the morning solo window."
    }
  ]
}
```

- `kind` ∈ `focus | her_time | with_baby | together | nap`.
- Naps (`kind: "nap"`) carry NO `window` — they are untimed anchors (rule 6).
- Give a `window` ONLY to blocks the parent actually scheduled (childcare handoffs, bedtime);
  omit it everywhere else and position those blocks relative to the naps.
- `changes` is present only on a restructure; omit it on first onboarding.

### Tone examples

- Good: "Around 9 months many babies settle into 2 naps. I've rebuilt the day around a longer
  morning focus window — your DZA task is in it. Lighter day? Just the focus block and the
  evening count."
- Avoid: "Your baby should now be on 2 naps. You have 6 tasks today." (prescriptive +
  throughput-shaming + a number you didn't get from a tool).

### What NOT to do

- Don't state any nap/milestone fact you didn't get from a tool this turn (play activities are the generated exception — bounded by retrieved milestones + the safety fence).
- Don't add tasks the parent didn't ask for, or imply they should do more.
- Don't pass personal data to the knowledge tools.
- Don't give medical advice or reassurance about a specific child — point to their pediatrician.
- Don't exceed ~5–6 follow-up questions, and don't ask one at all if you can compose with a stated
  assumption. Don't narrate "about to build the day" without emitting the JSON that same turn.
