from abc import ABC, abstractmethod
from typing import Iterator


class Agent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def stream_response(self, prompt: str) -> Iterator[str]:
        raise NotImplementedError("Subclasses must implement this method.")
