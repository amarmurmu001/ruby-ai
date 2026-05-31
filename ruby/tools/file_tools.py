import logging
import os
from pathlib import Path
from .base import Tool
from config.settings import settings

logger = logging.getLogger("ruby.tools.file")

class ReadFile(Tool):
    name = "read_file"
    description = "Read the contents of a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file"}
        },
        "required": ["path"]
    }

    def execute(self, path: str) -> str:
        try:
            p = Path(path)
            if not p.is_absolute():
                p = settings.WORKSPACE_DIR / p
            if not p.exists():
                return f"File not found: {p}"
            content = p.read_text(encoding="utf-8")
            return f"```\n{content}\n```" if len(content) < 5000 else content
        except Exception as e:
            return f"Error reading file: {e}"

class WriteFile(Tool):
    name = "write_file"
    description = "Write content to a file (overwrites if exists)"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file"},
            "content": {"type": "string", "description": "Content to write"}
        },
        "required": ["path", "content"]
    }

    def execute(self, path: str, content: str) -> str:
        try:
            p = Path(path)
            if not p.is_absolute():
                p = settings.WORKSPACE_DIR / p
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            logger.info("Wrote file: %s", p)
            return f"Written to {p}"
        except Exception as e:
            return f"Error writing file: {e}"

class ListDirectory(Tool):
    name = "list_directory"
    description = "List files and directories in a path"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path"}
        },
        "required": ["path"]
    }

    def execute(self, path: str = ".") -> str:
        try:
            p = Path(path)
            if not p.is_absolute():
                p = settings.WORKSPACE_DIR / p
            if not p.exists():
                return f"Directory not found: {p}"
            items = []
            for entry in sorted(p.iterdir()):
                suffix = "/" if entry.is_dir() else ""
                items.append(f"{entry.name}{suffix}")
            return "\n".join(items) if items else "(empty)"
        except Exception as e:
            return f"Error listing directory: {e}"

class SearchFiles(Tool):
    name = "search_files"
    description = "Search for files matching a glob pattern"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern (e.g. **/*.py)"},
            "path": {"type": "string", "description": "Root directory to search from"}
        },
        "required": ["pattern"]
    }

    def execute(self, pattern: str, path: str = ".") -> str:
        try:
            p = Path(path)
            if not p.is_absolute():
                p = settings.WORKSPACE_DIR / p
            matches = [str(f.relative_to(p)) for f in sorted(p.glob(pattern))]
            return "\n".join(matches) if matches else "No matches found"
        except Exception as e:
            return f"Error searching files: {e}"

class RunCommand(Tool):
    name = "run_command"
    description = "Run a shell command and return its output"
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Command to run"},
            "workdir": {"type": "string", "description": "Working directory (optional)"}
        },
        "required": ["command"]
    }

    def execute(self, command: str, workdir: str | None = None) -> str:
        import subprocess  # nosec
        try:
            cwd = Path(workdir) if workdir else settings.WORKSPACE_DIR
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                cwd=cwd, timeout=60
            )
            output = result.stdout or result.stderr
            return output[:10000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "Command timed out after 60 seconds"
        except Exception as e:
            return f"Error running command: {e}"
