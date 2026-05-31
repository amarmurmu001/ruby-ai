import os
from pathlib import Path

_ENV_FILE = Path(__file__).parent.parent / ".env"
if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)

class Settings:
    APP_NAME = "Ruby"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "Your AI Assistant — Like Jarvis, but Ruby."

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    HERMES_MODEL = os.getenv("HERMES_MODEL", "hermes3:8b")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")

    OBSIDIAN_VAULT_PATH = Path(os.getenv(
        "OBSIDIAN_VAULT_PATH",
        r"C:\Users\iron5\OneDrive\Desktop\2ndbrain"
    ))
    OBSIDIAN_MEMORY_DIR = "RubyMemory"
    OBSIDIAN_JOURNAL_DIR = "Daily"

    VOICE_ENABLED = os.getenv("RUBY_VOICE", "false").lower() == "true"
    TTS_ENGINE = os.getenv("RUBY_TTS", "system")
    STT_ENGINE = os.getenv("RUBY_STT", "system")

    AUTONOMOUS_MODE = os.getenv("RUBY_AUTONOMOUS", "false").lower() == "true"
    MAX_TOOL_RETRIES = 3
    MAX_PLAN_STEPS = 10

    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    MEMORY_TOP_K = 5

    LOG_LEVEL = os.getenv("RUBY_LOG_LEVEL", "INFO")

    WORKSPACE_DIR = Path.cwd()

    @classmethod
    def ensure_dirs(cls):
        cls.OBSIDIAN_VAULT_PATH.mkdir(parents=True, exist_ok=True)
        memory_path = cls.OBSIDIAN_VAULT_PATH / cls.OBSIDIAN_MEMORY_DIR
        memory_path.mkdir(parents=True, exist_ok=True)
        journal_path = cls.OBSIDIAN_VAULT_PATH / cls.OBSIDIAN_JOURNAL_DIR
        journal_path.mkdir(parents=True, exist_ok=True)

settings = Settings()
