from .agent import Agent


class AgentFactory:
    _registry: dict[str, type[Agent]] = {}
    _default_name: str | None = None
    _default_kwargs: dict = {}

    def __init__(self):
        self.current_agent: Agent | None = None

    @classmethod
    def register_agent(cls, agent_name: str):
        def decorator(agent_cls: type[Agent]) -> type[Agent]:
            cls._registry[agent_name] = agent_cls
            return agent_cls

        return decorator

    @classmethod
    def set_default(cls, name: str, **kwargs) -> None:
        cls._default_name = name
        cls._default_kwargs = kwargs

    def use(self, name: str, **kwargs) -> "AgentFactory":
        if name not in self._registry:
            raise ValueError(
                f"Unknown agent: {name}. Available agents: {list(self._registry.keys())}"
            )
        self.current_agent = self._registry[name](**kwargs)
        return self

    @property
    def agent(self) -> Agent:
        if self.current_agent is None:
            if self._default_name is None:
                raise RuntimeError(
                    "No default agent configured. Call AgentFactory.set_default() or use() first."
                )
            self.use(self._default_name, **self._default_kwargs)
        assert self.current_agent is not None # for type checker
        return self.current_agent
