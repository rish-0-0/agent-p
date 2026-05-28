import os
import threading

from rich.markdown import Markdown as RichMarkdown

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.theme import Theme
from textual.widget import Widget
from textual.widgets import Input, RichLog, Static

from agents import AgentFactory
from agents.work_queue import Priority, WorkItem, shared_queue
from tui.commands import CommandRegistry


AGENT_THEME = Theme(
    name="agent-p",
    primary="#00D4AA",
    secondary="#4A9EBA",
    accent="#00D4AA",
    foreground="#C0CAF5",
    background="#070B14",
    success="#9ECE6A",
    warning="#E0AF68",
    error="#F7768E",
    surface="#0D1117",
    panel="#1E2A3A",
    dark=True,
    variables={
        "input-selection-background": "#00D4AA 30%",
    },
)

_LOGO = (
    " ______  ____    ____    __  __  ______      ____    \n"
    "/\\  _  \\/\\  _`\\ /\\  _`\\ /\\ \\/\\ \\/\\__  _\\    /\\  _`\\  \n"
    "\\ \\ \\L\\ \\ \\ \\L\\_\\ \\ \\L\\_\\ \\ `\\\\ \\/_/\\ \\/    \\ \\ \\L\\ \\\n"
    " \\ \\  __ \\ \\ \\L_L\\ \\  _\\L\\ \\ , ` \\ \\ \\ \\     \\ \\ ,__/\n"
    "  \\ \\ \\/\\ \\ \\ \\/, \\ \\ \\L\\ \\ \\ \\`\\ \\ \\ \\ \\     \\ \\ \\/ \n"
    "   \\ \\_\\ \\_\\ \\____/\\ \\____/\\ \\_\\ \\_\\ \\ \\_\\     \\ \\_\\ \n"
    "    \\/_/\\/_/\\/___/  \\/___/  \\/_/\\/_/  \\/_/      \\/_/"
)


class AgentHeader(Widget):
    def compose(self) -> ComposeResult:
        cwd_parts = os.getcwd().replace("\\", "/").split("/")
        short_cwd = "/".join(cwd_parts[-2:]) if len(cwd_parts) >= 2 else os.getcwd()

        with Vertical(id="header-inner"):
            yield Static(_LOGO, id="logo")
            with Horizontal(id="stats-bar"):
                yield Static("[dim]@MODEL[/dim]\n[cyan]—[/cyan]", id="stat-model")
                yield Static(
                    "[dim]@STATUS[/dim]\n[green]Idle[/green]", id="stat-status"
                )
                yield Static(
                    f"[dim]@CWD[/dim]\n[cyan]{short_cwd}[/cyan]", id="stat-cwd"
                )

    def set_model(self, name: str) -> None:
        self.query_one("#stat-model", Static).update(
            f"[dim]@MODEL[/dim]\n[cyan]{name}[/cyan]"
        )

    def set_status(self, status: str) -> None:
        color = "green" if status == "Idle" else "yellow"
        self.query_one("#stat-status", Static).update(
            f"[dim]@STATUS[/dim]\n[{color}]{status}[/{color}]"
        )


class ModeBar(Widget):
    def compose(self) -> ComposeResult:
        with Horizontal(id="modebar-inner"):
            yield Static("[[1]] PLAN  [[2]] EDIT  [[3]] ASK", id="modes")
            yield Static("Tip: Press Ctrl+Q to quit", id="tip")


class Tui(App):
    CSS_PATH = "tui.tcss"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=False, priority=True),
        Binding("ctrl+l", "clear_log", "Clear", show=False),
    ]

    _THROBBER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    _throbber_index: int = 0

    def on_mount(self) -> None:
        self.register_theme(AGENT_THEME)
        self.theme = "agent-p"

        self.agent_factory = AgentFactory()
        model_name = getattr(self.agent_factory.agent, "model_name", "—")
        self.query_one(AgentHeader).set_model(model_name)

        self.query_one("#chat-log", RichLog).write(
            "[cyan]>[/cyan]  Session started. How can I help you today?"
        )

        self._cancel_event = threading.Event()
        self._start_throbber()
        self._start_agent_loop()

    def compose(self) -> ComposeResult:
        yield AgentHeader()
        yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
        yield Static("", id="stream-area")
        with Horizontal(id="throbber-bar"):
            yield Static("", id="throbber")
        with Horizontal(id="input-bar"):
            yield Static(">", id="prompt-prefix")
            yield Input(placeholder="Type your message...", id="user-input")
        yield ModeBar()

    def action_clear_log(self) -> None:
        self.query_one("#chat-log", RichLog).clear()
        self._update_stream_area("")

    @on(Input.Submitted, "#user-input")
    def handle_input(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        if not value:
            return
        event.input.clear()
        if value.startswith("/"):
            CommandRegistry.dispatch(value, self)
            return
        self.query_one("#chat-log", RichLog).write(
            f"[on #1a2f4a] you > {value} [/on #1a2f4a]"
        )
        shared_queue.put(WorkItem(Priority.HUMAN, value))
        self.query_one("#throbber-bar").display = True

    @work(thread=True)
    def _start_throbber(self) -> None:
        import time

        while True:
            time.sleep(0.08)
            self.call_from_thread(self._tick_throbber)

    def _tick_throbber(self) -> None:
        self._throbber_index = (self._throbber_index + 1) % len(self._THROBBER_FRAMES)
        self.query_one("#throbber", Static).update(
            self._THROBBER_FRAMES[self._throbber_index]
        )

    @work(thread=True)
    def _start_agent_loop(self) -> None:
        while True:
            try:
                item = shared_queue.get()
                if item.priority in (Priority.HUMAN, Priority.LLM_CALL):
                    self._stream_llm(item.payload)
                # Priority.TOOL_CALL: reserved for future tool execution
                if shared_queue.empty():
                    self.call_from_thread(self._set_idle)
            except Exception as exc:
                self.call_from_thread(self._on_agent_loop_error, str(exc))

    def _stream_llm(self, prompt: str) -> None:
        self._cancel_event.clear()
        self.call_from_thread(self._set_status, "Thinking…")
        buffer = ""
        first_chunk = True
        try:
            for chunk in self.agent_factory.agent.stream_response(prompt):
                if self._cancel_event.is_set():
                    self.call_from_thread(self._update_stream_area, "")
                    return
                if first_chunk:
                    self.call_from_thread(self._set_status, "Streaming…")
                    first_chunk = False
                buffer += chunk
                self.call_from_thread(self._update_stream_area, buffer)
        except Exception as exc:
            buffer = f"[red]Error: {exc}[/red]"
        if buffer.strip():
            self.call_from_thread(self._commit_response, buffer)

    def _set_status(self, status: str) -> None:
        self.query_one(AgentHeader).set_status(status)

    def _update_stream_area(self, text: str) -> None:
        self.query_one("#stream-area", Static).update(text)

    def _clear_stream_area(self) -> None:
        self._update_stream_area("")

    def _commit_response(self, buffer: str) -> None:
        log = self.query_one("#chat-log", RichLog)
        log.write("[dim]agent >[/dim]")
        log.write(RichMarkdown(buffer))
        self._update_stream_area("")

    def _on_agent_loop_error(self, msg: str) -> None:
        self.query_one("#chat-log", RichLog).write(f"[red]Agent error: {msg}[/red]")
        self._set_idle()

    def _set_idle(self) -> None:
        if not shared_queue.empty():
            return
        self.query_one("#throbber-bar").display = False
        self._set_status("Idle")
