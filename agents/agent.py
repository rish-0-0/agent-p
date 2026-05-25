from abc import ABC, abstractmethod


class Agent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement this method.")
