# Decisions (and why) — so we don't reopen settled questions

## ADK over raw Gemini function-calling
Our agent loop is simple enough to hand-roll, but: ADK is a gradable concept in a Google
ADK competition; `McpToolset` is the ready-made glue to our stdio MCP server (raw FC would
make us hand-write an MCP client); and ADK keeps the Skill concept reachable. Raw FC would
only win if we dropped MCP and served facts as in-process functions — which costs two
concepts and the privacy story. Status: **ADK.**

## One agent, not three
The onboarding/restructure flow is the only place the model drives control flow. The three
knowledge lookups are *tools*, not agents. Calling them "three agents" is the NutriGuard
overcount (sequential function calls relabelled as agents) — weaker and less credible than
one real agent with correct facts discipline. Status: **one agent.**

## MCP server over a plain text/JSON file
The file is fine for *storage*. The tool is a deterministic executable lookup (no model
in the path for facts) AND a gradable concept. We still keep the data as JSON; the server
wraps it. Status: **local stdio MCP server.**

## Eval harness is deterministic code, not an agent
It checks a hard property (facts trace to tools). A model-based judge would reintroduce the
non-determinism we're trying to catch. Optional LLM-as-judge only for soft qualities (tone).
Status: **deterministic harness, optional judge for tone.**

## The compose-baby-day Skill is margin, not core
It can tick a 5th concept (Agent skills) and packages the restructure method cleanly, but a
runtime-specific Skills mechanism may pull Antigravity into scope. We clear the 3-of-6 floor
without it (ADK + MCP + Security + Deployability). Status: **build if time allows.**

## Facts discipline is the differentiator
Across every layer: the model never originates a developmental number. This is what we
contrast against health agents that *claim* grounding but let the model estimate the number.
Status: **load-bearing; protected by `agent/instructions.py` + `eval/`.**

## Milestone bands finer than nap bands
Naps use eight coarse bands (0-3, 4-5, 6-8, 9-12, 12-18, 18-24, 24-36, 36-60 mo). Milestones
use one band per source-table age (1, 2, 3...16, 18, 20, 22, 24, 28, 30, 33 mo, then 3/4/5/6 yr),
because infant development moves fast and the source (Scharf et al., Pediatrics in Review
2016;37(1):25-37) reports it that finely — a 9- and a 12-month-old should not get the same
milestones the way they'd share a nap band. Consequence: the two domains no longer share
identical band *edges*, only the same age->band *lookup mechanism*. ARCHITECTURE.md's contract
section was updated to say "shared lookup, not shared edges." Bands are contiguous integer-month
ranges so every age maps to exactly one band; the loader/tool logic is unchanged. Status:
**milestones finer-banded; nap bands unchanged.**

## Play activities are generated, not curated
Games are not facts — there are many valid ones, and a wrong game isn't a false claim the way
a wrong nap number is. So play is the one place the model creates rather than retrieves. The
*milestones* it targets are still retrieved (a fact, from get_milestone_checkin); the *games*
are generated to exercise those milestones. This is bounded generation, NOT hallucination —
and calling it hallucination would undercut our facts-discipline headline. Required guardrail:
an infant-safety fence in agent/instructions.py (no choking/small-parts/mouthing hazards for
the age, nothing beyond motor stage, supervised, framed as an idea not a must). Consequence:
no play.json, no get_play_suggestions; the milestone data now feeds both the check-in and the
game generation. Status: **play generated under a safety fence; milestone + nap stay curated.**

## Onboarding persona — parent-wellbeing clinician, pediatric grounding for the baby
The onboarding voice centres on the PARENT's wellbeing: warm, authoritative, attentive to how
they're coping — if they signal overwhelm or illness, it offers a minimum day rather than a full
one. That is the differentiator made audible (§2.5 "protective, not throughput-maximising").
Anything about the BABY — naps, play ideas — stays pediatrically grounded: facts from the tools,
age-appropriate play under the safety fence. So it's a clinician who looks after the parent, with
a pediatrician's grounding for the child's routine — not a baby-tracker with a chat skin, and not
a mental-health assessor of the parent. Lives in agent/instructions.py (protected; edit only after
the conversational-onboarding plan is approved). Status: **parent-wellbeing voice + pediatric
facts; see docs/PLAN-conversational-onboarding.md.**

## Clarifying-question cap raised from one to 5–6
The original rule (brief §4 + the compose-baby-day Skill) capped clarifying questions at ONE, to
spare a depleted parent friction. The conversational onboarding is an interview — birth date, then
free text, then targeted follow-ups — so one is too few. New cap: up to 5–6 follow-ups, asked one
at a time, only for things that change the day, always skippable. The cap is a CEILING, not a
target: the agent stops as soon as it has enough, and a one-line free-text answer must still yield
a usable day without nagging (protective principle preserved). To apply: update the Skill's
clarifying-question policy (one → max 5–6) and soften brief §4. Status: **max 5–6 questions; replaces
the one-question rule; see docs/PLAN-conversational-onboarding.md.**
