from . import Agent, OllamaAgent
from const import DEFAULT_OLLAMA_MODEL


class AgentFactory:
    _registry: dict[str, type[Agent]] = {}

    def __init__(self):
        self.current_agent: Agent | None = None

    @classmethod
    def register_agent(cls, agent_name: str):
        """
        Register a new agent class with a unique name.
        """

        def decorator(agent_cls: type[Agent]) -> type[Agent]:
            cls._registry[agent_name] = agent_cls
            return agent_cls

        return decorator

    def use(self, name: str, **kwargs) -> "AgentFactory":
        """
        Switch to a different agent by name and model name.
        """
        if name not in self._registry:
            raise ValueError(
                f"Unknown agent: {name}. Available agents: {list(self._registry.keys())}"
            )
        self.current_agent = self._registry[name](**kwargs)
        return self

    @property
    def agent(self) -> Agent:
        """
        Get the current agent instance.
        """
        if self.current_agent is None:
            self.current_agent = OllamaAgent(DEFAULT_OLLAMA_MODEL)
        return self.current_agent
