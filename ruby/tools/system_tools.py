import logging
import platform
from datetime import datetime
from .base import Tool

logger = logging.getLogger("ruby.tools.system")

class GetTime(Tool):
    name = "get_time"
    description = "Get the current date and time"
    parameters = {
        "type": "object",
        "properties": {}
    }

    def execute(self) -> str:
        return f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

class SystemInfo(Tool):
    name = "system_info"
    description = "Get information about the current system"
    parameters = {
        "type": "object",
        "properties": {}
    }

    def execute(self) -> str:
        info = {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
        return "\n".join(f"{k}: {v}" for k, v in info.items())

class Echo(Tool):
    name = "echo"
    description = "Echo back a message (for testing)"
    parameters = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Message to echo"}
        },
        "required": ["message"]
    }

    def execute(self, message: str) -> str:
        return message

class Confirm(Tool):
    name = "confirm"
    description = "Ask the user to confirm an action"
    parameters = {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "Question to ask"}
        },
        "required": ["question"]
    }

    def execute(self, question: str) -> str:
        return f"[NEEDS_CONFIRMATION] {question}"
