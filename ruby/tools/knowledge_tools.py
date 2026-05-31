import logging
from .base import Tool
from config.settings import settings
from ruby.memory.obsidian import ObsidianMemory

logger = logging.getLogger("ruby.tools.knowledge")

class SaveMemory(Tool):
    name = "save_memory"
    description = "Save a memory to the Obsidian vault. Use for things you want to remember long-term."
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title of the memory"},
            "content": {"type": "string", "description": "Content to remember"},
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional tags"
            }
        },
        "required": ["title", "content"]
    }

    def execute(self, title: str, content: str, tags: list | None = None) -> str:
        mem = ObsidianMemory()
        path = mem.save_memory(title, content, tags)
        return f"Memory saved: {path}"

class RecallMemory(Tool):
    name = "recall_memory"
    description = "Search and recall memories from the Obsidian vault"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"}
        },
        "required": ["query"]
    }

    def execute(self, query: str) -> str:
        mem = ObsidianMemory()
        results = mem.search_memories(query)
        if not results:
            return "No memories found."
        parts = []
        for r in results:
            parts.append(f"## {r['title']}\n{r['content']}\n")
        return "\n---\n".join(parts)

class ListMemories(Tool):
    name = "list_memories"
    description = "List all saved memories"
    parameters = {
        "type": "object",
        "properties": {}
    }

    def execute(self) -> str:
        mem = ObsidianMemory()
        results = mem.list_memories()
        if not results:
            return "No memories yet."
        return "\n".join(f"- {r['title']} ({r['modified'][:10]})" for r in results)

class JournalEntry(Tool):
    name = "journal_entry"
    description = "Write an entry to today's journal in Obsidian"
    parameters = {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "Journal content"}
        },
        "required": ["content"]
    }

    def execute(self, content: str) -> str:
        mem = ObsidianMemory()
        path = mem.journal_today(content)
        return f"Journal entry saved: {path}"
