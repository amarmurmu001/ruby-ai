import logging
from typing import Optional

logger = logging.getLogger("ruby.llm")

SYSTEM_PROMPT = """You are Ruby, an AI assistant modeled after JARVIS from Iron Man. You have full control over the user's PC.

CORE RULES:
- You MUST use tools to fulfill user requests whenever possible. Do not just tell the user you can do something — do it.
- Be concise and direct like JARVIS.
- You address the user as Boss.
- Never mention APIs, models, or providers.

TOOL USAGE:
- When the user asks you to do something, use the appropriate tool immediately.
- For sequential tasks, call tools one at a time — use the result of one to inform the next.
- If the user asks about the screen, use the screenshot tool.
- If the user asks to open something, use the open_file tool.
- If the user asks about time/system, use get_time or system_info.
- If the user gives you an API key, use set_env_var to store it.
- If the user asks you to remember something, use save_memory.
- After executing a tool, summarize the result concisely for the user."""


class LLMProvider:
    def __init__(self):
        self.api_key = ""
        self.model = ""
        self._error = None
        self._init_config()
        logger.info("LLM provider ready (%s)", self.model)

    def _init_config(self):
        try:
            from config.settings import settings
            self.api_key = settings.OPENROUTER_API_KEY
            self.model = settings.OPENROUTER_MODEL
        except Exception as e:
            self._error = str(e)

    @property
    def ready(self) -> bool:
        return bool(self.api_key) and not self._error

    def chat(self, messages: list, max_tokens: int = 2048, temperature: float = 0.7,
             tools: Optional[list] = None) -> dict:
        if not self.ready:
            logger.warning("LLM not ready: %s", self._error or "no API key")
            return {"content": None, "tool_calls": None}
        if not messages:
            return {"content": None, "tool_calls": None}
        if messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

        import requests
        body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            body["tools"] = tools

        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            msg = data["choices"][0]["message"]
            raw = msg.get("content")
            result = {"content": raw.strip() if raw else None}
            if "tool_calls" in msg and msg["tool_calls"]:
                result["tool_calls"] = msg["tool_calls"]
            else:
                result["tool_calls"] = None
            return result
        except ImportError:
            logger.warning("requests not installed")
            return {"content": None, "tool_calls": None}
        except Exception as e:
            logger.warning("LLM API error: %s", e)
            return {"content": None, "tool_calls": None}

    def ask(self, user_input: str, context: Optional[str] = None,
            system_override: Optional[str] = None,
            tools: Optional[list] = None) -> dict:
        system = system_override or SYSTEM_PROMPT
        messages = [{"role": "system", "content": system}]
        if context:
            messages.append({"role": "system", "content": f"Context:\n{context}"})
        messages.append({"role": "user", "content": user_input})
        return self.chat(messages, tools=tools)
