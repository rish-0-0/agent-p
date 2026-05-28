from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

from agents.work_queue import Priority, WorkItem, shared_queue

if TYPE_CHECKING:
    from .tui import Tui


class CommandName(str, Enum):
    STOP = "stop"


class SlashCommand(ABC):
    name: CommandName

    @abstractmethod
    def execute(self, args: str, tui: "Tui") -> None: ...


class StopCommand(SlashCommand):
    name = CommandName.STOP

    def execute(self, args: str, tui: "Tui") -> None:
        from textual.widgets import RichLog
        from .tui import AgentHeader

        tui._cancel_event.set()

        while not shared_queue.empty():
            try:
                shared_queue.get_nowait()
            except Exception:
                break

        tui._clear_stream_area()
        log = tui.query_one("#chat-log", RichLog)

        if args:
            log.write(f"[on #1a2f4a] you > {args} [/on #1a2f4a]")
            shared_queue.put(WorkItem(Priority.HUMAN, args))
            tui.query_one("#throbber-bar").display = True
        else:
            log.write("[cyan]>[/cyan]  Stopped. What should agent-p do next?")
            tui.query_one("#throbber-bar").display = False
            tui.query_one(AgentHeader).set_status("Idle")


class CommandRegistry:
    _registry: dict[str, SlashCommand] = {}

    @classmethod
    def register(cls, cmd: SlashCommand) -> None:
        cls._registry[cmd.name.value] = cmd

    @classmethod
    def dispatch(cls, raw: str, tui: "Tui") -> None:
        from textual.widgets import RichLog

        parts = raw[1:].split(" ", 1)
        name = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""
        cmd = cls._registry.get(name)
        if cmd is None:
            tui.query_one("#chat-log", RichLog).write(
                f"[red]Unknown command:[/red] /{name}"
            )
            return
        cmd.execute(args, tui)


CommandRegistry.register(StopCommand())
