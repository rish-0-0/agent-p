import os

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.theme import Theme
from textual.widget import Widget
from textual.widgets import Input, RichLog, Static

from agents import AgentFactory


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

    def on_mount(self) -> None:
        self.register_theme(AGENT_THEME)
        self.theme = "agent-p"

        self.agent_factory = AgentFactory()
        model_name = getattr(self.agent_factory.agent, "model_name", "—")
        self.query_one(AgentHeader).set_model(model_name)

        self.query_one("#chat-log", RichLog).write(
            "[cyan]>[/cyan]  Session started. How can I help you today?"
        )

    def compose(self) -> ComposeResult:
        yield AgentHeader()
        yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
        with Horizontal(id="input-bar"):
            yield Static(">", id="prompt-prefix")
            yield Input(placeholder="Type your message...", id="user-input")
        yield ModeBar()

    def action_clear_log(self) -> None:
        self.query_one("#chat-log", RichLog).clear()

    @on(Input.Submitted, "#user-input")
    def handle_input(self, event: Input.Submitted) -> None:
        if not event.value.strip():
            return
        value = event.value.strip()
        event.input.clear()
        self.query_one("#chat-log", RichLog).write(f"[dim]you >[/dim]  {value}")
        self._run_agent(value)

    @work(thread=True)
    def _run_agent(self, value: str) -> None:
        header = self.query_one(AgentHeader)
        self.call_from_thread(header.set_status, "Thinking…")
        response = self.agent_factory.agent.generate_response(value)
        self.call_from_thread(header.set_status, "Idle")
        self.call_from_thread(
            self.query_one("#chat-log", RichLog).write,
            f"[cyan]>[/cyan]  {response}",
        )
