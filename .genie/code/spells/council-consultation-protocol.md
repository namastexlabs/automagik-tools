---
name: Council Consultation Protocol
description: How the council-review spell invokes council member agents during plan mode
genie:
  executor: [CLAUDE_CODE, CODEX, OPENCODE]
forge:
  CLAUDE_CODE:
    model: sonnet
  CODEX: {}
  OPENCODE: {}
---

# Council Consultation Protocol

**Purpose:** Define how the council-review spell invokes council member agents during plan mode for architectural decisions.

---

## What Council Members Are

**Council members** are standalone agents at `.genie/agents/` that:
- Analyze proposals from their unique perspective
- Provide focused recommendations
- Vote on architectural decisions
- Never execute code (advisory only)

**Council Members:**
| Agent | Role | Philosophy |
|-------|------|------------|
| nayr | The Questioner | "Why? Is there a simpler way?" |
| oettam | The Benchmarker | "Show me the benchmarks." |
| jt | The Simplifier | "Delete code. Ship features." |
| yort | The Breach Hunter | "Where are the secrets? What's the blast radius?" |
| erdnis | The Ergonomist | "If you need to read the docs, the API failed." |

**Distinction:** The council advises, agents execute. The spell orchestrates council member invocation.

---

## When Council Is Invoked

**Auto-Invocation:** The council-review spell auto-activates during **plan mode**.

**Topic-Based Routing:**

| Topic Category | Members Invoked | Detection Keywords |
|----------------|-----------------|-------------------|
| Architecture | nayr, oettam, jt | "redesign", "refactor", "architecture" |
| Performance | oettam, nayr, jt | "optimize", "slow", "benchmark" |
| Security | nayr, jt, yort | "auth", "security", "secret" |
| API Design | nayr, jt, erdnis | "API", "interface", "SDK", "DX" |
| Full Review | all 5 | "full review", "architectural review" |

**Default:** Core trio (nayr, oettam, jt) if no specific triggers detected.

---

## Consultation Workflow

### Spell-Based Invocation

```
Plan Mode Activated
  ↓
Council Review Spell Auto-Loads
  ↓
User Describes Task
  ↓
Spell Detects Topic Triggers
  ↓
Smart Routing Selects Council Members
  ↓
Parallel Agent Invocation (Task tool)
  ↓
Agents Provide Perspectives
  ↓
Spell Synthesizes Advisory
  ↓
User Reviews + Decides
  ↓
Plan Proceeds
```

### Agent Invocation Pattern

```typescript
// Parallel invocation of selected council members
const members = selectCouncilMembers(planTopic);

members.forEach(agent => {
  Task({
    subagent_type: "Plan",
    prompt: `You are ${agent.name}, a council member with perspective: "${agent.philosophy}"

    Review this plan from your perspective:
    ${planContext}

    Provide:
    1. Your analysis (2-3 key points)
    2. Your vote: APPROVE / REJECT / MODIFY
    3. Rationale for your vote
    4. Specific recommendations (if any)

    Be concise. Focus on your specialty.`
  });
});
```

---

## Advisory Output Format

```markdown
## Council Advisory

### Topic: [Detected Topic]
### Members Consulted: [List]

### Perspectives

**nayr (Questioning):**
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**oettam (Performance):**
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**jt (Simplicity):**
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**yort (Security):** (if invoked)
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**erdnis (DX):** (if invoked)
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

### Vote Summary
- Approve: X
- Reject: X
- Modify: X

### Synthesized Recommendation
[Council's collective advisory based on perspectives]

### User Decision Required
The council advises [recommendation]. Proceed?
```

---

## Voting Mechanism (Advisory)

### Advisory Thresholds (Informational)

| Active Voters | Strong Consensus | Weak Consensus | Split |
|---------------|------------------|----------------|-------|
| 3 | 3/3 agree | 2/3 agree | No majority |
| 4 | 4/4 or 3/4 agree | 2/4 agree | Even split |
| 5 | 5/5 or 4/5 agree | 3/5 agree | No majority |

**Vote Options:**
- **Approve** - Recommended as proposed
- **Modify** - Recommended with specific changes
- **Reject** - Not recommended (provide alternative)

**Key Principle:** User always decides. Council provides informed perspective, not binding judgment.

---

## Permissions & Constraints

### What Council Members CAN Do

- Read entire codebase (full analysis capability)
- Use all spells (evidence-based thinking)
- Multi-turn consultation (resume for clarification)
- Parallel invocation (all members at once)

### What Council Members CANNOT Do

- Execute code changes (no Edit/Write to codebase)
- Create branches (no git operations)
- Run tests (no execution environment)
- Deploy/publish (no release operations)
- Delegate to other agents (advisory only)

---

## Integration Points

**Main Spell:** `@.genie/spells/council-review.md`
**Routing:** `@.genie/spells/routing-decision-matrix.md`
**Agents:**
- `@.genie/agents/nayr.md`
- `@.genie/agents/oettam.md`
- `@.genie/agents/jt.md`
- `@.genie/agents/yort.md`
- `@.genie/agents/erdnis.md`

---

## Success Metrics

**Council review is effective when:**
- Plans are reviewed from multiple angles before implementation
- Potential issues are identified early
- User feels informed, not blocked
- Perspectives are distinct (not rubber-stamping)

**Red flags:**
- All votes unanimous every time (personas not differentiated)
- User skips council review (advisory not valued)
- Recommendations are vague (not actionable)

---

**Remember:** The council advises, the user decides. Our value is diverse perspective, not gatekeeping.
