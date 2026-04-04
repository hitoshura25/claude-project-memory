# Trial Summary — Scoreboard

> Quick-reference table. For full analysis, see the individual trial file.

| Trial | Date | Skill | Executors | Result | Notes |
|-------|------|-------|-----------|--------|-------|
| T01 | 2026-03-31 | implementation | Aider+Qwen | ❌ Partial | 27 tasks, 20/31 reflection exhaustion from I001/F401 lint loops |
| T02 | 2026-04-01 | implementation | Aider+Gemini Flash | ❌ Stalled | Stalled at task-02; enum bug + oversized scaffold + no escalation |
| T03 | 2026-04-02 | implementation | Claude CLI + Aider+Qwen | ❌ Hung | Hung on task-01; wrong `--allowedTools` semantics |
| T04 | 2026-04-03 | implementation | Aider+Qwen → Gemini → Claude | ⚠️ Best run | 15/18 tasks reached, all impl code produced; Claude rate limited |

---

## Progression

T01 → T02: Introduced model roles (validated test quality). Exposed enum bug and scaffold sizing.
T02 → T03: Introduced Claude CLI as executor. Exposed hardcoded flag assumptions.
T03 → T04: Runtime CLI research, multi-executor escalation. First run to produce all implementation code.

---

## Model Standings

| Model | Strengths | Weaknesses |
|-------|-----------|------------|
| Qwen 3 Coder 30B | Small/simple tasks (avro_writer, watermark_store) | Complex tasks, repetition loops without thinking mode, can't fix I001/F401 |
| Gemini Flash | Reliable rescue for mid-complexity tasks, handles 429 retries | Hit capacity limits under load |
| Claude CLI | Handles most complex tasks (parser), high code quality | Pro plan rate limit (~1hr active use) |

---

## Skill Standings

| Skill | Status | Last Validated |
|-------|--------|----------------|
| prototype-driven-planning | ✅ Built | 2026-03-28 (2 test runs) |
| prototype-driven-task-decomposition | ✅ Built | 2026-03-28 (3 test runs) |
| prototype-driven-implementation | 🔄 In progress | T04 (2026-04-03) |
