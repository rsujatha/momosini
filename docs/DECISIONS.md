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
