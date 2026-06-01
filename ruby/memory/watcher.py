import logging
import threading
import time
from pathlib import Path
from config.settings import settings

logger = logging.getLogger("ruby.memory.watcher")

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    Observer = None
    FileSystemEventHandler = object


class VaultChangeHandler(FileSystemEventHandler):
    def __init__(self, on_change):
        self.on_change = on_change
        self._debounce_timer = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".md"):
            return
        with self._lock:
            if self._debounce_timer:
                self._debounce_timer.cancel()
            self._debounce_timer = threading.Timer(3.0, self._fire)
            self._debounce_timer.daemon = True
            self._debounce_timer.start()

    def _fire(self):
        try:
            self.on_change()
        except Exception as e:
            logger.warning("Watcher callback error: %s", e)


class VaultWatcher:
    def __init__(self, brain=None):
        self.brain = brain
        self._observer = None
        self._thread = None
        self._running = False
        self._pending_reindex = False

    def start(self):
        if not HAS_WATCHDOG:
            logger.info("watchdog not installed — vault monitoring disabled")
            return False
        vault = settings.OBSIDIAN_VAULT_PATH
        if not vault.exists():
            logger.warning("Vault not found at %s", vault)
            return False

        self._observer = Observer()
        handler = VaultChangeHandler(self._on_vault_change)
        self._observer.schedule(handler, str(vault), recursive=True)
        self._observer.daemon = True
        self._observer.start()
        self._running = True
        logger.info("Vault watcher started on %s", vault)
        return True

    def stop(self):
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=3)

    def _on_vault_change(self):
        if not self.brain:
            return
        self._pending_reindex = True
        logger.info("Vault change detected — reindexing embeddings")
        try:
            from ruby.memory.embeddings import VectorMemory
            if self.brain.custom:
                vec = VectorMemory(self.brain.custom)
                vault = settings.OBSIDIAN_VAULT_PATH
                for f in vault.rglob("*.md"):
                    vec.index_memory(f)
                logger.info("Embedding reindex complete")
        except Exception as e:
            logger.warning("Reindex error: %s", e)

    @property
    def is_running(self) -> bool:
        return self._running
