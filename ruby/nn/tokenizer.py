import numpy as np
import re
from typing import Optional

class Tokenizer:
    def __init__(self):
        self.word_to_idx = {"<PAD>": 0, "<UNK>": 1}
        self.idx_to_word = {0: "<PAD>", 1: "<UNK>"}
        self.vocab_size = 2
        self.max_len = 20

    def fit(self, texts: list[str]):
        for text in texts:
            words = self._tokenize(text)
            for word in words:
                if word not in self.word_to_idx:
                    self.word_to_idx[word] = self.vocab_size
                    self.idx_to_word[self.vocab_size] = word
                    self.vocab_size += 1

    def _tokenize(self, text: str) -> list[str]:
        text = text.lower().strip()
        text = re.sub(r'[^a-z0-9\s?.!,]', '', text)
        return text.split()

    def encode(self, text: str, max_len: Optional[int] = None) -> np.ndarray:
        if max_len is None:
            max_len = self.max_len
        words = self._tokenize(text)[:max_len]
        indices = [self.word_to_idx.get(w, self.word_to_idx["<UNK>"]) for w in words]
        indices += [self.word_to_idx["<PAD>"]] * (max_len - len(indices))
        return np.array(indices, dtype=np.int32)

    def encode_batch(self, texts: list[str], max_len: Optional[int] = None) -> np.ndarray:
        return np.array([self.encode(t, max_len) for t in texts])

    def decode(self, indices: np.ndarray) -> str:
        words = []
        for i in indices:
            if i == self.word_to_idx["<PAD>"]:
                break
            words.append(self.idx_to_word.get(int(i), "<UNK>"))
        return " ".join(words)

    def get_word_vector(self, word: str, vocab_size: Optional[int] = None) -> np.ndarray:
        vs = vocab_size or self.vocab_size
        vec = np.zeros(vs)
        idx = self.word_to_idx.get(word, self.word_to_idx["<UNK>"])
        vec[idx] = 1
        return vec
