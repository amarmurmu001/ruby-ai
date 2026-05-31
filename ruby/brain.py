import logging
from typing import Optional

logger = logging.getLogger("ruby.brain")


class Brain:
    def __init__(self):
        self.llm = None
        self.custom = None
        self.registry = None
        self.conversation_history = []
        self._init_llm()
        self._init_registry()
        self._init_custom()

    def _init_llm(self):
        try:
            from ruby.tools.llm import LLMProvider
            self.llm = LLMProvider()
            if not self.llm.ready:
                logger.warning("LLM provider not ready")
                self.llm = None
        except Exception as e:
            logger.warning("LLM init failed: %s", e)
            self.llm = None

    def _init_custom(self):
        try:
            from ruby.nn.brain import CustomBrain
            self.custom = CustomBrain()
            logger.info("Custom neural brain ready — fallback mode")
        except Exception as e:
            logger.warning("Custom brain init failed: %s", e)
            self.custom = None

    def _init_registry(self):
        try:
            from ruby.tools.base import ToolRegistry
            self.registry = ToolRegistry()
            self._register_system_tools()
            self._register_file_tools()
            self._register_web_tools()
            self._register_desktop_tools()
            self._register_env_tools()
            self._register_knowledge_tools()
            logger.info("Tool registry ready: %s", ", ".join(self.registry.list_names()))
        except Exception as e:
            logger.warning("Tool registry init failed: %s", e)

    def _register_system_tools(self):
        try:
            from ruby.tools.system_tools import GetTime, SystemInfo, Echo
            self.registry.register(GetTime())
            self.registry.register(SystemInfo())
            self.registry.register(Echo())
        except Exception as e:
            logger.warning("system tools: %s", e)

    def _register_file_tools(self):
        try:
            from ruby.tools.file_tools import ReadFile, WriteFile, ListDirectory, SearchFiles, RunCommand
            self.registry.register(ReadFile())
            self.registry.register(WriteFile())
            self.registry.register(ListDirectory())
            self.registry.register(SearchFiles())
            self.registry.register(RunCommand())
        except Exception as e:
            logger.warning("file tools: %s", e)

    def _register_web_tools(self):
        try:
            from ruby.tools.web_tools import WebSearch, FetchURL
            self.registry.register(WebSearch())
            self.registry.register(FetchURL())
        except Exception as e:
            logger.warning("web tools: %s", e)

    def _register_desktop_tools(self):
        try:
            from ruby.tools.desktop_tools import (
                OpenFile, ReadClipboard, WriteClipboard,
                ShowNotification, Screenshot, GetActiveWindow, ListWindows
            )
            self.registry.register(OpenFile())
            self.registry.register(ReadClipboard())
            self.registry.register(WriteClipboard())
            self.registry.register(ShowNotification())
            self.registry.register(Screenshot())
            self.registry.register(GetActiveWindow())
            self.registry.register(ListWindows())
        except Exception as e:
            logger.warning("desktop tools: %s", e)

    def _register_env_tools(self):
        try:
            from ruby.tools.env_tools import GetEnvVar, SetEnvVar, ListEnvVars, DeleteEnvVar
            self.registry.register(GetEnvVar())
            self.registry.register(SetEnvVar())
            self.registry.register(ListEnvVars())
            self.registry.register(DeleteEnvVar())
        except Exception as e:
            logger.warning("env tools: %s", e)

    def _register_knowledge_tools(self):
        try:
            from ruby.tools.knowledge_tools import SaveMemory, RecallMemory, ListMemories, JournalEntry
            self.registry.register(SaveMemory())
            self.registry.register(RecallMemory())
            self.registry.register(ListMemories())
            self.registry.register(JournalEntry())
        except Exception as e:
            logger.warning("knowledge tools: %s", e)

    def _tool_defs(self):
        if not self.registry:
            return None
        return self.registry.list_tools()

    def _execute_tool_call(self, tc: dict) -> str:
        func_name = tc.get("function", {}).get("name", "")
        import json
        try:
            raw = tc.get("function", {}).get("arguments", "{}")
            args = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            args = {}
        logger.info("Tool call: %s(%s)", func_name, args)
        if not self.registry:
            return "Tool system unavailable"
        return self.registry.execute(func_name, **args)

    def _tool_calling_loop(self, user_input: str, max_rounds: int = 5) -> str:
        tool_defs = self._tool_defs()
        messages = list(self.conversation_history)
        messages.append({"role": "user", "content": user_input})

        for _ in range(max_rounds):
            raw = self.llm.chat(messages, tools=tool_defs)
            content = raw.get("content")
            tool_calls = raw.get("tool_calls")
            has_content = bool(content and content.strip())
            has_tc = bool(tool_calls)
            logger.info("LLM round: content=%s, tools=%s", bool(content), bool(tool_calls))
            if has_content and content:
                logger.info("LLM content preview: %s...", content[:80])

            if has_tc:
                pass
            elif has_content:
                return content
            else:
                if messages and messages[-1].get("role") == "tool":
                    last = messages[-1]["content"]
                    return last
                return "Done."

            for tc in tool_calls:
                tool_result = self._execute_tool_call(tc)
                logger.info("Tool result: %s", tool_result[:100])
                clean_tc = {k: v for k, v in tc.items() if k != "index"}
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [clean_tc]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": tool_result
                })

            tool_defs = None

        logger.warning("Tool calling loop exhausted after %d rounds", max_rounds)
        return "I couldn't complete the full task. Try rephrasing."

    def think(self, user_input: str, context: Optional[str] = None) -> str:
        if self.llm:
            try:
                ctx = self._build_context(context)
                reply = self._tool_calling_loop(user_input)
                if reply:
                    self.conversation_history.append({"role": "user", "content": user_input})
                    self.conversation_history.append({"role": "assistant", "content": reply})
                    self._learn(user_input, reply)
                    return reply
                logger.warning("LLM returned empty")
            except Exception as e:
                logger.warning("LLM error: %s — falling back", e)

        if self.custom:
            reply = self.custom.think(user_input, context)
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": reply})
            return reply

        return self._fallback_response(user_input)

    def _build_context(self, context: Optional[str] = None) -> str:
        parts = []
        if context:
            parts.append(context)
        if self.custom:
            try:
                ctx = self.custom._build_context("")
                if ctx:
                    parts.append(ctx)
            except Exception:
                pass
        if self.conversation_history:
            recent = self.conversation_history[-4:]
            lines = ["Recent conversation:"]
            for msg in recent:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:200]
                lines.append(f"[{role}]: {content}")
            parts.append("\n".join(lines))
        return "\n\n".join(parts)

    def _learn(self, user_input: str, reply: str):
        if self.custom:
            try:
                self.custom.learner.learn(user_input, reply)
                self.custom.generator.markov.train(user_input)
                self.custom.generator.markov.train(reply)
            except Exception:
                pass

    def _fallback_response(self, text: str) -> str:
        tl = text.lower()
        if "hello" in tl or "hi" in tl:
            return "Hey Boss. Ruby online."
        if "joke" in tl:
            return "Why did the AI cross the road? To optimize the path."
        if "time" in tl:
            import time as tm
            return f"Local time: {tm.strftime('%H:%M:%S')}"
        if "name" in tl:
            return "I am Ruby. Custom neural network. No cloud. No APIs."
        return "Acknowledged. Processing locally."

    def think_stream(self, user_input: str, context: Optional[str] = None):
        response = self.think(user_input, context)
        for word in response.split(" "):
            yield word + " "

    def structured_query(self, prompt: str) -> dict:
        prompt_lower = prompt.lower()
        if "remember" in prompt_lower or "save" in prompt_lower:
            return {"action": "save_memory"}
        if "time" in prompt_lower or "date" in prompt_lower:
            return {"action": "get_time"}
        return {"action": "chat"}

    def generate_embedding(self, text: str) -> list:
        return []

    def get_stats(self) -> dict:
        if self.custom:
            try:
                return self.custom.get_stats()
            except Exception:
                pass
        tools = self.registry.list_names() if self.registry else []
        return {
            "conversations": len(self.conversation_history) // 2,
            "facts_learned": 0,
            "vocabulary": 0,
            "ngrams": 0,
            "user_prefs": 0,
            "tools": len(tools),
            "tool_list": tools,
        }

    def reset(self):
        if self.custom:
            self.custom.reset()
        self.conversation_history = []
