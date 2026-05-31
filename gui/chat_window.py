import tkinter as tk
from tkinter import font
import threading
import time
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class ScanningLine:
    def __init__(self, width):
        self.y = 0
        self.speed = 1.5
        self.width = width

    def update(self):
        self.y += self.speed
        if self.y > 720:
            self.y = 0

    def draw(self, canvas):
        canvas.create_line(0, self.y, self.width, self.y,
            fill="#00d4ff", width=1, tags="scanline")
        canvas.create_line(0, self.y - 2, self.width, self.y - 2,
            fill="#004466", width=3, tags="scanline")
        canvas.create_line(0, self.y + 2, self.width, self.y + 2,
            fill="#004466", width=3, tags="scanline")


class Particle:
    def __init__(self, width, height):
        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.5, -0.1)
        self.size = random.uniform(1, 2.5)
        self.alpha = random.uniform(0.2, 0.6)
        self.life = random.uniform(2, 6)
        self.max_life = self.life

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.life -= dt
        return self.life > 0

    def draw(self, canvas):
        alpha = int(self.alpha * (self.life / self.max_life) * 60)
        if alpha > 0:
            canvas.create_oval(
                self.x - self.size, self.y - self.size,
                self.x + self.size, self.y + self.size,
                fill="#00d4ff", outline="", tags="particle"
            )


