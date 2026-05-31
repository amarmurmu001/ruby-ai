import json
import logging
import numpy as np
from pathlib import Path
from typing import Optional
from config.settings import settings

logger = logging.getLogger("ruby.memory.embeddings")

try:
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

class VectorMemory:
    def __init__(self, brain):
        self.brain = brain
        self.index_path = settings.OBSIDIAN_VAULT_PATH / "ruby_index.json"
        self.index = self._load_index()

    def _load_index(self) -> dict:
        if self.index_path.exists():
            try:
                return json.loads(self.index_path.read_text(encoding="utf-8"))
            except Exception:
                return {"chunks": []}
        return {"chunks": []}

    def _save_index(self):
        self.index_path.write_text(json.dumps(self.index, indent=2), encoding="utf-8")

    def _chunk_text(self, text: str, chunk_size: int = 512) -> list[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))
        return chunks

    def index_memory(self, path: Path):
        text = path.read_text(encoding="utf-8")
        chunks = self._chunk_text(text)

        existing = [c for c in self.index["chunks"] if c["source"] == str(path)]
        self.index["chunks"] = [c for c in self.index["chunks"] if c["source"] != str(path)]

        for chunk in chunks:
            embedding = self.brain.generate_embedding(chunk)
            if embedding:
                self.index["chunks"].append({
                    "source": str(path),
                    "text": chunk,
                    "embedding": embedding
                })

        self._save_index()
        logger.info("Indexed %d chunks from %s", len(chunks), path)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self.index["chunks"]:
            return []

        query_embedding = self.brain.generate_embedding(query)
        if not query_embedding:
            return []

        embeddings = np.array([c["embedding"] for c in self.index["chunks"]])
        query_vec = np.array(query_embedding).reshape(1, -1)

        if HAS_SKLEARN:
            scores = cosine_similarity(query_vec, embeddings)[0]
        else:
            norms = np.linalg.norm(embeddings, axis=1)
            query_norm = np.linalg.norm(query_vec)
            scores = np.dot(embeddings, query_vec.T).flatten() / (norms * query_norm + 1e-8)

        top_indices = np.argsort(scores)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if scores[idx] > 0.3:
                results.append({
                    "source": self.index["chunks"][idx]["source"],
                    "text": self.index["chunks"][idx]["text"][:500],
                    "score": float(scores[idx])
                })

        return results

    def get_context(self, query: str, max_chars: int = 2000) -> str:
        results = self.search(query)
        parts = []
        for r in results:
            parts.append(f"[Source: {r['source']}] (score: {r['score']:.2f})\n{r['text']}")
        combined = "\n\n".join(parts)
        return combined[:max_chars]

    def reindex_all(self):
        self.index = {"chunks": []}
        vault = settings.OBSIDIAN_VAULT_PATH
        for f in vault.rglob("*.md"):
            self.index_memory(f)
        logger.info("Reindexed all memories")
