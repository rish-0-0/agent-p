from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static, Input, Pretty

from agents import OllamaAgent
from const import OLLAMA_MODEL_NAME


class Tui(App):
    """
    Agent UI Communication Interface
    """

    BINDINGS = [Binding("ctrl+q", "quit", "Quit", show=False, priority=True)]
    agent_output = reactive("")

    def on_mount(self) -> None:
        self.agent = OllamaAgent(model_name=OLLAMA_MODEL_NAME)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Ah, Agent P! Glad you're here. Here's your instructions:")
        yield Input(
            placeholder="Describe Agent P's task here...",
        )
        yield Pretty("")
        yield Footer()

    @on(Input.Submitted)
    def handle_input(self, event: Input.Submitted) -> None:
        if not event.value.strip():
            return
        self.agent_output = self.agent.generate_response(event.value)
        self.query_one(Pretty).update(self.agent_output)
