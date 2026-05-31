import logging
import os
from pathlib import Path
from .base import Tool

logger = logging.getLogger("ruby.tools.env")

ENV_FILE = Path(__file__).parent.parent.parent / ".env"


def _load_env() -> dict:
    if not ENV_FILE.exists():
        return {}
    env = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _save_env(env: dict):
    lines = []
    for k, v in sorted(env.items()):
        lines.append(f'{k}="{v}"')
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


class GetEnvVar(Tool):
    name = "get_env_var"
    description = "Get the value of an environment variable or .env file entry"
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Variable name"}
        },
        "required": ["name"]
    }

    def execute(self, name: str) -> str:
        val = os.environ.get(name, "")
        if val:
            return f"{name}={val}"
        env = _load_env()
        if name in env:
            return f"{name}={env[name]}"
        return f"Variable '{name}' not found"


class SetEnvVar(Tool):
    name = "set_env_var"
    description = "Set an environment variable in the .env file. Use for storing API keys, secrets, and configuration."
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Variable name (uppercase with underscores, e.g. MY_API_KEY)"},
            "value": {"type": "string", "description": "Variable value"}
        },
        "required": ["name", "value"]
    }

    def execute(self, name: str, value: str) -> str:
        try:
            env = _load_env()
            env[name] = value
            _save_env(env)
            os.environ[name] = value
            return f"Set {name}={value[:4]}...{value[-4:] if len(value) > 8 else ''}"
        except Exception as e:
            return f"Error setting variable: {e}"


class ListEnvVars(Tool):
    name = "list_env_vars"
    description = "List all variable names stored in .env (values hidden for security)"
    parameters = {
        "type": "object",
        "properties": {}
    }

    def execute(self) -> str:
        env = _load_env()
        if not env:
            return "No .env variables stored"
        return "\n".join(f"  {k}=****" for k in sorted(env.keys()))


class DeleteEnvVar(Tool):
    name = "delete_env_var"
    description = "Delete an environment variable from the .env file"
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Variable name to delete"}
        },
        "required": ["name"]
    }

    def execute(self, name: str) -> str:
        try:
            env = _load_env()
            if name in env:
                del env[name]
                _save_env(env)
                return f"Deleted {name}"
            return f"Variable '{name}' not found"
        except Exception as e:
            return f"Error deleting variable: {e}"
