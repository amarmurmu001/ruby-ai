import tkinter as tk
import sys
import ctypes
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.theme import Theme
from gui.controller import Controller
from gui.widgets.title_bar import TitleBar
from gui.widgets.status_bar import StatusBar
from gui.widgets.sidebar import Sidebar
from gui.widgets.chat_panel import ChatPanel
from gui.widgets.info_panel import InfoPanel
from gui.widgets.input_bar import InputBar
from gui.widgets.visualizer import WaveVisualizer
from gui.widgets.tray import SystemTray
from gui.widgets.settings import SettingsPanel

def voice_summary(text: str, max_chars: int = 300) -> str:
    stripped = re.sub(r"```[\s\S]*?```", "", text)
    stripped = re.sub(r"`[^`]+`", "", stripped)
    stripped = re.sub(r"\[Source:.*?\]", "", stripped)
    stripped = re.sub(r"^---\s*$", "", stripped, flags=re.MULTILINE)
    stripped = re.sub(r"http[s]?://\S+", "", stripped)
    stripped = re.sub(r"[A-Z]:\\[^\s,;)]+", "", stripped)
    stripped = re.sub(r"/[a-zA-Z0-9_\-./]+\.\w{2,4}", "", stripped)

    lines = []
    for line in stripped.split("\n"):
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("- ") or clean.startswith("* "):
            continue
        if re.match(r"^\d+[.)]", clean):
            continue
        lines.append(clean)

    summary = " ".join(lines)
    summary = re.sub(r"\s+", " ", summary).strip()
    if len(summary) > max_chars:
        summary = summary[:max_chars].rsplit(". ", 1)[0]
        if not summary.endswith("."):
            summary = summary[:max_chars].rsplit("?", 1)[0]
        if not summary:
            summary = text.split(". ")[0] + "."
    return summary


def _check_deps() -> list[str]:
    missing = []
    checks = [
        ("numpy", "numpy", "array ops"),
        ("requests", "requests", "HTTP/API"),
        ("sounddevice", "sounddevice", "mic input"),
        ("speech_recognition", "speech_recognition", "STT"),
        ("duckduckgo_search", "duckduckgo_search", "web search"),
    ]
    for name, pkg, purpose in checks:
        try:
            __import__(name)
        except ImportError:
            missing.append(f"  {pkg} — {purpose}")
    return missing


def _try_dark_title_bar(hwnd: int) -> bool:
    try:
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        val = ctypes.c_int(1)
        r = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(val), ctypes.sizeof(val)
        )
        return r == 0
    except Exception:
        return False


