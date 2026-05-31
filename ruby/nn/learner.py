import json
import logging
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from config.settings import settings

logger = logging.getLogger("ruby.nn.learner")

class Learner:
    def __init__(self):
        self.memory_file = settings.OBSIDIAN_VAULT_PATH / "RubyMemory" / "_ruby_knowledge.json"
        self.knowledge: dict[str, dict] = {}
        self.conversations: list[dict] = []
        self.user_prefs: dict[str, str] = {}
        self.word_freq: dict[str, int] = defaultdict(int)
        self.ngrams: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._load()

    def _load(self):
        if self.memory_file.exists():
            try:
                data = json.loads(self.memory_file.read_text(encoding="utf-8"))
                self.knowledge = data.get("knowledge", {})
                self.conversations = data.get("conversations", [])[-500:]
                self.user_prefs = data.get("user_prefs", {})
                self.word_freq = defaultdict(int, data.get("word_freq", {}))
                ngram_data = data.get("ngrams", {})
                for k, v in ngram_data.items():
                    self.ngrams[k] = defaultdict(int, v)
                logger.info("Loaded %d knowledge items, %d conversations",
                           len(self.knowledge), len(self.conversations))
            except Exception as e:
                logger.warning("Failed to load knowledge file: %s", e)

    def _save(self):
        try:
            data = {
                "knowledge": self.knowledge,
                "conversations": self.conversations[-500:],
                "user_prefs": self.user_prefs,
                "word_freq": dict(self.word_freq),
                "ngrams": {k: dict(v) for k, v in self.ngrams.items()},
                "updated": datetime.now().isoformat()
            }
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            self.memory_file.write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.warning("Failed to save knowledge: %s", e)

    def learn(self, user_input: str, response: str):
        self._store_conversation(user_input, response)
        self._extract_knowledge(user_input, response)
        self._build_ngrams(user_input)
        self._build_ngrams(response)
        self._track_words(user_input)
        self._track_words(response)
        self._save()

    def _store_conversation(self, user_input: str, response: str):
        self.conversations.append({
            "user": user_input,
            "ruby": response,
            "time": datetime.now().isoformat()
        })

    def _extract_knowledge(self, user_input: str, response: str):
        patterns = [
            (r"(?:i am|im|my name is|call me)\s+(\w+)", "user_name"),
            (r"(?:i like|i love|my favorite|i enjoy)\s+(.+?)(?:\.|$)", "preference"),
            (r"(?:i work as|i am a|my job is)\s+(.+?)(?:\.|$)", "job"),
            (r"(?:i live in|im from|my city is)\s+(.+?)(?:\.|$)", "location"),
            (r"(?:my (?:birthday|birth date) is)\s+(.+?)(?:\.|$)", "birthday"),
        ]
        for pattern, key in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                existing = self.user_prefs.get(key)
                if existing != value:
                    self.user_prefs[key] = value
                    logger.info("Learned %s: %s", key, value)

        words = user_input.lower().split()
        for i in range(len(words) - 1):
            pair = f"{words[i]} {words[i+1]}"
            if len(words) > i + 2:
                fact_key = f"fact:{pair}"
                if fact_key not in self.knowledge:
                    self.knowledge[fact_key] = {
                        "text": user_input,
                        "learned": datetime.now().isoformat(),
                        "count": 1
                    }
                else:
                    self.knowledge[fact_key]["count"] = (
                        self.knowledge[fact_key].get("count", 0) + 1
                    )

    def _build_ngrams(self, text: str):
        words = text.lower().split()
        for i in range(len(words) - 1):
            key = words[i]
            next_word = words[i + 1]
            self.ngrams[key][next_word] += 1

    def _track_words(self, text: str):
        for word in text.lower().split():
            self.word_freq[word] += 1

    def recall(self, query: str, top_k: int = 3) -> list[dict]:
        query_lower = query.lower()
        results = []

        for key, data in self.knowledge.items():
            text = data.get("text", "").lower()
            if any(word in text for word in query_lower.split()):
                results.append({
                    "text": data["text"],
                    "key": key,
                    "count": data.get("count", 1),
                    "learned": data.get("learned", "")
                })

        results.sort(key=lambda x: x["count"], reverse=True)
        return results[:top_k]

    def get_user_context(self) -> str:
        if not self.user_prefs:
            return ""
        parts = []
        for key, val in self.user_prefs.items():
            label = key.replace("_", " ").title()
            parts.append(f"{label}: {val}")
        return " | ".join(parts)

    def get_similar_conversations(self, query: str, top_k: int = 3) -> list[dict]:
        query_words = set(query.lower().split())
        scored = []
        for conv in self.conversations[-200:]:
            conv_words = set(conv["user"].lower().split())
            overlap = len(query_words & conv_words)
            if overlap > 0:
                scored.append((overlap, conv))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    def predict_next_word(self, word: str) -> str | None:
        if word.lower() in self.ngrams:
            candidates = self.ngrams[word.lower()]
            if candidates:
                return max(candidates, key=candidates.get)
        return None

    def get_stats(self) -> dict:
        return {
            "conversations": len(self.conversations),
            "facts_learned": len(self.knowledge),
            "user_prefs": len(self.user_prefs),
            "vocabulary": len(self.word_freq),
            "ngrams": sum(len(v) for v in self.ngrams.values())
        }
