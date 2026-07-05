# Momosini: A Privacy-First Concierge Agent for New Parents

**Track:** Concierge Agents
**Submitting Team:** suja-capstone (Sujatha)
**Video Demo URL:** [YouTube Link (To be attached)]
**Project Demo URL:** [Cloud Run URL / GitHub Link (To be attached)]

---

## Executive Summary
**Momosini** is a privacy-first concierge agent that structures a new parent's day around their baby's developmental stage. Traditional planners optimize for *throughput* and assume you control your own schedule. For new parents that assumption is structurally wrong: their available time is defined by caregiving windows, nap sequences, and childcare handoffs.

By separating the interface (a deterministic tracker) from the reasoning engine (a Google ADK agent) and grounding pediatric knowledge in a local Model Context Protocol (MCP) server, it delivers a protective, dynamic schedule: warm conversational onboarding, automatic restructuring when the baby hits a developmental transition (like dropping a nap), and age-appropriate play ideas.

---

## 1. The Pitch: Problem, Solution, and Core Value

### The Problem
New parents operate under depleted cognitive load, sleep deprivation, and a daily calendar they do not control. Standard planners force parents to fit tasks into rigid hourly blocks, which leads to feelings of overwhelm and failure when a baby's unpredictable sleep cycles disrupt the plan. 
Furthermore, a baby's routine is highly dynamic; sleep windows and developmental milestones shift rapidly between 0 and 24 months. Traditional systems are static, requiring manual recalibration of schedules, while commercial baby trackers focus on logging past events rather than planning the day ahead.

### The Solution
Momosini shifts the scheduling paradigm. It organizes around the time the parent *doesn't* control—the baby's sleep and developmental needs—and adjusts as the baby grows. 

```
A generic planner helps you spend the time you control; this one organises around the time you don't — your baby's — and changes as your baby does.
```

### Why Agents (and Not Just a Chatbot)?
A plain LLM chatbot could *hold* this conversation—it could read a parent's free-text description and reply warmly. So the interesting question is not "why not an app," but "why an agent rather than a chatbot." Two things this problem demands are exactly the things a chatbot cannot safely do.

First, a chatbot would **generate** developmental facts from its training data: nap windows, wake times, milestone ages. These are precisely the numbers a sleep-deprived parent must be able to trust, and precisely where an LLM is most likely to hallucinate. Second, a chatbot only emits text; it has no dependable way to decide when it has gathered enough, when to look something up, or how to return a structured plan the interface can render.

An agent closes both gaps through **agency**—the capacity to reason, act, and decide in a loop rather than simply respond. When a parent types *"I'm exhausted, my mother is coming from 10 to 1, and I need to polish one paragraph of my proposal,"* the agent:
1. **Grounds facts through action, instead of generating them.** Rather than inventing sleep ranges, it *decides* to call deterministic knowledge tools (our MCP server) and uses only what they return—so every developmental number traces back to a cited source.
2. **Drives its own control flow.** It chooses which tools to call and when, judges whether the day's structure is complete, asks a gentle follow-up only if a real gap remains, and then stops on its own.
3. **Acts, rather than only answering.** It composes a structured, relative-time day plan the tracker renders, and proactively restructures the day as the baby hits developmental transitions.
4. **Improves with history, instead of starting over.** Because the parent's schedule, tasks, and the baby's birthday are already tracked on-device, the agent has a growing record to reason over. A stateless chatbot treats every turn as new; an agent can use that history as context—recognising that this baby dropped a nap early, or that mornings are the parent's only focus window—so each day's plan can evolve from the last rather than resetting. Personalization compounds precisely because an agent reasons over accumulated state, not a single prompt.

In short: a chatbot answers questions; this agent reasons about the parent's day, uses tools to stay factually grounded, and acts by composing a safe, structured plan.

---

## 2. Technical Architecture & Course Concepts

The project demonstrates five core course concepts: **ADK (Agent Development Kit)**, **MCP Server**, **Security & Privacy Features**, **Deployability**, and **Agent Skills**.

```mermaid
sequenceDiagram
    autonumber
    actor Parent as Parent (Browser)
    participant Web as Web Seam (FastAPI)
    participant Agent as ADK Agent (LlmAgent)
    participant MCP as Local stdio MCP Server
    participant DB as Curated JSON (Sourced)

    Parent->>Web: POST /converse (Birthday & Day Description)
    Web->>Agent: Run onboarding turn (Session Context)
    Note over Agent: Model reasons & decides<br/>to retrieve facts
    Agent->>MCP: Call get_nap_guidance(age_months)
    MCP->>DB: Read naps.json
    DB-->>MCP: Sourced Sleep Data [A/B/C]
    MCP-->>Agent: JSON Results
    Agent->>MCP: Call get_milestone_checkin(age_months)
    MCP->>DB: Read milestones.json
    DB-->>MCP: Sourced Milestones [B]
    MCP-->>Agent: JSON Results
    Note over Agent: Model evaluates completeness<br/>& applies Safety Fence
    alt Session incomplete (under 5-6 questions)
        Agent-->>Web: Return clarifying question
        Web-->>Parent: Display next interview question
    else Session complete or parent skips
        Note over Agent: Generate safe play activities<br/>& assemble schedule blocks
        Agent-->>Web: Return composed blocks JSON
        Web-->>Parent: Render Day Blocks (Sanitized)
        Note over Parent: Save to LocalStorage
    end
```

