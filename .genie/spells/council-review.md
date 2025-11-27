---
name: Council Review
description: Multi-perspective advisory review during plan mode - invokes council members dynamically
load_priority: plan_mode
---

# Council Review Spell

**Purpose:** Provide multi-perspective advisory review during plan mode by dynamically invoking council member agents.

---

## When to Invoke

This spell **auto-activates during plan mode** to ensure architectural decisions receive multi-perspective review before implementation.

**Trigger:** Plan mode is active
**Mode:** Advisory (recommendations only, user decides)

---

## Council Members

The council consists of 5 agents, each representing a distinct perspective:

| Agent | Role | Philosophy | Trigger Keywords |
|-------|------|------------|------------------|
| **nayr** | The Questioner | "Why? Is there a simpler way?" | architecture, assumptions, complexity, dependencies |
| **oettam** | The Benchmarker | "Show me the benchmarks." | performance, latency, throughput, benchmark, optimize |
| **jt** | The Simplifier | "Delete code. Ship features." | simplify, delete, reduce, ship, YAGNI |
| **yort** | The Breach Hunter | "Where are the secrets? What's the blast radius?" | security, auth, secrets, vulnerability, encryption |
| **erdnis** | The Ergonomist | "If you need to read the docs, the API failed." | API, DX, interface, usability, error messages |

---

## Smart Routing

Not every plan needs all 5 perspectives. Route based on topic:

### Topic Detection

| Topic Category | Members Invoked | Detection Keywords |
|----------------|-----------------|-------------------|
| Architecture | nayr, oettam, jt | "redesign", "refactor", "architecture", "structure" |
| Performance | oettam, nayr, jt | "optimize", "slow", "benchmark", "latency" |
| Security | nayr, jt, yort | "auth", "security", "secret", "permission" |
| API Design | nayr, jt, erdnis | "API", "interface", "SDK", "CLI", "DX" |
| Full Review | all 5 | "full review", "architectural review", major decisions |

### Selection Logic

```
1. Analyze plan topic from user request
2. Match against trigger keywords
3. Select relevant council members
4. Default to core trio (nayr, oettam, jt) if no specific triggers
5. Add yort for security topics
6. Add erdnis for API/DX topics
```

---

## Invocation Protocol

### During Plan Mode

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

### Synthesis

After collecting perspectives:
1. Summarize each member's position
2. Count votes (approve/reject/modify)
3. Present synthesized advisory
4. User makes final decision

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

## Voting Thresholds (Advisory)

Since voting is advisory (non-blocking), thresholds are informational:

| Active Voters | Strong Consensus | Weak Consensus | Split |
|---------------|------------------|----------------|-------|
| 3 | 3/3 agree | 2/3 agree | No majority |
| 4 | 4/4 or 3/4 agree | 2/4 agree | Even split |
| 5 | 5/5 or 4/5 agree | 3/5 agree | No majority |

**User always decides** - council provides informed perspective, not binding judgment.

---

## Integration Points

### AGENTS.md Reference
```markdown
## Plan Mode Spells (Auto-Load)

During plan mode, load:
- `mcp__genie__read_spell("council-review")` - Multi-perspective advisory
```

### Routing Decision Matrix
```markdown
**When planning major changes**, invoke council:
- [routing-XXX] council-review = Multi-perspective planning review (nayr, oettam, jt, yort, erdnis)
  - Triggers: Plan mode active
  - Output: Advisory recommendations, vote summary
```

---

## Council Member Agents

Each council member is a standalone agent at `.genie/agents/`:

- `@.genie/agents/nayr.md` - Questioning perspective (Ryan Dahl)
- `@.genie/agents/oettam.md` - Performance perspective (Matteo Collina)
- `@.genie/agents/jt.md` - Simplicity perspective (TJ Holowaychuk)
- `@.genie/agents/yort.md` - Security perspective (Troy Hunt)
- `@.genie/agents/erdnis.md` - DX perspective (Sindre Sorhus)

---

## Example Usage

### Scenario: Planning a new authentication system

```
User: "I want to plan implementing OAuth2 for our API"

Council Review activates:
- Topic detected: Security + API Design
- Members selected: nayr, jt, yort, erdnis

Perspectives gathered:
- nayr: "Why OAuth2? What problem does basic auth not solve?"
- jt: "OAuth2 is complex. Can we use a simpler approach?"
- yort: "OAuth2 is good for security. Where will tokens be stored?"
- erdnis: "OAuth2 flow must be intuitive. Error messages critical."

Vote: 3 APPROVE, 1 MODIFY (jt suggests simplification)

Advisory: Proceed with OAuth2, but document the specific
requirements it solves (nayr's concern) and ensure error
messages are developer-friendly (erdnis's point).

User decides: Proceed / Modify / Reject
```

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
