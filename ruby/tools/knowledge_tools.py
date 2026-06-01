import logging
from datetime import datetime
from pathlib import Path
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


class VaultSearch(Tool):
    name = "vault_search"
    description = "Search all notes in the entire Obsidian vault (not just RubyMemory). Full-text search with filename, path, and content snippet."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query — case-insensitive"},
            "max_results": {"type": "integer", "description": "Max results to return (default 5)"}
        },
        "required": ["query"]
    }

    def execute(self, query: str, max_results: int = 5) -> str:
        vault = settings.OBSIDIAN_VAULT_PATH
        if not vault.exists():
            return f"Vault not found at {vault}"

        results = []
        query_lower = query.lower()
        for f in sorted(vault.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            if len(results) >= max_results:
                break
            try:
                content = f.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    rel = f.relative_to(vault)
                    # Find first occurrence for snippet
                    idx = content.lower().find(query_lower)
                    start = max(0, idx - 100)
                    end = min(len(content), idx + len(query) + 100)
                    snippet = content[start:end].replace("\n", " ")
                    if len(snippet) > 200:
                        snippet = snippet[:200] + "..."
                    results.append({
                        "path": str(rel),
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                        "snippet": snippet.strip(),
                    })
            except Exception:
                continue

        if not results:
            return f"No results found for '{query}' in vault."

        lines = [f"Found {len(results)} result(s) for '{query}':\n"]
        for r in results:
            lines.append(f"[{r['path']}] ({r['modified']})")
            lines.append(f"> {r['snippet']}\n")
        return "\n".join(lines)
