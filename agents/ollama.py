from typing import Iterator, override

from langchain_ollama import ChatOllama
from . import Agent, AgentFactory

SYSTEM_PROMPT = (
    "system",
    "You are a helpful assistant that provides accurate and concise information.",
)


@AgentFactory.register_agent("ollama")
class OllamaAgent(Agent):
    def __init__(self, model_name: str):
        super().__init__(name="OllamaAgent")
        self.model_name = model_name
        self.chat_model = ChatOllama(model=model_name)

    @override
    def generate_response(self, prompt: str) -> str:
        message: list[tuple[str, str]] = [SYSTEM_PROMPT, ("human", prompt)]
        response = self.chat_model.invoke(message)
        return response.text

    @override
    def stream_response(self, prompt: str) -> Iterator[str]:
        messages: list[tuple[str, str]] = [SYSTEM_PROMPT, ("human", prompt)]
        for chunk in self.chat_model.stream(messages):
            yield chunk.content
