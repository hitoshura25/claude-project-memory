# Tool & Stack Reference

## Claude Code Skills
- Markdown-based instruction packages: `SKILL.md` + `references/` + `scripts/`
- Slash commands (`/command`) are Claude Code-specific invocations
- Skills also trigger automatically via description matching
- Best practices:
  - SKILL.md under 500 lines; use `references/` for detailed guidance
  - YAML frontmatter: `name` and `description` required; description should be "pushy"
  - Progressive disclosure: metadata → SKILL.md body → references (on demand)
  - Explain *why* behind instructions, not just *what*
  - Bundle scripts for deterministic tasks; references for contextual docs

## Aider
- CLI coding agent for file editing with local/cloud models
- Scripting flags: `--yes-always`, `--no-git`, `--no-check-update`, `--no-show-model-warnings`
- Explicit `--test-cmd` and `--lint-cmd` arguments for TDD loops
- Prototype references inlined into `--message-file` (not `--read` flags)
- Reference pattern: `run-tasks-template.sh` from `agent-ready-plans` skill

## LM Studio
- Local model server (OpenAI-compatible API at localhost:1234)
- Currently running: Qwen 3 Coder 30B Q4 via MLX
- Context length floor: 32k (lower causes Metal GPU OOM)
- Logs: `~/.lmstudio/server-logs/<year-month>/<date>.log`

## Gemini Flash
- Cloud fallback model via Gemini API
- Free-tier ~250k input token quota

## LangGraph
- State machine orchestration for multi-model routing, checkpointing, escalation
- Used in prototype-driven-implementation skill
- Docs: https://langchain-ai.github.io/langgraph/

## PydanticAI
- Typed agent framework, model-agnostic design
- Validates structured outputs via Pydantic schemas
- Used in task-decomposition (schema enforcement) and implementation (contract validation)
- Run with: `uv run --with pydantic` (venv activation doesn't persist in Claude Code)
- Docs: https://ai.pydantic.dev/

## Filesystem MCP
- Used in Claude Code sessions
- Prefer `list_directory` + `read_multiple_files` with known paths over `directory_tree`
  on large repos (avoids pulling `.git/objects` and `.venv`)
- Use `head`/`tail` params for large log files
