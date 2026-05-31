import numpy as np
import json
from pathlib import Path
from .layers import Dense, ReLU, Softmax, categorical_crossentropy, accuracy
from .optimizer import Adam
from .tokenizer import Tokenizer
from config.settings import settings

INTENTS = [
    "greeting", "farewell", "name_query", "capabilities",
    "time_query", "memory_save", "memory_recall", "help_request",
    "thanks", "insult", "praise", "joke_request", "weather_query",
    "unknown"
]

TRAINING_DATA = [
    ("hello", "greeting"), ("hi", "greeting"), ("hey", "greeting"),
    ("good morning", "greeting"), ("good evening", "greeting"),
    ("whats up", "greeting"), ("how are you", "greeting"),
    ("hey ruby", "greeting"), ("hi ruby", "greeting"), ("hello ruby", "greeting"),
    ("goodbye", "farewell"), ("bye", "farewell"), ("see you", "farewell"),
    ("later", "farewell"), ("good night", "farewell"), ("see you later", "farewell"),
    ("what is your name", "name_query"), ("who are you", "name_query"),
    ("what are you", "name_query"), ("your name", "name_query"),
    ("tell me about yourself", "name_query"), ("who is ruby", "name_query"),
    ("what can you do", "capabilities"), ("help me", "capabilities"),
    ("what do you do", "capabilities"), ("your capabilities", "capabilities"),
    ("show me what you can do", "capabilities"), ("list your skills", "capabilities"),
    ("what time is it", "time_query"), ("current time", "time_query"),
    ("whats the time", "time_query"), ("tell me time", "time_query"),
    ("give me the time", "time_query"), ("whats the current time", "time_query"),
    ("what day is it", "time_query"), ("todays date", "time_query"),
    ("remember this", "memory_save"), ("save this", "memory_save"),
    ("remember", "memory_save"), ("dont forget", "memory_save"),
    ("remember that", "memory_save"), ("save that", "memory_save"),
    ("keep this", "memory_save"), ("write this down", "memory_save"),
    ("do you remember", "memory_recall"), ("recall", "memory_recall"),
    ("what do you know about", "memory_recall"), ("search memory", "memory_recall"),
    ("look up", "memory_recall"), ("find memory", "memory_recall"),
    ("what do you remember", "memory_recall"), ("retrieve", "memory_recall"),
    ("help", "help_request"), ("commands", "help_request"),
    ("what commands", "help_request"), ("how to use", "help_request"),
    ("show commands", "help_request"), ("available commands", "help_request"),
    ("thanks", "thanks"), ("thank you", "thanks"), ("thanks ruby", "thanks"),
    ("thank you ruby", "thanks"), ("appreciate it", "thanks"),
    ("much obliged", "thanks"), ("you are useless", "insult"),
    ("you suck", "insult"), ("stupid", "insult"), ("bad", "insult"),
    ("dumb", "insult"), ("useless", "insult"), ("terrible", "insult"),
    ("you are amazing", "praise"), ("good job", "praise"),
    ("you are great", "praise"), ("awesome", "praise"),
    ("brilliant", "praise"), ("fantastic", "praise"),
    ("tell me a joke", "joke_request"), ("joke", "joke_request"),
    ("make me laugh", "joke_request"), ("funny", "joke_request"),
    ("crack a joke", "joke_request"), ("humour me", "joke_request"),
    ("weather", "weather_query"), ("temperature", "weather_query"),
    ("is it raining", "weather_query"), ("forecast", "weather_query"),
    ("how is the weather", "weather_query"), ("weather today", "weather_query"),
]

