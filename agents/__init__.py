from .agent import Agent as Agent
from .agent_registry import AgentFactory as AgentFactory
from .ollama import OllamaAgent as OllamaAgent
from const import DEFAULT_OLLAMA_MODEL

AgentFactory.register_agent("ollama")(OllamaAgent)
AgentFactory.set_default("ollama", model_name=DEFAULT_OLLAMA_MODEL)
