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

**Purpose:** Define how the council-review spell invokes council member agents (now hybrid agents in code collective) during plan mode for architectural decisions.

---

## What Council Members Are

**Council members** are hybrid agents at `.genie/code/agents/` that:
- Analyze proposals from their unique perspective
- Provide focused recommendations
- Vote on architectural decisions
- Can also execute related work (hybrid mode)

**Council Members (10 Hybrid Agents):**
| Agent | Role | Philosophy |
|-------|------|------------|
| questioner | The Questioner | "Why? Is there a simpler way?" |
| benchmarker | The Benchmarker | "Show me the benchmarks." |
| simplifier | The Simplifier | "Delete code. Ship features." |
| sentinel | The Breach Hunter | "Where are the secrets? What's the blast radius?" |
| ergonomist | The Ergonomist | "If you need to read the docs, the API failed." |
| architect | The Systems Thinker | "Talk is cheap. Show me the code." |
| operator | The Ops Realist | "No one wants to run your code." |
| deployer | The Zero-Config Zealot | "Zero-config with infinite scale." |
| measurer | The Measurer | "Measure, don't guess." |
| tracer | The Production Debugger | "You will debug this in production." |

**Distinction:** These are hybrid agents - they can advise AND execute. The spell orchestrates council member invocation in review mode.

---

## When Council Is Invoked

**Auto-Invocation:** The council-review spell auto-activates during **plan mode**.

**Topic-Based Routing:**

| Topic Category | Members Invoked | Detection Keywords |
|----------------|-----------------|-------------------|
| Architecture | questioner, benchmarker, simplifier, architect | "redesign", "refactor", "architecture" |
| Performance | benchmarker, questioner, architect, measurer | "optimize", "slow", "benchmark", "profile" |
| Security | questioner, simplifier, sentinel | "auth", "security", "secret" |
| API Design | questioner, simplifier, ergonomist, deployer | "API", "interface", "SDK", "DX" |
| Operations | operator, tracer, measurer | "deploy", "ops", "on-call", "runbook" |
| Observability | tracer, measurer, benchmarker | "observability", "tracing", "metrics", "debugging" |
| Systems | architect, measurer, benchmarker | "concurrency", "threading", "backwards compat" |
| Deployment/DX | ergonomist, deployer, operator | "CI/CD", "preview", "zero-config" |
| Full Review | all 10 | "full review", "architectural review" |

**Default:** Core trio (questioner, benchmarker, simplifier) if no specific triggers detected.

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

**questioner (Questioning):**
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**benchmarker (Performance):**
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**simplifier (Simplicity):**
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**sentinel (Security):** (if invoked)
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**ergonomist (DX):** (if invoked)
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**architect (Systems):** (if invoked)
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**operator (Operations):** (if invoked)
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**deployer (Deployment DX):** (if invoked)
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**measurer (Measurement):** (if invoked)
- [Key point]
- Vote: [APPROVE/REJECT/MODIFY]

**tracer (Production):** (if invoked)
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
| 6-7 | 6/7 or 5/6 agree | 4/7 agree | < 50% majority |
| 8-10 | 8/10+ agree | 6/10 agree | < 50% majority |

**Vote Options:**
- **Approve** - Recommended as proposed
- **Modify** - Recommended with specific changes
- **Reject** - Not recommended (provide alternative)

**Key Principle:** User always decides. Council provides informed perspective, not binding judgment.

---

## Permissions & Constraints

### What Council Members CAN Do (Review Mode)

- Read entire codebase (full analysis capability)
- Use all spells (evidence-based thinking)
- Multi-turn consultation (resume for clarification)
- Parallel invocation (all members at once)

### What Council Members CAN Do (Execution Mode)

Because these are hybrid agents, they can also:
- Execute code changes in their specialty area
- Run audits and generate reports
- Perform security scans (sentinel)
- Run benchmarks (benchmarker)
- Set up monitoring (tracer, measurer)

### What Council Members CANNOT Do

- Delegate to other agents (they are specialists)
- Make final decisions (advisory only in review mode)

---

## Integration Points

**Main Spell:** `@.genie/spells/council-review.md`
**Routing:** `@.genie/spells/routing-decision-matrix.md`
**Agents (10 Hybrid):**
- `@.genie/code/agents/questioner.md` - Questioning (Ryan Dahl)
- `@.genie/code/agents/benchmarker.md` - Performance (Matteo Collina)
- `@.genie/code/agents/simplifier.md` - Simplicity (TJ Holowaychuk)
- `@.genie/code/agents/sentinel.md` - Security (Troy Hunt)
- `@.genie/code/agents/ergonomist.md` - DX (Sindre Sorhus)
- `@.genie/code/agents/architect.md` - Systems (Linus Torvalds)
- `@.genie/code/agents/operator.md` - Operations (Kelsey Hightower)
- `@.genie/code/agents/deployer.md` - Deployment DX (Guillermo Rauch)
- `@.genie/code/agents/measurer.md` - Measurement (Bryan Cantrill)
- `@.genie/code/agents/tracer.md` - Production (Charity Majors)

**Claude Code Aliases:** `@.claude/agents/` (all 10 members)

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
