# Trial Summary — Scoreboard

> Quick-reference table. For full analysis, see the individual trial file.

| Trial | Date | Model | Result | Notes |
|-------|------|-------|--------|-------|
| T01 | 2026-02-27 – 03-02 | Codestral / Qwen | Strategy comparison | Code-based + Spec-based abandoned |
| T02 | 2026-03-03 | Qwen 30B | 16/18 (interrupted) | First TDD trial; summarizer spiral identified |
| T03 | 2026-03-04 | Qwen 30B | 13 ✅, 4 ⚠️ | --timeout ineffective with streaming; git restore bug |
| T04 | 2026-03-04 | Qwen 30B | Crashed task 9 | 12k context → Metal GPU OOM. **Floor: 32k** |
| T05 | 2026-03-04 | Qwen 30B | 18 completed, hung on 9 | HeartRate contract mismatch; code quality assessment |
| T06 | 2026-03-09 | Qwen 30B | 11/18 ✅, 1 ⚠️, halted 12 | UUIDStore CREATE TABLE; dotted mock path |
| T07 | 2026-03-10 | Qwen 30B | 9/12 ✅, 3 ⚠️, halted 13 | Cascade root cause identified; :memory: trap |
| T08 | 2026-03-10 | Codestral 22B | 5/18 ✅, 13 ⚠️ | Test file corruption; first disqualification signal |
| T09 | 2026-03-10 | Gemini 2.0 Flash Lite | 12/13 ✅, 1 ⚠️, halted 14 | Hallucinated import; cascade confirmed structural |
| T10 | 2026-03-12 | Qwen 30B | 15/17 ✅, 2 ⚠️ | Post cascade fix; SQLite multi-column IN trap |
| T11 | 2026-03-12 | Codestral 22B | 7/17 ✅, 9 ⚠️ | Second disqualification signal |
| T12 | 2026-03-12 | Gemini 3.1 Flash Lite | **17/17 ✅** | **First clean sweep** — 27 calls |
| T13 | 2026-03-12 | Qwen 30B | 17/18 ✅, 1 ⚠️ | Wire DAG E501 spiral + ISE; import_integrity validated |
| T14 | 2026-03-12 | Qwen 30B | 16/18 ✅, 1 ❌ | ISE → OOM on Wire DAG; fatal context bloat |
| T15 | 2026-03-14 | Qwen 30B | **18/18 ✅** (1 ⚠️) | **First Qwen clean sweep** — snippet fix validated |
| T16 | 2026-03-14 | Codestral 22B | 2/7 ✅, 1 ❌ | **Codestral permanently disqualified** (3rd confirmation) |
| T17 | 2026-03-14 | Gemini 3.1 Flash Lite | **18/18 ✅** | Second Gemini sweep — 21 calls |
| T18 | 2026-03-14 | Qwen 30B | **18/18 ✅** (1 ⚠️) | Second Qwen sweep — 23 calls; loop closed |
| T19 | 2026-03-15 | Qwen 30B | 17/19 ✅, 2 ⚠️, 1 ⏭ | New task set; `is_closed` mock + empty test_command |
| T20 | 2026-03-15 | Gemini 3.1 Flash Lite | **18/18 ✅**, 1 ⏭ | Third Gemini sweep on new task set |
| T21 | 2026-03-16 | Qwen 30B | 16/18 ✅, 1 ⚠️, 1 ❌ | Revised + infra; Docker image tag authoring error |
| T22 | 2026-03-16 | Gemini 3.1 Flash Lite | 16/18 ✅, 1 ⚠️, 1 ❌ | Same image tag error; pip/USER constraint revealed |
| T23 | 2026-03-16 | Qwen 30B | 0/18 — stalled task 1 | `:memory:` fixture without persistent conn warning |
| T24 | 2026-03-17 | Qwen 30B | 3/18 (1 ⚠️, 2 ✅) — stalled task 4 | Capture mock + body assertion contradiction |
| T25 | 2026-03-17 | Qwen 30B | 16/18 ✅, 1 ⚠️ | Pinned version fabrication (`boto3==1.29.150`) |
| T26 | 2026-03-17 | Gemini 3.1 Flash Lite | 16/18 ✅, 1 ⚠️ | hadolint DL3013 + token limit; container exit(1) |
| T27 | 2026-03-18 | Qwen 30B | 17/19 (14✅ 3⚠️ 1❌) | Chat 7: test-by-ref + Dockerfile scaffold validated; Docker exit(1) missing secret key |
| T28 | 2026-03-18 | Gemini 3.1 Flash Lite | 17/19 (17✅ 1❌) | Chat 7: 17/17 service tasks clean; same Docker exit(1); 26 calls |
| T29 | 2026-03-19 | Qwen 30B | 7✅ 1⚠️ 9 degraded 1❌ | **Regression**: missing persistent conn guidance → 9-task cascade |
| T30 | 2026-03-19 | Gemini 3.1 Flash Lite | 2✅, hard-stop task 3 | **Same regression**: both models default to multi-connection SQLite without explicit guidance |

---

## Model Standings (as of T30)

- **Gemini 3.1 Flash Lite**: Reference model. Clean sweeps on T12, T17, T20. T28: 17/17 service tasks clean. T30: hard-stop at task 3 — Claude Code authoring gap, not model regression.
- **Qwen 3 Coder 30B**: Clean sweeps on T15, T18. T27: 14✅ 3⚠️. T29: 7✅ 9 degraded — same authoring gap as Gemini T30.
- **Codestral 22B**: Permanently disqualified (T8, T11, T16). Not fixable at skill level.
