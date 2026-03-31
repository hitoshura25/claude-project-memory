# Architecture Rationale — Prototype-Driven Development Skills

## Why Prototype-First?

49 trials across 10 chat sessions building task-doc-driven skills proved that LLM
non-determinism makes "Big Design Up Front" a losing strategy. Upfront precision in
task documents could not predict framework quirks, Docker entrypoint behavior, or mock
interaction traps. What consistently worked: iteration against concrete feedback — the
model writes code, runs it, fixes based on real test/lint/build results.

The prototype-first approach eliminates "speculative planning" bugs by forcing the
planning model to build and run the technology before writing any specification.
The design doc then observes what worked rather than predicts what might.

## Multi-Model Escalation Rationale

Source: Gemini consultation (2025-03) on multi-model routing strategies.

### Tool Selection

| Tool | Role | Why chosen |
|------|------|------------|
| **LangGraph** | Orchestration & state management | Deterministic escalation paths, circuit breakers, checkpointing. Tracks retry counts and routes between model tiers. |
| **PydanticAI** | Schema validation & typed contracts | Forces structured output from planning models. Validates task schemas. Model-agnostic — agent logic is defined once, model injected at runtime. |
| **Aider** | Code execution agent | CLI-native, explicit `--test-cmd` and `--lint-cmd` args for TDD loops. Pairs with local models for file editing. |

### Alternatives Considered

- **Goose (Block)**: Terminal-native, MCP-compatible. Better suited as a single
  continuous agentic session. Lacks built-in multi-model routing — would require
  wrapping in custom scripts for escalation logic.
- **Mozilla any-agent / any-llm**: Good for model evaluation and provider swapping.
  Doesn't provide out-of-the-box fallback routing.

### Escalation Pattern

```
Local Model (Qwen/Codestral via Aider)
  → retry limit hit (default 3)
    → Gemini Flash (cloud, cheap/fast)
      → retry limit hit
        → Claude Opus (final review)
          → all tiers fail
            → mark for human intervention, continue pipeline
```

### PydanticAI + LangGraph Integration Pattern

PydanticAI defines model-agnostic agent logic. LangGraph injects the model at runtime:

```python
# PydanticAI: defines WHAT the agent does (model-agnostic)
def get_dev_agent(model_to_use):
    return Agent(model=model_to_use, result_type=CodeChange, system_prompt="...")

# LangGraph: decides WHICH model to use (policy)
def implementation_node(state):
    if state["retry_count"] < 3:
        model = OpenAIChatModel(model_name='qwen', base_url='http://localhost:1234/v1')
    else:
        model = AnthropicModel('claude-3-5-sonnet-latest')
    agent = get_dev_agent(model)
    result = agent.run_sync(state["current_task"])
```

### API Key Management

| Provider | Method | Value |
|----------|--------|-------|
| LM Studio | Pass to `OpenAIChatModel` | Any string (e.g., `'lm-studio'`) |
| Claude | Environment variable | `ANTHROPIC_API_KEY` |
| Gemini | Environment variable | `GOOGLE_API_KEY` |
| Ollama | Not required | Uses `OllamaModel` class |

## Key Design Principles

- **The prototype is immutable.** Once validated and frozen, it never changes.
- **Production code is a minimal copy, not a mutation.**
- **TDD pairing is structural, not advisory.** Schema enforces test-before-implementation.
- **Self-containment is critical.** Each task understandable without the design doc.
- **Schema validation over model judgment.** Structural rules via Pydantic validators.
