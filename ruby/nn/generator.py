import random
import re
from datetime import datetime
from .knowledge import KnowledgeBase

GREETINGS = [
    "Hey Boss, what can I do for you?",
    "Right here, Boss. What's up?",
    "At your service. What do you need?",
    "Ready when you are, Boss.",
    "Ruby online. What's the plan?",
    "Boss! How can I help today?",
]

FAREWELLS = [
    "Take care, Boss. I'll be here.",
    "Shutting down. Call me anytime.",
    "Goodbye, Boss. It was a pleasure.",
    "See you later, Boss. Ruby out.",
    "Until next time, Boss.",
]

CAPABILITIES = [
    "I can chat with you, remember things, search your files, tell jokes, check the time, and more. Just ask!",
    "Think of me as JARVIS but built from scratch. I can hold conversations, store memories in your Obsidian vault, search for information, and run commands.",
    "My skills: natural conversation, memory storage and recall, knowledge search, joke telling, time checks, and file operations. All running locally on your machine.",
]

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I told my computer I needed a break. Now it won't stop sending me vacation ads.",
    "Why did the AI break up with the database? Too many relationships.",
    "What's a computer's favorite snack? Microchips!",
    "Why was the Python programmer so good at his job? He had excellent range.",
    "I'm not lazy, I'm on energy-saving mode.",
    "Why do they call it 'debugging'? Because 'removing features' was already taken.",
    "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
]

INTRO = "I'm Ruby — your AI assistant, built from scratch. No APIs, no cloud, just pure Python and numpy. Think of me as your own JARVIS."

class ResponseGenerator:
    def __init__(self, knowledge_base: KnowledgeBase, save_callback=None):
        self.kb = knowledge_base
        self.markov = MarkovChain()
        self.save_callback = save_callback
        self._init_markov()

    def _init_markov(self):
        corpus = GREETINGS + FAREWELLS + CAPABILITIES + JOKES + [INTRO]
        for fact in self.kb.facts.values():
            corpus.append(fact)
        for text in corpus:
            self.markov.train(text)

    def generate(self, intent: str, text: str, confidence: float) -> str:
        text_lower = text.lower()

        if intent == "greeting":
            return random.choice(GREETINGS)

        if intent == "farewell":
            return random.choice(FAREWELLS)

        if intent == "name_query":
            return "I'm Ruby. Built from scratch, no APIs, just pure code. Like JARVIS, but smarter and offline."

        if intent == "capabilities":
            return random.choice(CAPABILITIES) + " " + INTRO

        if intent == "time_query":
            now = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
            return f"It's {now}, Boss."

        if intent == "thanks":
            return random.choice([
                "Anytime, Boss. That's what I'm here for.",
                "You're welcome, Boss!",
                "Glad I could help, Boss.",
                "My pleasure, Boss.",
            ])

        if intent == "insult":
            return random.choice([
                "Ouch. I'll try harder, Boss.",
                "I'm doing my best with what I've got. Be patient with me.",
                "I'm still learning, Boss. Give me time.",
            ])

        if intent == "praise":
            return random.choice([
                "Thanks, Boss! I try my best.",
                "I appreciate that, Boss. Let's keep building.",
                "You're not so bad yourself, Boss.",
            ])

        if intent == "joke_request":
            return random.choice(JOKES)

        if intent == "help_request":
            return ("Commands: just talk to me naturally! I can greet you, tell jokes, "
                    "remember things, search my knowledge, check the time, and more. "
                    "Say 'remember this' to save something, or ask 'do you remember' to recall.")

        if intent == "memory_save":
            content = self._extract_content(text)
            if content:
                if self.save_callback:
                    path = self.save_callback(content)
                    return f"Saved to vault: '{content}'"
                return f"I'll remember that, Boss. Saving: '{content}'"
            return "What should I remember, Boss?"

        if intent == "memory_recall":
            text_lower = text.lower()
            direct = self.kb.get_fact(text_lower)
            if direct:
                return f"Found: {direct}"
            results = self.kb.query(text)
            if results:
                best = results[0]
                return f"I found: {best['text']}"
            return "I don't have any memories about that yet, Boss."

        knowledge = self.kb.query(text)
        if knowledge:
            best = knowledge[0]
            if best["score"] > 0.15:
                return best["text"]

        markov_reply = self.markov.generate()
        if markov_reply and random.random() < 0.3:
            return markov_reply

        return self._fallback(text)

    def _fallback(self, text: str) -> str:
        text_lower = text.lower()

        if re.search(r'\byou\b', text_lower) and re.search(r'\b(?:are|can|will)\b', text_lower):
            return ("I'm Ruby, your custom-built AI. I run entirely on your machine "
                    "with my own neural network brain. No cloud, no APIs.")
        if "?" in text:
            return ("That's a good question, Boss. I'll keep learning so I can "
                    "give you better answers.")
        if re.search(r'\b(?:tell|say|speak)\b', text_lower):
            return ("I'd tell you something clever, but I'm still growing my brain. "
                    "Ask me about what I can do!")
        if len(text.split()) > 5:
            return ("I hear you, Boss. I'm processing what you said. "
                    "The more we talk, the better I'll understand.")
        return random.choice([
            "Interesting, Boss. Tell me more.",
            "I'm listening, Boss. What else is on your mind?",
            "I see. Go on, Boss.",
            "Noted, Boss. Is there something specific you need?",
            "I hear you loud and clear, Boss.",
        ])

    def _extract_content(self, text: str) -> str | None:
        patterns = [
            r"(?:remember this|remember|save this|dont forget)\s*:?\s*(?:that\s+)?(.+)",
            r"remember that (.+)",
            r"save (.+)",
            r"remember: (.+)",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        words = text.split()
        if len(words) > 4:
            return text.strip()
        return None

class MarkovChain:
    def __init__(self, order: int = 2):
        self.order = order
        self.chain: dict[tuple[str, ...], list[str]] = {}

    def train(self, text: str):
        words = text.lower().split()
        if len(words) <= self.order:
            return
        for i in range(len(words) - self.order):
            key = tuple(words[i:i + self.order])
            next_word = words[i + self.order]
            if key not in self.chain:
                self.chain[key] = []
            self.chain[key].append(next_word)

    def generate(self, max_words: int = 15) -> str | None:
        if not self.chain:
            return None
        keys = list(self.chain.keys())
        key = random.choice(keys)
        words = list(key)
        for _ in range(max_words - self.order):
            if key in self.chain:
                next_word = random.choice(self.chain[key])
                words.append(next_word)
                key = tuple(words[-self.order:])
            else:
                break
        return " ".join(words).capitalize()
