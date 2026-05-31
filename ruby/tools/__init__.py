from .base import Tool, ToolRegistry
from .file_tools import ReadFile, WriteFile, ListDirectory, SearchFiles, RunCommand
from .web_tools import WebSearch, FetchURL
from .knowledge_tools import SaveMemory, RecallMemory, ListMemories, JournalEntry
from .system_tools import GetTime, SystemInfo, Echo, Confirm

def create_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ReadFile())
    registry.register(WriteFile())
    registry.register(ListDirectory())
    registry.register(SearchFiles())
    registry.register(RunCommand())
    registry.register(WebSearch())
    registry.register(FetchURL())
    registry.register(SaveMemory())
    registry.register(RecallMemory())
    registry.register(ListMemories())
    registry.register(JournalEntry())
    registry.register(GetTime())
    registry.register(SystemInfo())
    registry.register(Echo())
    registry.register(Confirm())
    return registry

__all__ = ["Tool", "ToolRegistry", "create_registry"]
