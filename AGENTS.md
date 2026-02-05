# Project Context for AI Agents

## What This Is

A podcast exploring technological innovations that shaped modern life—how they were discovered, how they spread, and their ripple effects. Think Acquired, but focused on *innovations* rather than companies.

**Hosts:** Jeff and Cyrus
**Status:** Pre-pilot planning phase

---

## Episode Structure

Each episode follows a 3-act structure with intro and outro:

| Section | Target Time | Purpose |
|---------|-------------|---------|
| **INTRO: The Hook** | 10-15 min | Impact stats + "world before" to set the stakes |
| **ACT 1: Discovery** | 20-25 min | The human story of invention—people, failures, breakthroughs |
| **ACT 2: Diffusion** | 25-35 min | The messy middle—resistance, enabling conditions, tipping point |
| **ACT 3: Aftermath** | 25-30 min | Consequences—immediate effects, winners/losers, structural changes |
| **OUTRO: Open Questions** | 5-10 min | 2-3 unresolved questions to leave listeners thinking |

See `episode_template.md` for detailed guidance on each section.

---

## Per-Episode Workflow

Each episode has **three files** in its folder:

### 1. Raw Research (`research.md`)
**Created by:** Claude
**Purpose:** Comprehensive research organized by episode section

- Covers all sections of the episode structure
- More is better—be exhaustive
- Highlight best material with ⭐
- Link sources inline
- Include a "Key Sources" section for deep-dive recommendations
- Flag claims that need verification

**Template:** `templates/research_template.md`

### 2. Episode Notes (`notes.md`)
**Created by:** Jeff & Cyrus
**Purpose:** Editorial synthesis and decisions

- What to include from the research
- Connections and throughlines
- Pacing and emphasis decisions
- Who drives which section
- Questions for each other

**Template:** `templates/episode_notes_template.md`

### 3. Script/Outline (`script.md`)
**Created by:** Claude (based on research + notes)
**Purpose:** Recording document

- Structured beats for each section
- Scripted intros/transitions
- Key stats and details to hit
- Flexible enough for genuine conversation

**Template:** `templates/script_template.md`

---

## Workflow Steps

```
1. INITIAL RESEARCH
   Claude creates comprehensive research.md from the template
   ↓
2. REVIEW & REFINE
   Jeff/Cyrus review, request deeper dives on specific areas
   Claude adds to research.md (all refinements stay in one file)
   ↓
3. EPISODE NOTES
   Jeff & Cyrus create notes.md—their synthesis and editorial decisions
   (Claude may provide suggestions if asked)
   ↓
4. SCRIPT
   Claude creates script.md based on research.md + notes.md
   ↓
5. RECORD
```

---

## Folder Structure

```
/
├── overview.md              # Podcast concept, format, goals
├── episode_template.md      # Episode structure reference (the 3-act framework)
├── topics.md                # Episode topic ideas
├── pilot_checklist.md       # Planning checklist for pilot
├── AGENTS.md                # This file (AI instructions)
│
├── templates/               # Per-episode file templates
│   ├── research_template.md
│   ├── episode_notes_template.md
│   └── script_template.md
│
└── episodes/                # Episode folders
    └── [topic-name]/
        ├── research.md
        ├── notes.md
        └── script.md
```

---

## The Core Angle

Most tech/business content skips from "invention" to "winner." This podcast emphasizes the **diffusion story**—the messy middle:
- Who resisted and why
- What complementary tech was needed
- The tipping point from novelty to inevitability
- Second-order societal effects

---

## Tone & Style Guidelines

- **Narrative-driven**, not textbook summaries
- **Human drama** over technical achievement
- **Accessible explanations**—mental models, not engineering diagrams
- **No "dorm room" debates**—avoid simplistic good/bad framing
- **Historical empathy**—don't judge past decisions by today's values without context

---

## Research Guidelines

When researching, prioritize:
1. Vivid "before" scenarios (what life was like without the innovation)
2. Human stories—inventors, resisters, winners, losers
3. The diffusion/adoption story (not just the breakthrough)
4. Specific anecdotes with names, dates, verifiable details
5. Statistics that capture scale of change

**Always:**
- Highlight the best material (⭐) so it's easy to find
- Flag claims that need fact-checking
- Suggest primary sources when possible
- Note when information might be uncertain or contested

**Avoid:**
- Generic overviews without specific details
- Over-explaining technical mechanisms
- Treating adoption as inevitable (resistance is often the story)

---

## AI Limitations to Remember

- Knowledge has a cutoff date—verify recent information independently
- AI may present plausible-sounding but incorrect information confidently
- Quotes attributed to historical figures are often inaccurate—always verify
- AI tends to oversimplify complex historical debates
- Different sources may tell different versions; AI may pick one arbitrarily

**When in doubt, go to the primary source.**

---

*Last updated: February 2026*