### Concept 1: Agent / Multi-Agent System (ADK)
The agent layer is built using the Google Agent Development Kit (ADK) `LlmAgent`. Rather than using a rigid, hardcoded pipeline of LLM calls, the agent's control flow is entirely model-driven. The agent is initialized with a system instruction that outlines its persona and behavioral constraints, equipped with the local MCP toolset, and guided by a declarative `compose-baby-day` Skill. The agent loops: it decides which tools to call, observes tool outputs, decides whether to ask a clarifying question, and composes the final day plan when ready.

### Concept 2: Local Stdio MCP Server
To guarantee the model never fabricates developmental facts, we built a local **Model Context Protocol (MCP)** server (`FastMCP`) using `stdio` transport. The server exposes two tools: `get_nap_guidance` and `get_milestone_checkin`. When the agent needs developmental sleep ranges or milestones, it spawns the MCP server as a subprocess and queries the tools. This decoupling ensures the knowledge lookup remains 100% deterministic and auditable.

### Concept 3: Security & Privacy Features
Parents are highly protective of their family's data. To ensure privacy, we implemented a strict boundary:
- **Zero-Storage Backend:** The FastAPI server holds conversations in-memory during onboarding but stores no persistent data.
- **On-Device Storage:** The parent’s schedule, tasks, progress, and the baby's exact birthdate are saved exclusively in the browser's `LocalStorage`.
- **Anonymized Tool Queries:** When the agent invokes MCP tools, it passes only the baby's age in integer months (e.g., `9`). No personal details, names, or schedules are ever sent to the MCP server or out to the model API.

### Concept 4: Deployability
The application is packaged into a single Docker container. The FastAPI application exposes the frontend and `/converse` API endpoints, while the backend agent automatically handles spawning and communicating with the stdio MCP server inside the same container. The container is deployed to **Google Cloud Run**. Because Cloud Run is serverless and scales down or across instances, we configure `--max-instances=1` and set session affinity. This guarantees that multi-turn onboarding sessions remain pinned to the warm memory of a single container instance during the user demo.

### Concept 5: Agent Skills
To separate the agent's core identity and rules from its procedural capabilities, we implemented the **Agent Skills** pattern. The onboarding and restructuring logic is codified in a discrete, runtime-loadable Skill definition: `compose-baby-day` (located at `agent/skills/compose-baby-day/SKILL.md`). The system instructions set the baseline persona and clinical safety rules, while the detailed schedule composition methodology, interview policies, and blocks JSON contract are dynamically loaded on demand and appended to the model's instructions at runtime via `build_compose_agent()`. This makes the agent's procedural methods modular and easily extensible without altering the core codebase.

---

## 3. Implementation Details: The "Facts Discipline"

Our core technical differentiator is the implementation of a strict **Facts Discipline**. In standard clinical or scheduling agents, models are given free rein to estimate windows, naps, or developmental advice. This leads to dangerous or incorrect information. In Momosini, the model is strictly forbidden from originating developmental facts.

### 1. Evidence-Tiered Knowledge Databases
We curated our developmental knowledge files (`naps.json` and `milestones.json`) from authoritative medical literature. Every record is explicitly tagged with a source and an evidence confidence tier:
*   **[A] Consensus Guideline:** E.g., American Academy of Sleep Medicine (AASM/AAP) or World Health Organization (WHO).
*   **[B] Research Literature:** E.g., Galland et al. (2012) systematic reviews on infant sleep, and Scharf et al. (2016) in *Pediatrics in Review* for milestones.
*   **[C] Practical Convention:** Common clinical sleep conventions (like wake windows) that are widely used but lack large-scale consensus clinical trials.

The agent's system instruction strictly mandates that sleep ranges and milestones must be phrased as *typical ranges* (never absolute prescriptions) and must trace directly back to the active tools.

### 2. Generated Play Activities vs. Grounded Facts
While sleep durations and developmental milestones are retrieved facts, **Play Activities** are creatively generated by the model. This is a deliberate distinction: games are not medical facts, and generating play ideas is a safe creative space. 
However, to ensure safety, this generation is bounded by a strict **Infant-Safety Fence** in the agent's instructions:
> Activities must be age-appropriate; carry NO small-parts, choking, or mouthing hazards; require caregiver supervision; stay within the baby's current motor stage (no unsupported sitting/standing if not yet achieved); and be framed strictly as a playful idea, never a developmental requirement.