class RubyGUI:
    BG_DARK = "#050510"
    BG_MED = "#0a0a1a"
    BG_LIGHT = "#0f0f2a"
    ACCENT = "#00d4ff"
    ACCENT2 = "#0088ff"
    ACCENT_DIM = "#003366"
    TEXT_PRIMARY = "#c8d8ff"
    TEXT_SECONDARY = "#6688aa"
    TEXT_DIM = "#334466"
    USER_COLOR = "#00ff88"
    RUBY_COLOR = "#00d4ff"
    ERROR_COLOR = "#ff4466"
    PANEL_BG = "#080818"
    PANEL_BORDER = "#0a1a2a"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RUBY")
        self.root.geometry("1000x720")
        self.root.configure(bg=self.BG_DARK)
        self.root.minsize(800, 600)

        self.ruby = None
        self.listener = None
        self.voice = None
        self.mic_active = False
        self.wake_enabled = False
        self.particles = []
        self.anim_start = time.time()
        self.thinking_start = None

        self.root.overrideredirect(False)

        self._init_modules()
        self._build_layout()
        self._init_animations()
        self._bind_events()
        self._start_animation()
        self._show_welcome()

    def _init_modules(self):
        try:
            from gui.voice import VoiceEngine
            self.voice = VoiceEngine()
        except Exception:
            self.voice = None
        try:
            from ruby.tools.voice_listener import VoiceListener
            self.listener = VoiceListener()
            if not self.listener.available:
                self.listener = None
        except Exception:
            self.listener = None

    def _build_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

        self._build_top_hud()
        self._build_center_area()
        self._build_bottom_hud()

    def _build_top_hud(self):
        top = tk.Frame(self.root, bg=self.BG_DARK, height=80)
        top.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 0))
        top.grid_propagate(False)

        canvas_bg = tk.Canvas(top, height=80, bg=self.BG_DARK, highlightthickness=0)
        canvas_bg.pack(fill="x")

        canvas_bg.create_line(20, 78, 300, 78, fill=self.ACCENT_DIM, width=1, tags="topline")
        canvas_bg.create_line(700, 78, 980, 78, fill=self.ACCENT_DIM, width=1, tags="topline")

        title_font = font.Font(family="Segoe UI", size=22, weight="bold")
        tk.Label(top, text="RUBY", font=title_font,
                 fg=self.ACCENT, bg=self.BG_DARK).place(x=30, y=18)

        sub_font = font.Font(family="Segoe UI", size=9)
        tk.Label(top, text="AI ASSISTANT  //  v1.0",
                 font=sub_font, fg=self.TEXT_DIM, bg=self.BG_DARK).place(x=30, y=52)

        self.status_label = tk.Label(top, text=">> SYSTEM ONLINE <<",
            font=font.Font(family="Consolas", size=10),
            fg=self.USER_COLOR, bg=self.BG_DARK)
        self.status_label.place(x=370, y=30)

        right_x = 700
        info_font = font.Font(family="Consolas", size=9)

        self.voice_btn = tk.Label(top, text="[ VOICE : ON ]" if (self.voice and self.voice.enabled) else "[ VOICE : OFF ]",
            font=info_font, fg=self.ACCENT if (self.voice and self.voice.enabled) else self.TEXT_DIM,
            bg=self.BG_DARK, cursor="hand2")
        self.voice_btn.place(x=right_x, y=18)
        self.voice_btn.bind("<Button-1>", lambda e: self._toggle_voice())

        self.wake_btn = tk.Label(top, text="[ WAKE : OFF ]",
            font=info_font, fg=self.TEXT_DIM, bg=self.BG_DARK, cursor="hand2")
        self.wake_btn.place(x=right_x, y=38)
        self.wake_btn.bind("<Button-1>", lambda e: self._toggle_wake())

        self.vault_label = tk.Label(top,
            text=f"[ VAULT : {self._get_vault_name()} ]",
            font=info_font, fg=self.TEXT_SECONDARY, bg=self.BG_DARK, cursor="hand2")
        self.vault_label.place(x=right_x, y=58)
        self.vault_label.bind("<Button-1>", lambda e: self._show_vault_info())

    def _build_center_area(self):
        center = tk.Frame(self.root, bg=self.BG_DARK)
        center.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        center.columnconfigure(0, weight=1)
        center.rowconfigure(0, weight=1)

        self.holo_canvas = tk.Canvas(center, bg=self.BG_DARK, highlightthickness=0)
        self.holo_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        panel = tk.Frame(center, bg=self.PANEL_BG, highlightbackground=self.PANEL_BORDER,
                         highlightthickness=1, bd=0)
        panel.place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)

        inner = tk.Frame(panel, bg=self.BG_MED)
        inner.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)
        inner.columnconfigure(0, weight=1)
        inner.rowconfigure(0, weight=1)

        self.chat_display = tk.Text(
            inner, wrap="word", state="disabled",
            bg=self.BG_MED, fg=self.TEXT_PRIMARY,
            insertbackground=self.ACCENT,
            relief="flat", borderwidth=0,
            padx=20, pady=20,
            font=("Consolas", 11),
            spacing1=5, spacing2=2, spacing3=10,
            highlightthickness=0
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(inner, command=self.chat_display.yview,
            bg=self.BG_DARK, troughcolor=self.BG_MED,
            activebackground=self.ACCENT, width=8)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_display.configure(yscrollcommand=scrollbar.set)

        self.chat_display.tag_config("user", foreground=self.USER_COLOR,
            font=("Consolas", 11, "bold"))
        self.chat_display.tag_config("ruby", foreground=self.RUBY_COLOR,
            font=("Consolas", 11, "bold"))
        self.chat_display.tag_config("ruby_text", foreground=self.TEXT_PRIMARY)
        self.chat_display.tag_config("error", foreground=self.ERROR_COLOR)
        self.chat_display.tag_config("system", foreground=self.TEXT_DIM,
            font=("Consolas", 9))
        self.chat_display.tag_config("thinking", foreground="#006688",
            font=("Consolas", 9, "italic"))
        self.chat_display.tag_config("voice", foreground="#ffaa44",
            font=("Consolas", 9, "italic"))

    def _build_bottom_hud(self):
        bottom = tk.Frame(self.root, bg=self.BG_DARK, height=100)
        bottom.grid(row=2, column=0, sticky="ew", padx=0, pady=(0, 0))
        bottom.grid_propagate(False)

        input_area = tk.Frame(bottom, bg=self.BG_DARK)
        input_area.pack(fill="x", padx=20, pady=(10, 5))

        entry_font = font.Font(family="Consolas", size=12)
        input_row = tk.Frame(input_area, bg=self.BG_DARK)
        input_row.pack(fill="x")

        prompt_lbl = tk.Label(input_row, text=">>",
            font=font.Font(family="Consolas", size=14, weight="bold"),
            fg=self.ACCENT, bg=self.BG_DARK)
        prompt_lbl.pack(side="left", padx=(0, 8))

        self.input_entry = tk.Text(
            input_row, height=1, wrap="word",
            bg=self.BG_LIGHT, fg=self.TEXT_PRIMARY,
            insertbackground=self.ACCENT,
            relief="flat", borderwidth=0,
            padx=12, pady=8,
            font=entry_font,
            highlightthickness=1,
            highlightcolor=self.ACCENT,
            highlightbackground="#1a1a3a"
        )
        self.input_entry.pack(side="left", fill="x", expand=True)
        self.input_entry.bind("<Return>", self._on_enter)
        self.input_entry.bind("<Shift-Return>", lambda e: self.input_entry.insert("insert", "\n"))
        self.input_entry.focus_set()

        btn_font = font.Font(family="Consolas", size=10, weight="bold")

        can_hear = self.listener is not None
        self.mic_btn = tk.Label(
            input_row, text="[MIC]" if can_hear else "[NO-MIC]",
            font=btn_font, fg=self.TEXT_SECONDARY,
            bg=self.BG_LIGHT, cursor="hand2" if can_hear else "arrow",
            padx=10, pady=8
        )
        self.mic_btn.pack(side="left", padx=(6, 0))
        if can_hear:
            self.mic_btn.bind("<ButtonPress-1>", lambda e: self._start_listening_thread())
            self.mic_btn.bind("<ButtonRelease-1>", lambda e: None)
            self.root.bind("<Control-m>", lambda e: self._start_listening_thread())

        send_btn = tk.Label(
            input_row, text="SEND", font=btn_font,
            fg=self.BG_DARK, bg=self.ACCENT,
            padx=14, pady=8, cursor="hand2"
        )
        send_btn.pack(side="left", padx=(6, 0))
        send_btn.bind("<Button-1>", lambda e: self._send_message())

        hint_font = font.Font(family="Consolas", size=8)
        hint = tk.Label(bottom,
            text="[CTRL+M: MIC]  [ESC: EXIT]  [/HELP: COMMANDS]",
            font=hint_font, fg=self.TEXT_DIM, bg=self.BG_DARK, anchor="w")
        hint.pack(fill="x", padx=30, pady=(2, 5))

    def _bind_events(self):
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def _init_animations(self):
        self.scan_line = ScanningLine(1000)
        for _ in range(30):
            self.particles.append(Particle(1000, 720))

    def _start_animation(self):
        self._animate()

    def _animate(self):
        now = time.time() - self.anim_start
        dt = 0.03

        self.holo_canvas.delete("scanline")
        self.holo_canvas.delete("particle")
        self.holo_canvas.delete("ring")

        w = self.holo_canvas.winfo_width() or 1000
        h = self.holo_canvas.winfo_height() or 720

        self._draw_corner_indicators(w, h)
        self._draw_center_core(w, h, now)

        self.scan_line.width = w
        self.scan_line.update()
        self.scan_line.draw(self.holo_canvas)

        self.particles = [p for p in self.particles if p.update(dt)]
        while len(self.particles) < 30:
            self.particles.append(Particle(w, h))
        for p in self.particles:
            p.draw(self.holo_canvas)

        self.root.after(30, self._animate)

    def _draw_corner_indicators(self, w, h):
        c = self.holo_canvas
        size = 30
        gap = 15

        for x1, y1, x2, y2 in [
            (gap, gap + size, gap, gap),
            (gap, gap, gap + size, gap),
            (w - gap - size, gap, w - gap, gap),
            (w - gap, gap, w - gap, gap + size),
            (gap, h - gap - size, gap, h - gap),
            (gap, h - gap, gap + size, h - gap),
            (w - gap, h - gap - size, w - gap, h - gap),
            (w - gap - size, h - gap, w - gap, h - gap),
        ]:
            c.create_line(x1, y1, x2, y2, fill=self.ACCENT_DIM, width=1, tags="ring")

        mid_x = w // 2
        c.create_line(mid_x - 60, gap + 5, mid_x + 60, gap + 5, fill="#003355", width=1, tags="ring")
        c.create_line(mid_x, gap, mid_x, gap + 10, fill="#005588", width=1, tags="ring")

    def _draw_center_core(self, w, h, t):
        c = self.holo_canvas
        cx, cy = w - 120, 120

        for i in range(3):
            r = 40 + i * 18
            pulse = math.sin(t * 2 + i * 1.2) * 0.15 + 0.85
            c.create_oval(cx - r, cy - r, cx + r, cy + r,
                outline="#00d4ff", width=1, tags="ring")

        r = 18
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
            fill="#001828", outline=self.ACCENT, width=2, tags="ring")
        glow = math.sin(t * 3) * 10 + 20
        c.create_oval(cx - glow, cy - glow, cx + glow, cy + glow,
            fill="#000d18", outline="", tags="ring")
        c.create_text(cx, cy, text="R", font=("Segoe UI", 18, "bold"),
            fill=self.ACCENT, tags="ring")

    def _get_vault_name(self) -> str:
        from config.settings import settings
        p = settings.OBSIDIAN_VAULT_PATH
        return p.name if p.exists() else "NONE"

    def _toggle_voice(self):
        if not self.voice:
            self._add_message("system", "SYS",
                "[VOICE UNAVAILABLE] Install pyttsx3: pip install pyttsx3")
            return
        enabled = self.voice.toggle()
        self.voice_btn.config(
            text="[ VOICE : ON ]" if enabled else "[ VOICE : OFF ]",
            fg=self.ACCENT if enabled else self.TEXT_DIM
        )
        self._add_message("system", "SYS",
            f"[VOICE {'ACTIVE' if enabled else 'OFFLINE'}]")

    def _toggle_wake(self):
        self.wake_enabled = not self.wake_enabled
        if self.wake_enabled:
            if self.listener and self.listener.available:
                self.listener.start_continuous(self._on_heard, wake_word="ruby")
                status = "[WAKE ACTIVE] Listening for 'Ruby...'"
            else:
                self.wake_enabled = False
                status = "[WAKE FAILED] No microphone available"
        else:
            if self.listener:
                self.listener.stop()
            status = "[WAKE DEACTIVATED]"
        self.wake_btn.config(
            text="[ WAKE : ON ]" if self.wake_enabled else "[ WAKE : OFF ]",
            fg=self.ACCENT if self.wake_enabled else self.TEXT_DIM
        )
        self._add_message("system", "SYS", status)

    def _start_listening_thread(self):
        if self.mic_active or not self.listener:
            return
        self.mic_active = True
        self.mic_btn.config(fg=self.ERROR_COLOR, text="[MIC:ON]")
        self.status_label.config(text=">> LISTENING <<", fg=self.ERROR_COLOR)
        threading.Thread(target=self._listen_for_input, daemon=True).start()

    def _listen_for_input(self):
        text = self.listener.listen_once(timeout=8, phrase_limit=10)
        self.root.after(0, self._finish_listening, text)

    def _finish_listening(self, text):
        self.mic_active = False
        self.mic_btn.config(fg=self.TEXT_SECONDARY, text="[MIC]")
        self.status_label.config(text=">> SYSTEM ONLINE <<", fg=self.USER_COLOR)
        if text:
            self._add_message("voice", "V-IN", f"[HEARD] {text}")
            self.input_entry.delete("1.0", "end")
            self.input_entry.insert("1.0", text)
            self._send_message()

    def _on_heard(self, text: str, via_wake: bool = False):
        if via_wake:
            self.root.after(0, lambda: self._add_message("voice", "WAKE",
                f"[COMMAND] Ruby, {text}"))
            self.root.after(0, lambda: self._input_and_send(text))

    def _input_and_send(self, text: str):
        self.input_entry.delete("1.0", "end")
        self.input_entry.insert("1.0", text)
        self._send_message()

    def _show_welcome(self):
        from config.settings import settings
        v = settings.OBSIDIAN_VAULT_PATH
        voice_name = "OFFLINE"
        if self.voice and self.voice.enabled:
            try:
                voice_name = self.voice.get_voice_name()
            except Exception:
                voice_name = "ACTIVE"
        llm_status = self._detect_llm_backend()
        lines = [
            ">> RUBY AI ASSISTANT v1.0 <<",
            f">> {llm_status} <<",
            "",
            f"  Vault: {v.name if v.exists() else 'NOT FOUND'}",
            f"  Voice: {voice_name}",
            f"  Mic: {'READY (Ctrl+M)' if self.listener else 'UNAVAILABLE'}",
            "",
            ">> SYSTEM READY <<",
            ">> Type /help for available commands <<",
        ]
        self._add_message("system", "RUBY", "\n".join(lines))

    def _detect_llm_backend(self) -> str:
        try:
            from ruby.tools.llm import LLMProvider
            llm = LLMProvider()
            if llm.ready:
                return f"LLM BACKEND: {llm.model}"
        except Exception:
            pass
        return "CUSTOM NEURAL BRAIN - 100% LOCAL"

    def _add_message(self, msg_type, sender, text):
        self.chat_display.configure(state="normal")
        if msg_type == "user":
            self.chat_display.insert("end", f"\n[{sender}]\n", "user")
            self.chat_display.insert("end", f"{text}\n")
        elif msg_type == "ruby":
            self.chat_display.insert("end", f"\n[{sender}]\n", "ruby")
            self.chat_display.insert("end", f"{text}\n")
        elif msg_type == "system":
            self.chat_display.insert("end", f"\n{text}\n", "system")
        elif msg_type == "voice":
            self.chat_display.insert("end", f"\n{text}\n", "voice")
        elif msg_type == "error":
            self.chat_display.insert("end", f"\n[{sender}]\n", "error")
            self.chat_display.insert("end", f"{text}\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def _show_thinking(self):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", "\n[RUBY]\n", "ruby")
        self.thinking_start = self.chat_display.index("end-1c")
        self.chat_display.insert("end", ">> PROCESSING... <<\n", "thinking")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        self.status_label.configure(text=">> PROCESSING <<", fg=self.ACCENT_DIM)

    def _clear_thinking(self):
        self.chat_display.configure(state="normal")
        if self.thinking_start:
            self.chat_display.delete(self.thinking_start, "end")
            self.thinking_start = None
        self.chat_display.configure(state="disabled")
        self.status_label.configure(text=">> SYSTEM ONLINE <<", fg=self.USER_COLOR)

    def _on_enter(self, event):
        if not event.state & 0x1:
            self._send_message()
            return "break"

    def _send_message(self):
        text = self.input_entry.get("1.0", "end-1c").strip()
        if not text:
            return
        self.input_entry.delete("1.0", "end")
        self._add_message("user", "YOU", text)

        if text.startswith("/"):
            self._handle_command(text)
            return

        self._show_thinking()
        threading.Thread(target=self._get_response, args=(text,), daemon=True).start()

    def _speak_response(self, text):
        if self.voice and self.voice.enabled:
            self.voice.speak_async(text)

    def _get_response(self, text):
        try:
            if self.ruby:
                response = self.ruby.think(text)
            else:
                response = self._local_response(text)
            self.root.after(0, self._clear_thinking)
            self.root.after(50, lambda: self._add_message("ruby", "RUBY", response))
            self.root.after(100, lambda: self._speak_response(response))
        except Exception as e:
            self.root.after(0, self._clear_thinking)
            self.root.after(0, lambda: self._add_message("error", "SYS", str(e)))

    def _local_response(self, text):
        try:
            from ruby.brain import Brain
            self.ruby = Brain()
            return self.ruby.think(text)
        except ImportError:
            pass
        tl = text.lower()
        if "hello" in tl or "hi" in tl:
            return "Hey Boss. Ruby online. What do you need?"
        if "joke" in tl:
            return "Why did the AI cross the road? To optimize the path."
        if "time" in tl:
            return f"Current local time: {time.strftime('%H:%M:%S')}"
        if "name" in tl:
            return "I am Ruby. Custom neural network. No cloud. No APIs."
        return "Acknowledged. I am still learning. Continue."

    def _show_vault_info(self):
        from config.settings import settings
        p = settings.OBSIDIAN_VAULT_PATH
        if not p.exists():
            self._add_message("system", "VAULT", f"[ERROR] Vault not found: {p}")
            return
        folders = [d.name for d in p.iterdir() if d.is_dir() and not d.name.startswith('.')]
        note_count = len(list(p.rglob("*.md")))
        info = (
            f"[VAULT: {p.name}]\n"
            f"[PATH: {p}]\n"
            f"[NOTES: {note_count}]\n"
            f"[FOLDERS: {', '.join(folders[:6])}]"
        )
        self._add_message("system", "VAULT", info)

    def _handle_command(self, cmd):
        cmd = cmd.strip().lower()
        if cmd in ("/exit", "/quit"):
            self.root.destroy()
        elif cmd == "/help":
            v = "[VOICE]" if self.voice else ""
            w = "[WAKE]" if self.listener else ""
            self._add_message("system", "HELP",
                f"COMMANDS:\n"
                f"  /help     Show this\n"
                f"  /exit     Shutdown\n"
                f"  /reset    Reset session\n"
                f"  /voice    Toggle voice output {v}\n"
                f"  /wake     Toggle wake word {w}\n"
                f"  /mic      Activate microphone\n"
                f"  /vault    Obsidian vault status\n"
                f"  /status   System diagnostics\n"
                f"  /learn    Learning statistics\n"
                f"  /about    About this system\n"
                f"  /notes    List vault notes\n"
                f"  /read     Read a vault note\n\n"
                f"HOTKEYS:\n"
                f"  Ctrl+M    Push-to-talk\n"
                f"  Enter     Send message\n"
                f"  Esc       Exit")
        elif cmd == "/reset":
            if self.ruby:
                self.ruby.reset()
                self.ruby = None
            self.chat_display.configure(state="normal")
            self.chat_display.delete("1.0", "end")
            self.chat_display.configure(state="disabled")
            self._show_welcome()
        elif cmd == "/mic":
            if self.listener:
                self._start_listening_thread()
            else:
                self._add_message("error", "SYS", "[MIC OFFLINE]")
        elif cmd == "/wake":
            self._toggle_wake()
        elif cmd == "/status":
            s = ""
            llm_info = self._detect_llm_backend()
            if self.ruby:
                try:
                    st = self.ruby.get_stats()
                    s = f"\n  Conversations: {st.get('conversations', 0)}\n  Facts: {st.get('facts_learned', 0)}\n  Vocabulary: {st.get('vocabulary', 0)}"
                except Exception:
                    pass
            self._add_message("system", "STATUS",
                f"RUBY STATUS:\n"
                f"  Brain: {llm_info}{s}\n"
                f"  Voice: {'ACTIVE' if self.voice and self.voice.enabled else 'OFF'}\n"
                f"  Mic: {'READY' if self.listener else 'N/A'}\n"
                f"  Wake: {'ON' if self.wake_enabled else 'OFF'}\n"
                f"  Fallback: Custom Neural Net (numpy)")
        elif cmd == "/learn":
            if self.ruby:
                try:
                    st = self.ruby.get_stats()
                    self._add_message("system", "LEARN",
                        f"LEARNING REPORT:\n"
                        f"  Conversations logged: {st.get('conversations', 0)}\n"
                        f"  Facts extracted: {st.get('facts_learned', 0)}\n"
                        f"  User preferences: {st.get('user_prefs', 0)}\n"
                        f"  Vocabulary size: {st.get('vocabulary', 0)}\n"
                        f"  Word patterns: {st.get('ngrams', 0)}")
                except Exception as e:
                    self._add_message("system", "LEARN", f"[ERROR] {e}")
            else:
                self._add_message("system", "LEARN", "[NO DATA] Start chatting.")
        elif cmd == "/voice":
            self._toggle_voice()
        elif cmd == "/vault":
            self._show_vault_info()
        elif cmd.startswith("/notes"):
            p = cmd.split(" ", 1)
            self._list_vault_notes(p[1].strip() if len(p) > 1 else "")
        elif cmd.startswith("/read"):
            p = cmd.split(" ", 1)
            if len(p) > 1:
                self._read_vault_note(p[1].strip())
            else:
                self._add_message("error", "VAULT", "[USAGE] /read <path>")
        elif cmd == "/about":
            llm_info = self._detect_llm_backend()
            self._add_message("system", "ABOUT",
                "RUBY v1.0\n"
                f"  {llm_info}\n"
                "  Custom Neural Net (numpy) fallback\n"
                "  TF-IDF Knowledge Retrieval\n"
                "  Continuous Learning Engine\n"
                "  Markov Chain Generator\n"
                "  Web Knowledge Integration\n"
                "  Voice: Output + Input\n"
                "  Obsidian Vault Sync")
        else:
            self._add_message("error", "SYS", f"[UNKNOWN] '{cmd}' — try /help")

    def _list_vault_notes(self, folder=""):
        from config.settings import settings
        p = settings.OBSIDIAN_VAULT_PATH
        if folder:
            p = p / folder
        if not p.exists():
            self._add_message("error", "VAULT", f"[NOT FOUND] /{folder}")
            return
        notes = sorted(p.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)[:20]
        if not notes:
            self._add_message("system", "VAULT", f"[EMPTY] /{folder}")
            return
        lines = [f"[NOTES] /{folder or p.name}:"]
        for n in notes:
            rel = n.relative_to(settings.OBSIDIAN_VAULT_PATH)
            lines.append(f"  {rel}  ({n.stat().st_size}B)")
        self._add_message("system", "VAULT", "\n".join(lines))

    def _read_vault_note(self, note_path):
        from config.settings import settings
        p = settings.OBSIDIAN_VAULT_PATH / note_path
        if not p.exists() or p.suffix != ".md":
            self._add_message("error", "VAULT", f"[NOT FOUND] {note_path}")
            return
        self._add_message("system", f"NOTE: {p.stem}", p.read_text(encoding="utf-8")[:1500])

    def run(self):
        self.root.mainloop()