class IntentClassifier:
    def __init__(self):
        self.tokenizer = Tokenizer()
        self.intents = INTENTS
        self.intent_to_idx = {n: i for i, n in enumerate(INTENTS)}
        self.model_path = Path("ruby_intents.json")
        self.layer1 = None
        self.layer2 = None
        self.relu = ReLU()
        self.softmax = Softmax()
        self.optimizer = Adam(lr=0.005)
        self._setup()

    def _setup(self):
        texts = [t for t, _ in TRAINING_DATA]
        self.tokenizer.fit(texts)
        self.tokenizer.max_len = 10
        input_size = self.tokenizer.max_len

        if self.model_path.exists():
            self._load()
        else:
            self.layer1 = Dense(input_size, 64)
            self.layer2 = Dense(64, len(self.intents))
            self._train()

    def _train(self, epochs: int = 100):
        texts = [t for t, _ in TRAINING_DATA]
        labels = [self.intent_to_idx[l] for _, l in TRAINING_DATA]

        X = self.tokenizer.encode_batch(texts)
        X_flat = X.astype(np.float32) / self.tokenizer.vocab_size

        y = np.array(labels)

        for epoch in range(epochs):
            h1 = self.relu.forward(self.layer1.forward(X_flat))
            output = self.softmax.forward(self.layer2.forward(h1))

            loss = categorical_crossentropy(output, y)
            acc = accuracy(output, y)

            dout = output.copy()
            dout[range(len(dout)), y] -= 1
            dout /= len(dout)

            dh1 = self.layer2.backward(dout)
            drelu = self.relu.backward(dh1)
            self.layer1.backward(drelu)

            self.optimizer.update_params(self.layer1, 0, None)
            self.optimizer.update_params(self.layer2, 1, None)

            if epoch % 20 == 0:
                pass

        self._save()

    KEYWORD_MAP = [
        (["goodbye", "bye", "see you", "cya", "farewell", "later", "leaving"], "farewell"),
        (["hello", "hi ", "hey ", "good morning", "good evening", "hi ruby", "hey ruby", "whats up", "how are you"], "greeting"),
        (["your name", "who are you", "what are you", "tell me about yourself", "who is ruby"], "name_query"),
        (["can you do", "capabilities", "your skills", "what do you do", "help me with"], "capabilities"),
        (["time", "clock", "what day", "todays date", "current date"], "time_query"),
        (["remember this", "remember that", "save this", "save that", "dont forget", "write this", "keep this"], "memory_save"),
        (["do you remember", "recall", "look up", "search memory", "find memory", "retrieve", "what do you know about"], "memory_recall"),
        (["joke", "make me laugh", "funny", "humour", "crack"], "joke_request"),
        (["weather", "temperature", "raining", "forecast", "cold", "hot outside"], "weather_query"),
        (["help", "commands", "how to", "what commands", "/help"], "help_request"),
        (["thank", "thanks", "appreciate", "grateful"], "thanks"),
        (["stupid", "useless", "terrible", "dumb", "suck", "bad", "hate"], "insult"),
        (["amazing", "great", "awesome", "brilliant", "fantastic", "good job", "love", "perfect"], "praise"),
    ]

    def classify(self, text: str) -> tuple[str, float]:
        text_lower = text.lower().strip()

        for keywords, intent in self.KEYWORD_MAP:
            for kw in keywords:
                if kw in text_lower:
                    return intent, 0.85

        X = self.tokenizer.encode(text).reshape(1, -1).astype(np.float32) / self.tokenizer.vocab_size
        h1 = self.relu.forward(self.layer1.forward(X))
        output = self.softmax.forward(self.layer2.forward(h1))
        idx = np.argmax(output[0])
        confidence = float(output[0][idx])
        return self.intents[idx], confidence

    def _save(self):
        data = {
            "w1": self.layer1.weights.tolist(),
            "b1": self.layer1.biases.tolist(),
            "w2": self.layer2.weights.tolist(),
            "b2": self.layer2.biases.tolist(),
            "word_to_idx": self.tokenizer.word_to_idx,
            "max_len": self.tokenizer.max_len,
            "vocab_size": self.tokenizer.vocab_size
        }
        self.model_path.write_text(json.dumps(data), encoding="utf-8")

    def _load(self):
        data = json.loads(self.model_path.read_text(encoding="utf-8"))
        self.tokenizer.word_to_idx = data["word_to_idx"]
        self.tokenizer.vocab_size = len(data["word_to_idx"])
        self.tokenizer.idx_to_word = {v: k for k, v in data["word_to_idx"].items()}
        self.tokenizer.max_len = data.get("max_len", 10)

        input_size = self.tokenizer.max_len
        self.layer1 = Dense(input_size, 64)
        self.layer2 = Dense(64, len(self.intents))
        self.layer1.weights = np.array(data["w1"])
        self.layer1.biases = np.array(data["b1"])
        self.layer2.weights = np.array(data["w2"])
        self.layer2.biases = np.array(data["b2"])