### 3. The Clinical Parent-Wellbeing Persona
The agent's persona is designed to protect parent wellbeing:
- If a parent indicates exhaustion, illness, or overwhelm in the text, the agent bypasses complex routines and offers a **Minimum Day** (consisting of only one protected focus task and family evening time), reassuring the parent that doing one thing is a successful day.
- To prevent user fatigue, the onboarding interview is capped at a ceiling of **5 to 6 questions**, asked one at a time. The parent can skip or provide brief answers, in which case the agent fills gaps with sensible defaults and documents them.

### 4. Deterministic Render Guard
To prevent scheduling errors if the model outputs overlapping times, the frontend tracker applies a deterministic `sanitizeWindows()` routine. If the model accidentally assigns overlapping clock slots or zero-length blocks, the frontend automatically separates or filters them before rendering.

---

## 4. Evaluation and Verification

To ensure the Facts Discipline is maintained across code modifications, we built a deterministic **Evaluation Harness** (`pytest eval/`). The harness runs offline simulation checks on the agent:
1.  **Hallucination Detector:** Parses the LLM's conversation history and matches all developmental numbers (naps, sleep hours, milestone ages) against the values returned by the MCP tools during that session. If a number does not exist in the tool trace, the test fails.
2.  **Blocks Contract Verification:** Checks that the JSON returned by the agent strictly adheres to the schema expected by the tracker UI.
3.  **Tone Judge:** An optional LLM-as-judge test that evaluates agent responses against clinician warmth and checks if the agent correctly triggered a "Minimum Day" when presented with simulated parental overwhelm.

---

## 5. The Build Journey

The project didn't arrive at this shape on day one — several design decisions changed after we tested the earlier version against real use:

*   **From three agents to one.** Our first instinct was to frame the nap lookup, the milestone lookup, and the day composer as three cooperating agents. On review, that was overcount: relabeling sequential function calls as "agents" inflates the concept count without adding real agency. We collapsed to the honest architecture — the lookups are deterministic *tools*, and there is exactly **one** agent, the composer, genuinely deciding which tools to call and when. Fewer claimed agents, but a more credible one.
*   **The clarifying-question cap went up, not down.** The original design capped onboarding at a single clarifying question, to spare a sleep-deprived parent friction. Once we rebuilt onboarding as a real interview — birthday, free text about the day, then targeted follow-ups — one question couldn't fill the gaps a free-text answer leaves. We raised the ceiling to 5–6 questions, one at a time, always skippable, with defaults documented when the parent opts out — a ceiling, not a target: the agent stops as soon as it has enough.
*   **Milestone bands couldn't reuse the nap bands.** We assumed both domains would share identical age-band edges for simplicity. Curating milestone data against Scharf et al. (2016) proved otherwise: early development moves fast enough that a 9-month-old and a 12-month-old need different milestone check-ins, even within the same nap band. We kept a shared age-lookup *mechanism* but let each domain define its own band edges.
*   **Rate limits pushed us toward model-agnosticism.** Local testing against Gemini's free tier hit rate limits mid-build. Rather than block on that, we added LiteLLM as an optional wrapper so the model backend swaps with a single environment variable — we verified the agent runs correctly against both Gemini and DeepSeek. What started as a workaround became a genuine deployability strength.
*   **Serverless session state was the deployment surprise.** Keeping onboarding conversations in-memory is simple for a prototype, but Cloud Run's serverless scaling can split a live conversation across instances or drop it entirely. We caught this before the demo, not after, and mitigated it with `--max-instances=1` (and `--min-instances=1` to keep one instance warm) — an honestly-logged limitation rather than a hidden one, with a real fix (a shared session store like Memorystore) named as future work.

---

## 6. Reflections and Future Work

### Future Work
In future iterations of Momosini, we plan to:
1.  **Extend Curated Domains:** Include feeding schedules (solids transition), safety checks, and motor developmental exercises.
2.  **Pediatrician Escalation Pathways:** Integrate developmental "Red Flags" from the AAP guidelines, formatting them as deterministic alerts that recommend pediatrician consultation without the model attempting a diagnosis.
3.  **Cross-Device Synchronization:** Implement encrypted, local-first syncing (using WebRTC or private user database containers) to share the day's routine seamlessly between parents and caregivers.

---

## Conclusion
Momosini proves that AI agents can act as empathetic, reliable concierge assistants when properly bounded. By placing clinical facts in deterministic MCP tools and focusing the agent's creativity strictly on safe play activities and empathetic conversation, we have built a concierge system that respects parental boundaries, adapts dynamically to a child's growth, and provides genuine, everyday value.
