import queue
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class Priority(IntEnum):
    HUMAN = 0
    TOOL_CALL = 1
    LLM_CALL = 2


@dataclass(order=True)
class WorkItem:
    priority: int
    payload: Any = field(compare=False)


shared_queue: queue.PriorityQueue[WorkItem] = queue.PriorityQueue()
