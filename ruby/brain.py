import logging
import json
import time
import os
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger("ruby.brain")

CONV_FILE = Path(__file__).parent / "ruby_conversations.json"


class Brain:
    def __init__(self):
        self.llm = None
        self.custom = None
        self.registry = None
        self.conversations = []
        self._current_id = None
        self._cancel_requested = threading.Event()
        self._init_llm()
        self._init_registry()
        self._init_custom()
        self._load_conversations()
        self._ensure_current()
        self.start_vault_watcher()

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
            from ruby.tools.knowledge_tools import SaveMemory, RecallMemory, ListMemories, JournalEntry, VaultSearch
            self.registry.register(SaveMemory())
            self.registry.register(RecallMemory())
            self.registry.register(ListMemories())
            self.registry.register(JournalEntry())
            self.registry.register(VaultSearch())
        except Exception as e:
            logger.warning("knowledge tools: %s", e)

    def start_vault_watcher(self):
        try:
            from ruby.memory.watcher import VaultWatcher
            self._watcher = VaultWatcher(brain=self)
            self._watcher.start()
        except Exception as e:
            logger.warning("Vault watcher init: %s", e)

    def _load_conversations(self):
        try:
            if CONV_FILE.exists():
                data = json.loads(CONV_FILE.read_text(encoding="utf-8"))
                self.conversations = data.get("conversations", [])
                logger.info("Loaded %d conversations", len(self.conversations))
        except Exception as e:
            logger.warning("Failed to load conversations: %s", e)
            self.conversations = []

    def _save_conversations(self):
        try:
            CONV_FILE.write_text(
                json.dumps({"conversations": self.conversations}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("Failed to save conversations: %s", e)

    def _ensure_current(self):
        if not self.conversations:
            self._new_conversation()

    def _new_conversation(self, title: str = "New chat"):
        conv = {
            "id": str(int(time.time() * 1000)),
            "title": title,
            "created": time.strftime("%Y-%m-%d %H:%M"),
            "messages": [],
        }
        self.conversations.insert(0, conv)
        self._current_id = conv["id"]
        self._save_conversations()
        return conv["id"]

    def _current_messages(self) -> list:
        for c in self.conversations:
            if c["id"] == self._current_id:
                return c["messages"]
        if self.conversations:
            self._current_id = self.conversations[0]["id"]
            return self.conversations[0]["messages"]
        self._new_conversation()
        return self.conversations[0]["messages"]

    def _update_title(self, user_input: str):
        for c in self.conversations:
            if c["id"] == self._current_id:
                if c["title"] == "New chat":
                    c["title"] = user_input[:50] + ("..." if len(user_input) > 50 else "")
                break

    def switch_conversation(self, conv_id: str) -> bool:
        for c in self.conversations:
            if c["id"] == conv_id:
                self._current_id = conv_id
                return True
        return False

    def delete_conversation(self, conv_id: str) -> bool:
        for i, c in enumerate(self.conversations):
            if c["id"] == conv_id:
                self.conversations.pop(i)
                if self._current_id == conv_id:
                    self._ensure_current()
                self._save_conversations()
                return True
        return False

    def get_conversations(self) -> list:
        return [
            {"id": c["id"], "title": c["title"], "created": c["created"], "active": c["id"] == self._current_id}
            for c in self.conversations
        ]

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

    def _tool_calling_loop(self, user_input: str, max_rounds: int = 5, vault_context: str = "") -> str:
        tool_defs = self._tool_defs()
        messages = list(self._current_messages())
        if vault_context:
            messages.insert(0, {"role": "system", "content": f"Relevant vault context:\n{vault_context}"})
        messages.append({"role": "user", "content": user_input})

        for _ in range(max_rounds):
            if self._cancel_requested.is_set():
                self._cancel_requested.clear()
                return "Cancelled."
            raw = self.llm.chat(messages, tools=tool_defs)
            content = raw.get("content")
            tool_calls = raw.get("tool_calls")
            has_content = bool(content and content.strip())
            has_tc = bool(tool_calls)
            logger.info("LLM round: content=%s, tools=%s", bool(content), bool(tool_calls))

            if has_tc:
                pass
            elif has_content:
                return content
            else:
                if messages and messages[-1].get("role") == "tool":
                    return messages[-1]["content"]
                return "Done."

            for tc in tool_calls:
                tool_result = self._execute_tool_call(tc)
                logger.info("Tool result: %s", tool_result[:100])
                clean_tc = {k: v for k, v in tc.items() if k != "index"}
                messages.append({"role": "assistant", "content": None, "tool_calls": [clean_tc]})
                messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": tool_result})

            tool_defs = None

        logger.warning("Tool calling loop exhausted after %d rounds", max_rounds)
        return "I couldn't complete the full task. Try rephrasing."

    def _vault_context(self, query: str, max_chars: int = 2000) -> str:
        try:
            from ruby.memory.embeddings import VectorMemory
            from ruby.memory.obsidian import ObsidianMemory
            parts = []
            vec = None
            if self.custom:
                try:
                    vec = VectorMemory(self.custom)
                    ctx = vec.get_context(query, max_chars)
                    if ctx:
                        parts.append(ctx)
                except Exception:
                    pass
            try:
                om = ObsidianMemory()
                ctx = om.get_context(query, max_chars)
                if ctx:
                    parts.append(ctx)
            except Exception:
                pass
            return "\n\n".join(parts)[:max_chars]
        except Exception:
            return ""

    def think(self, user_input: str, context: Optional[str] = None) -> str:
        if self.llm:
            try:
                vault_ctx = self._vault_context(user_input)
                reply = self._tool_calling_loop(user_input, vault_context=vault_ctx)
                if reply:
                    msgs = self._current_messages()
                    msgs.append({"role": "user", "content": user_input})
                    msgs.append({"role": "assistant", "content": reply})
                    self._update_title(user_input)
                    self._save_conversations()
                    self._learn(user_input, reply)
                    return reply
                logger.warning("LLM returned empty")
            except Exception as e:
                logger.warning("LLM error: %s — falling back", e)

        if self.custom:
            reply = self.custom.think(user_input, context)
            msgs = self._current_messages()
            msgs.append({"role": "user", "content": user_input})
            msgs.append({"role": "assistant", "content": reply})
            self._update_title(user_input)
            self._save_conversations()
            return reply

        return self._fallback_response(user_input)

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

    def get_stats(self) -> dict:
        tools = self.registry.list_names() if self.registry else []
        msg_count = len(self._current_messages()) // 2
        return {
            "conversations": len(self.conversations),
            "current_messages": msg_count,
            "facts_learned": 0,
            "tools": len(tools),
            "tool_list": tools,
        }

    def cancel(self):
        self._cancel_requested.set()

    def shutdown(self):
        self.cancel()
        try:
            if hasattr(self, "_watcher") and self._watcher:
                self._watcher.stop()
        except Exception:
            pass

    def reset(self):
        if self.custom:
            self.custom.reset()
        self._new_conversation("New chat")
