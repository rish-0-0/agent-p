from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static, Input, Pretty

from agents import AgentFactory


class Tui(App):
    """
    Agent UI Communication Interface
    """

    BINDINGS = [Binding("ctrl+q", "quit", "Quit", show=False, priority=True)]
    agent_output = reactive("")

    def on_mount(self) -> None:
        self.agent_factory = AgentFactory()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Ah, Agent P! Glad you're here. Here's your instructions:")
        yield Input(
            placeholder="Describe Agent P's task here...",
        )
        yield Pretty(None)
        yield Footer()

    @on(Input.Submitted)
    def handle_input(self, event: Input.Submitted) -> None:
        if not event.value.strip():
            return
        self.agent_output = self.agent_factory.agent.generate_response(event.value)
        self.query_one(Pretty).update(self.agent_output)
