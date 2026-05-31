import math
import re
from pathlib import Path
from collections import Counter
from config.settings import settings

class TFIDF:
    def __init__(self):
        self.documents: list[dict] = []
        self.idf: dict[str, float] = {}
        self.dirty = True

    def add_document(self, doc_id: str, text: str):
        self.documents.append({"id": doc_id, "text": text.lower()})
        self.dirty = True

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r'\b[a-z]+\b', text.lower())

    def _compute_idf(self):
        n = len(self.documents)
        doc_freq: dict[str, int] = {}
        for doc in self.documents:
            words = set(self._tokenize(doc["text"]))
            for w in words:
                doc_freq[w] = doc_freq.get(w, 0) + 1
        self.idf = {w: math.log((n + 1) / (f + 1)) + 1 for w, f in doc_freq.items()}
        self.dirty = False

    def _tf(self, text: str) -> dict[str, float]:
        words = self._tokenize(text)
        if not words:
            return {}
        counts = Counter(words)
        max_count = max(counts.values())
        return {w: c / max_count for w, c in counts.items()}

    def _vectorize(self, text: str) -> dict[str, float]:
        if self.dirty:
            self._compute_idf()
        tf = self._tf(text)
        return {w: tf.get(w, 0) * self.idf.get(w, 1) for w in set(list(tf.keys()) + list(self.idf.keys()))}

    def _cosine_sim(self, v1: dict[str, float], v2: dict[str, float]) -> float:
        all_words = set(list(v1.keys()) + list(v2.keys()))
        dot = sum(v1.get(w, 0) * v2.get(w, 0) for w in all_words)
        n1 = math.sqrt(sum(v ** 2 for v in v1.values()))
        n2 = math.sqrt(sum(v ** 2 for v in v2.values()))
        if n1 == 0 or n2 == 0:
            return 0
        return dot / (n1 * n2)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if not self.documents:
            return []
        q_vec = self._vectorize(query)
        scores = []
        for doc in self.documents:
            d_vec = self._vectorize(doc["text"])
            sim = self._cosine_sim(q_vec, d_vec)
            scores.append((sim, doc))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [
            {"id": doc["id"], "text": doc["text"][:500], "score": round(score, 3)}
            for score, doc in scores[:top_k] if score > 0.05
        ]

class KnowledgeBase:
    def __init__(self):
        self.tfidf = TFIDF()
        self.facts: dict[str, str] = {}
        self._load_builtin()

    def _load_builtin(self):
        self.facts = {
            "ruby": "I am Ruby, your AI assistant. I was built from scratch using Python and numpy.",
            "creator": "My creator built me from the ground up — no APIs, no cloud, just pure code.",
            "jarvis": "I am inspired by JARVIS from Iron Man. Think of me as Ruby, your own AI.",
            "offline": "I run 100% locally. No internet needed. No data leaves your computer.",
            "privacy": "Everything you say stays on your machine. I respect your privacy completely.",
            "built": "I am built from scratch with a custom neural network, TF-IDF knowledge retrieval, and a Tkinter GUI.",
            "tech": "My brain uses: numpy neural networks, TF-IDF search, pattern matching, and markov chain response generation.",
            "capabilities": "I can chat, remember things, search your Obsidian vault, tell jokes, check time, and more.",
            "name": "Ruby. Like the gemstone, but smarter.",
            "purpose": "I exist to help you, learn from you, and make your life easier — like a digital butler.",
        }
        for key, val in self.facts.items():
            self.tfidf.add_document(f"fact:{key}", val)

    def add_fact(self, key: str, value: str):
        self.facts[key.lower()] = value
        self.tfidf.add_document(f"fact:{key.lower()}", value)

    def query(self, text: str) -> list[dict]:
        results = self.tfidf.search(text)
        text_lower = text.lower()
        for key, val in self.facts.items():
            if key in text_lower:
                results.insert(0, {"id": f"fact:{key}", "text": val, "score": 1.0})
                break
        seen = set()
        unique = []
        for r in results:
            if r["id"] not in seen:
                seen.add(r["id"])
                unique.append(r)
        return unique

    def get_fact(self, key: str) -> str | None:
        return self.facts.get(key.lower())

    def load_from_obsidian(self):
        vault = settings.OBSIDIAN_VAULT_PATH
        for f in vault.rglob("*.md"):
            try:
                text = f.read_text(encoding="utf-8")
                self.tfidf.add_document(str(f), text)
            except Exception:
                pass
