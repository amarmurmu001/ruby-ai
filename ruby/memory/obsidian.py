import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from config.settings import settings

logger = logging.getLogger("ruby.memory.obsidian")

class ObsidianMemory:
    def __init__(self):
        self.vault_path = settings.OBSIDIAN_VAULT_PATH
        self.memory_dir = self.vault_path / settings.OBSIDIAN_MEMORY_DIR
        self.journal_dir = self.vault_path / settings.OBSIDIAN_JOURNAL_DIR
        self._ensure_dirs()

    def _ensure_dirs(self):
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.journal_dir.mkdir(parents=True, exist_ok=True)

    def _slug(self, text: str) -> str:
        return "".join(c if c.isalnum() or c in " _-" else "_" for c in text).strip()[:60]

    def save_memory(self, title: str, content: str, tags: Optional[list] = None) -> Path:
        slug = self._slug(title)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        tags_line = f"\ntags: {', '.join(tags)}\n" if tags else ""

        note = f"""---
created: {timestamp}
type: memory
{tags_line}
---

# {title}

{content}

---
*Saved by Ruby at {timestamp}*
"""
        filepath = self.memory_dir / f"{slug}.md"
        filepath.write_text(note, encoding="utf-8")
        logger.info("Memory saved: %s", filepath)
        return filepath

    def read_memory(self, title: str) -> Optional[str]:
        slug = self._slug(title)
        filepath = self.memory_dir / f"{slug}.md"
        if filepath.exists():
            return filepath.read_text(encoding="utf-8")
        return None

    def search_memories(self, query: str) -> list[dict]:
        results = []
        query_lower = query.lower()
        for f in sorted(self.memory_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            content = f.read_text(encoding="utf-8")
            if query_lower in content.lower():
                results.append({
                    "title": f.stem,
                    "path": str(f),
                    "content": content[:500],
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
        return results[:settings.MEMORY_TOP_K]

    def list_memories(self) -> list[dict]:
        results = []
        for f in sorted(self.memory_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            results.append({
                "title": f.stem,
                "path": str(f),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
        return results

    def delete_memory(self, title: str) -> bool:
        slug = self._slug(title)
        filepath = self.memory_dir / f"{slug}.md"
        if filepath.exists():
            filepath.unlink()
            logger.info("Memory deleted: %s", filepath)
            return True
        return False

    def journal_today(self, content: str) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        filepath = self.journal_dir / f"{today}.md"
        mode = "a" if filepath.exists() else "w"
        header = "" if filepath.exists() else f"# Journal — {today}\n\n"
        timestamp = datetime.now().strftime("%H:%M")
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(f"{header}## {timestamp}\n\n{content}\n\n")
        logger.info("Journal entry added: %s", filepath)
        return filepath

    def read_journal(self, date: Optional[str] = None) -> Optional[str]:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        filepath = self.journal_dir / f"{date}.md"
        if filepath.exists():
            return filepath.read_text(encoding="utf-8")
        return None

    def get_context(self, query: str, max_chars: int = 2000) -> str:
        parts = []
        memories = self.search_memories(query)
        for m in memories:
            parts.append(f"[Memory: {m['title']}]\n{m['content']}")
        journal = self.read_journal()
        if journal:
            parts.append(f"[Today's Journal]\n{journal[:1000]}")

        combined = "\n\n".join(parts)
        return combined[:max_chars]
