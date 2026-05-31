from abc import ABC, abstractmethod
from typing import Any

class Tool(ABC):
    name: str
    description: str
    parameters: dict

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass

    def to_openai_format(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [t.to_openai_format() for t in self._tools.values()]

    def list_names(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, tool_name: str, **kwargs) -> Any:
        tool = self.get(tool_name)
        if not tool:
            return f"Tool '{tool_name}' not found. Available: {', '.join(self.list_names())}"
        return tool.execute(**kwargs)
