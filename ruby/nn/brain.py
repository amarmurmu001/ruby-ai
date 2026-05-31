import logging
from datetime import datetime
from pathlib import Path
from .classifier import IntentClassifier
from .generator import ResponseGenerator
from .knowledge import KnowledgeBase
from .learner import Learner
from config.settings import settings

logger = logging.getLogger("ruby.nn.brain")

class CustomBrain:
    def __init__(self):
        logger.info("Initialising custom neural brain...")
        self.classifier = IntentClassifier()
        self.knowledge = KnowledgeBase()
        self.learner = Learner()
        self.generator = ResponseGenerator(self.knowledge, save_callback=self._save_to_vault)
        self.web = None
        self.obsidian_vault = settings.OBSIDIAN_VAULT_PATH
        self.conversation_history = []
        self.user_ref = "Boss"
        self._ensure_vault_dirs()

    def _ensure_vault_dirs(self):
        (self.obsidian_vault / "RubyMemory").mkdir(parents=True, exist_ok=True)
        (self.obsidian_vault / "Daily").mkdir(parents=True, exist_ok=True)
        self._load_vault_notes()

    def _load_vault_notes(self):
        count = 0
        for f in self.obsidian_vault.rglob("*.md"):
            try:
                text = f.read_text(encoding="utf-8")
                self.knowledge.add_fact(str(f.relative_to(self.obsidian_vault)), text)
                self.generator.markov.train(text)
                count += 1
            except Exception:
                pass
        if count:
            logger.info("Loaded %d notes from vault", count)

    def _init_web(self):
        if self.web is None:
            try:
                from ruby.tools.web_knowledge import WebKnowledge
                self.web = WebKnowledge()
            except Exception:
                self.web = False

    def _save_to_vault(self, content: str) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        slug = "".join(c if c.isalnum() or c in " _-" else "_" for c in content)[:50]
        note = (
            f"---\ncreated: {ts}\nsource: Ruby AI\n---\n\n"
            f"# Memory: {content[:60]}\n\n{content}\n\n"
            f"---\n*Saved by Ruby at {ts}*\n"
        )
        fpath = self.obsidian_vault / "RubyMemory" / f"{slug}.md"
        fpath.write_text(note, encoding="utf-8")

        keywords = content.lower().split()[:5]
        for kw in keywords:
            self.knowledge.add_fact(f"kw:{kw}", content)

        logger.info("Memory saved to vault: %s", fpath)
        return str(fpath)

    def _build_context(self, user_input: str) -> str:
        parts = []

        similar = self.learner.get_similar_conversations(user_input, top_k=2)
        for conv in similar:
            parts.append(f"[Earlier: You said '{conv['user']}', I replied '{conv['ruby'][:100]}']")

        user_ctx = self.learner.get_user_context()
        if user_ctx:
            parts.append(f"[About You: {user_ctx}]")

        recalled = self.learner.recall(user_input, top_k=2)
        for r in recalled:
            parts.append(f"[Learned: {r['text']}]")

        return "\n".join(parts)

    def think(self, user_input: str, context: str | None = None) -> str:
        internal_context = self._build_context(user_input)

        if context:
            internal_context = f"{context}\n{internal_context}"

        intent, confidence = self.classifier.classify(user_input)
        logger.info("Intent: %s (%.2f%%)", intent, confidence * 100)

        response = self.generator.generate(intent, user_input, confidence)

        self.learner.learn(user_input, response)
        self.generator.markov.train(user_input)
        self.generator.markov.train(response)

        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def think_with_web(self, user_input: str) -> str:
        self._init_web()
        if self.web:
            results = self.web.search(user_input)
            if results:
                ctx = "\n".join(f"[{r['source']}] {r['snippet']}" for r in results[:2])
                self.knowledge.add_fact(f"web:{user_input[:30]}", ctx)
                return self.think(f"{user_input} (web context: {ctx[:500]})")
        return self.think(user_input)

    def think_stream(self, user_input: str, context: str | None = None):
        response = self.think(user_input, context)
        words = response.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")

    def structured_query(self, prompt: str) -> dict:
        prompt_lower = prompt.lower()
        if "remember" in prompt_lower:
            return {"action": "save_memory"}
        if "time" in prompt_lower or "date" in prompt_lower:
            return {"action": "get_time"}
        return {"action": "chat"}

    def generate_embedding(self, text: str) -> list:
        return []

    def set_user_name(self, name: str):
        self.user_ref = name
        self.knowledge.add_fact("user_name", name)

    def get_stats(self) -> dict:
        return self.learner.get_stats()

    def reset(self):
        self.conversation_history = []
        logger.info("Conversation history reset")