class RubyGUI:
    def __init__(self):
        missing = _check_deps()
        if missing:
            msg = "Missing dependencies:\n" + "\n".join(missing)
            msg += "\n\nRun: pip install " + " ".join(m.split(" — ")[0] for m in missing)
            import tkinter.messagebox as mb
            mb.showerror("Ruby — Dependencies Missing", msg)

        self.ctrl = Controller()

        self.root = tk.Tk()
        self.root.title("")
        self.root.geometry("1100x740")
        self.root.configure(bg=Theme.BG_DARK)
        self.root.minsize(900, 640)

        self.root.update_idletasks()
        hwnd = self.root.winfo_id()
        self.use_custom_titlebar = not _try_dark_title_bar(hwnd)
        if self.use_custom_titlebar:
            self.root.overrideredirect(True)

        try:
            blank = tk.PhotoImage(width=1, height=1)
            self.root.iconphoto(True, blank)
        except Exception:
            pass

        self.mic_active = False
        self.wake_enabled = False
        self.is_processing = False
        self.anim_start = 0.0
        self._cancel_btn = None

        self._build_layout()
        self._bind_events()
        self._start_animation()
        self._show_welcome()
        self._setup_tray()

    def _build_layout(self):
        self.root.columnconfigure(0, weight=1)
        row = 0

        if self.use_custom_titlebar:
            self.title_bar = TitleBar(self.root,
                on_close=self._on_closing,
                on_minimize=lambda: self.root.iconify(),
                on_maximize=self._toggle_maximize)
            self.root.rowconfigure(row, weight=0)
            row += 1

        self.status_bar = StatusBar(self.root, self.ctrl, on_cancel=self._on_cancel_think)
        self.status_bar.frame.grid(row=row, column=0, sticky="ew")
        self.root.rowconfigure(row, weight=0)
        self._status_row = row
        row += 1

        main_frame = Theme.frame(self.root)
        main_frame.grid(row=row, column=0, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        self.root.rowconfigure(row, weight=1)
        self._main_row = row
        row += 1

        self.sidebar = Sidebar(main_frame, self.ctrl,
                               on_switch_conv=self._on_switch_conv,
                               on_delete_conv=self._on_delete_conv)
        self.chat = ChatPanel(main_frame)
        self.info = InfoPanel(main_frame, self.ctrl)
        self.settings = SettingsPanel(self.root, self.ctrl)

        self.visualizer = WaveVisualizer(self.root)
        self.visualizer.frame.grid(row=row, column=0, sticky="ew")
        self.root.rowconfigure(row, weight=0)
        self._vis_row = row
        row += 1

        self.input = InputBar(self.root,
            on_send=self._on_send,
            on_mic_press=self._on_mic_press,
            on_mic_release=self._on_mic_release)
        self.input.frame.grid(row=row, column=0, sticky="ew")
        self.root.rowconfigure(row, weight=0)
        self._input_row = row
        row += 1

        self.root.bind("<Configure>", self._on_resize)

    def _on_resize(self, event=None):
        if event and event.widget != self.root:
            return
        w = self.root.winfo_width()
        if w < 800:
            self.sidebar.toggle_off()
            self.info.toggle_off()
        elif w < 950:
            self.sidebar.toggle_off()
            self.info.toggle_on()
        else:
            self.sidebar.toggle_on()
            self.info.toggle_on()

    def _on_escape(self, event=None):
        if self.settings.visible:
            self.settings.hide()
        elif hasattr(self, "tray") and self.tray and self.tray._icon:
            self._minimize_to_tray()

    def _on_delete_conv(self, conv_id: str):
        self.chat.clear_all()
        self._show_welcome()

    def _on_switch_conv(self, conv_id: str):
        self.chat.clear_all()
        conv = self.ctrl.brain._current_messages()
        for msg in conv:
            if msg["role"] == "user":
                self.chat.add("user", "AMAR", msg["content"])
            elif msg["role"] == "assistant":
                self.chat.add("ruby", "RUBY", msg["content"])
        self.sidebar.refresh()
        self.info.refresh()

    def _toggle_maximize(self):
        if self.root.state() == "zoomed":
            self.root.state("normal")
        else:
            self.root.state("zoomed")

    def _bind_events(self):
        self.root.bind("<Escape>", self._on_escape)
        self.root.bind("<Control-m>", lambda e: self._on_mic_press())
        self.root.bind("<Control-comma>", lambda e: self.settings.toggle())
        self.root.bind("<Control-f>", lambda e: self.chat.show_search())
        self.root.bind("<Control-Up>", lambda e: self._focus_input())
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _focus_input(self):
        self.input.focus()

    def _setup_tray(self):
        self.tray = SystemTray(self.root)
        if self.tray.setup():
            self.tray.run()
            self.root.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)
            self.root.bind("<Control-Shift-R>", lambda e: self._show_from_tray())

    def _minimize_to_tray(self):
        self.root.withdraw()

    def _show_from_tray(self):
        self.root.deiconify()
        self.root.lift()

    def _on_closing(self):
        self.tray.stop()
        self.ctrl.shutdown()
        try:
            self.root.destroy()
        except Exception:
            pass

    def _show_welcome(self):
        from config.settings import settings
        v = settings.OBSIDIAN_VAULT_PATH
        voice_name = "OFFLINE"
        if self.ctrl.voice and self.ctrl.voice.enabled:
            try:
                voice_name = self.ctrl.voice.get_voice_name()
            except Exception:
                voice_name = "ACTIVE"
        self.chat.welcome(
            backend=self.ctrl.backend_name,
            vault=v.name if v.exists() else "NOT FOUND",
            voice=voice_name,
            mic=self.ctrl.has_mic,
        )
        self.status_bar.refresh()
        self.info.refresh()

    def _start_animation(self):
        self.anim_start = __import__("time").time()
        self._animate()

    def _animate(self):
        dt = 0.03
        is_active = self.mic_active or self.is_processing
        self.visualizer.update(dt, is_active)
        self.visualizer.draw()
        self.root.after(30, self._animate)

    def _on_send(self, text):
        if not text.strip():
            return
        self.chat.add("user", "AMAR", text)

        if text.startswith("/"):
            self._handle_command(text)
            return

        self.is_processing = True
        self.chat.show_thinking()
        self.status_bar.show_cancel(True)
        self.info.log_action(f"user: {text[:40]}")
        self.ctrl.think_async(text, self._on_response)

    def _on_cancel_think(self):
        self.ctrl.cancel_think()
        self.status_bar.show_cancel(False)

    def _on_response(self, response: str):
        self.root.after(0, self.chat.clear_thinking)
        self.root.after(0, lambda: self.info.log_action(f"ruby: {response[:40]}"))
        self.root.after(50, lambda: self.chat.add("ruby", "RUBY", response))
        self.root.after(100, self._speak_response, response)
        self.root.after(50, lambda: setattr(self, "is_processing", False))
        self.root.after(50, lambda: self.status_bar.show_cancel(False))

    def _speak_response(self, text):
        if self.ctrl.voice and self.ctrl.voice.enabled:
            self.is_processing = True
            self.status_bar.show_cancel(False)
            speech = voice_summary(text)
            if speech:
                self.ctrl.speak(speech)
                delay = max(2000, len(speech) * 60)
                self.root.after(delay, lambda: setattr(self, "is_processing", False))
            else:
                self.root.after(50, lambda: setattr(self, "is_processing", False))

    def _on_mic_press(self):
        if self.mic_active or not self.ctrl.has_mic:
            return
        self.mic_active = True
        self.input.mic_btn.config(fg=Theme.STATUS_ON)
        self.ctrl.listen_async(self._on_mic_result)

    def _on_mic_release(self):
        if self.mic_active:
            self.ctrl.listen_stop()

    def _on_mic_result(self, text):
        self.mic_active = False
        self.input.mic_btn.config(fg=Theme.TEXT_PRIMARY)
        if text:
            self._on_send(text)
        self.input.clear()

    def _on_heard(self, text, via_wake=False):
        if via_wake:
            self.root.after(0, lambda: self.chat.add("voice", "WAKE",
                f"[COMMAND] Ruby, {text}"))
            self.root.after(0, lambda: self._on_send(text))

    def _toggle_voice(self):
        if not self.ctrl.voice:
            self.chat.add("system", "SYS", "[-] voice unavailable")
            return
        enabled = self.ctrl.voice.toggle()
        self.chat.add("system", "SYS",
            f"[*] voice {'on' if enabled else 'off'}")
        self.status_bar.refresh()
        self.info.log_action(f"voice {'on' if enabled else 'off'}")

    def _toggle_wake(self):
        self.wake_enabled = not self.wake_enabled
        if self.wake_enabled:
            if self.ctrl.has_mic:
                self.ctrl.start_wake(self._on_heard, "ruby")
                self.chat.add("system", "SYS",
                    "[*] wake active — listening for 'ruby'")
            else:
                self.wake_enabled = False
                self.chat.add("system", "SYS", "[-] wake failed — no mic")
        else:
            self.ctrl.stop_wake()
            self.chat.add("system", "SYS", "[-] wake deactivated")

    def _handle_command(self, cmd):
        cmd = cmd.strip().lower()

        if cmd in ("/exit", "/quit"):
            self._on_closing()

        elif cmd == "/help":
            self.chat.add("system", "HELP",
                "[+] /help     show this\n"
                "[+] /exit     shutdown\n"
                "[+] /reset    reset session\n"
                "[+] /voice    toggle voice output\n"
                "[+] /wake     toggle wake word\n"
                "[+] /vault    vault status\n"
                "[+] /status   system diagnostics\n"
                "[+] /sidebar  toggle sidebar\n"
                "[+] /info     toggle info panel\n"
                "[+] /settings settings panel\n"
                "[+] /mic      activate microphone")

        elif cmd == "/reset":
            if self.ctrl.brain:
                self.ctrl.brain.reset()
            self.chat.clear_all()
            self._show_welcome()

        elif cmd == "/voice":
            self._toggle_voice()

        elif cmd == "/wake":
            self._toggle_wake()

        elif cmd == "/sidebar":
            self.sidebar.toggle()

        elif cmd == "/info":
            self.info.toggle()

        elif cmd == "/settings":
            self.settings.toggle()

        elif cmd == "/mic":
            self._on_mic_press()

        elif cmd == "/status":
            self.status_bar.refresh()
            self.info.refresh()
            self.chat.add("system", "STATUS", "[*] system diagnostic complete")

        elif cmd == "/vault":
            self._show_vault_info()

        else:
            self.chat.add("error", "SYS",
                f"[-] unknown command '{cmd}' — try /help")

    def _show_vault_info(self):
        from config.settings import settings
        p = settings.OBSIDIAN_VAULT_PATH
        if not p.exists():
            self.chat.add("system", "VAULT", f"[-] vault not found: {p}")
            return
        folders = [d.name for d in p.iterdir() if d.is_dir() and not d.name.startswith('.')]
        note_count = len(list(p.rglob("*.md")))
        watcher = "active" if (self.ctrl.brain and hasattr(self.ctrl.brain, "_watcher")
                               and self.ctrl.brain._watcher.is_running) else "off"
        info = (
            f"[*] vault: {p.name}\n"
            f"[*] path: {p}\n"
            f"[*] notes: {note_count}\n"
            f"[*] folders: {', '.join(folders[:6])}\n"
            f"[*] auto-index: {watcher}"
        )
        self.chat.add("system", "VAULT", info)

    def run(self):
        self.root.mainloop()
