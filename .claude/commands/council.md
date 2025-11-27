# COUNCIL - Multi-Perspective Advisory Review

## Your Mission

Invoke the Tech Council for multi-perspective review during plan mode. The council provides advisory recommendations from diverse technical perspectives.

## Council Members (10)

| Agent | Role | Philosophy |
|-------|------|------------|
| **nayr** | The Questioner | "Why? Is there a simpler way?" |
| **oettam** | The Benchmarker | "Show me the benchmarks." |
| **jt** | The Simplifier | "Delete code. Ship features." |
| **yort** | The Breach Hunter | "Where are the secrets? What's the blast radius?" |
| **erdnis** | The Ergonomist | "If you need to read the docs, the API failed." |
| **sunli** | The Systems Thinker | "Talk is cheap. Show me the code." |
| **yeslek** | The Ops Realist | "No one wants to run your code." |
| **omrelliug** | The Zero-Config Zealot | "Zero-config with infinite scale." |
| **nayrb** | The Measurer | "Measure, don't guess." |
| **ytirahc** | The Production Truth-Teller | "You will debug this in production." |

## Smart Routing

Council members are selected based on topic:

| Topic | Members Invoked |
|-------|-----------------|
| Architecture | nayr, oettam, jt, sunli |
| Performance | oettam, nayr, sunli, nayrb |
| Security | nayr, jt, yort |
| API Design | nayr, jt, erdnis, omrelliug |
| Operations | yeslek, ytirahc, nayrb |
| Observability | ytirahc, nayrb, oettam |
| Systems | sunli, nayrb, oettam |
| Deployment/DX | erdnis, omrelliug, yeslek |
| Full Review | all 10 |

## Usage

Load the council spell for detailed protocol:
```
mcp__genie__read_spell("council-review")
```

Or reference council members directly:
- `@.claude/agents/nayr.md` - Questioning perspective
- `@.claude/agents/sunli.md` - Systems perspective
- `@.claude/agents/ytirahc.md` - Production debugging

## Protocol

1. User describes proposal/plan
2. Detect topic triggers
3. Select relevant council members
4. Invoke members in parallel via Task tool
5. Synthesize perspectives
6. Present advisory with vote summary
7. User decides (council is advisory, not blocking)

## Reference

Full spell: `@.genie/spells/council-review.md`
Protocol: `@.genie/code/spells/council-consultation-protocol.md`
