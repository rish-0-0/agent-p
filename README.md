# Agent P

*Doobi Doobi Dooba*

A terminal-based AI agent with a sleek TUI, powered by local LLMs via Ollama and built on LangChain.

## Capabilities

- **Streaming responses** — tokens stream in real time into the terminal UI
- **Priority work queue** — human inputs, LLM calls, and (future) tool calls are dispatched through a priority queue
- **Pluggable agent backends** — register new LLM backends via `@AgentFactory.register_agent(name)`
- **Markdown rendering** — agent responses are rendered as rich Markdown in the chat log

## Tools

| Backend | Description |
|---|---|
| `ollama` | Runs local models via [Ollama](https://ollama.com) using `langchain-ollama` |

The default model is configured in `const.py` via `DEFAULT_OLLAMA_MODEL`.

## Slash Commands

| Command | Description |
|---|---|
| `/stop` | Cancels the current stream and clears the queue |
| `/stop <prompt>` | Cancels the current stream, then immediately sends `<prompt>` as the next message |

## Context Management

Agent P uses a **shared priority queue** (`agents/work_queue.py`) to manage work items:

| Priority | Type | Description |
|---|---|---|
| `0` | `HUMAN` | Messages typed by the user |
| `1` | `TOOL_CALL` | Reserved for future tool execution |
| `2` | `LLM_CALL` | Follow-up LLM calls chained internally |

The TUI runs the agent loop in a background thread, draining the queue and streaming each response. The `_cancel_event` threading flag lets `/stop` interrupt an in-flight stream cleanly.
