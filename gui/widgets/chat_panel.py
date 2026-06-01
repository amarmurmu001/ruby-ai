import tkinter as tk
from ..theme import Theme


class ChatPanel:
    def __init__(self, parent):
        self.parent = parent
        self.thinking_mark = None

        self.frame = tk.Frame(parent, bg=Theme.BG_DARK)
        self.frame.grid(row=0, column=1, sticky="nsew")
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self._build()

    def _build(self):
        self.text = tk.Text(
            self.frame, wrap="word", state="disabled",
            bg=Theme.BG_DARK, fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.ACCENT,
            relief="flat", borderwidth=0,
            padx=20, pady=20,
            font=(Theme.FONT_FAMILY, Theme.FONT_SIZES["body"]),
            spacing1=6, spacing2=3, spacing3=10,
            highlightthickness=0,
        )
        self.text.grid(row=0, column=0, sticky="nsew")

        scrollbar = Theme.scrollbar(self.frame, command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scrollbar.set)

        self.text.tag_config("user", foreground=Theme.TEXT_SECONDARY,
                             font=(Theme.FONT_FAMILY, 11, "bold"))
        self.text.tag_config("ruby", foreground=Theme.ACCENT,
                             font=(Theme.FONT_FAMILY, 11, "bold"))
        self.text.tag_config("content", foreground=Theme.TEXT_PRIMARY)
        self.text.tag_config("error", foreground=Theme.ERROR)
        self.text.tag_config("system", foreground=Theme.TEXT_DIM,
                             font=(Theme.FONT_FAMILY, 10))
        self.text.tag_config("thinking", foreground=Theme.ACCENT_DIM,
                             font=(Theme.FONT_FAMILY, 12, "italic"))
        self.text.tag_config("voice", foreground=Theme.TEXT_DIM,
                             font=(Theme.FONT_FAMILY, 10, "italic"))

    def add(self, msg_type: str, sender: str, text: str):
        self.text.configure(state="normal")
        if msg_type == "user":
            self.text.insert("end", f"[{sender}]\n", "user")
            self.text.insert("end", f"{text}\n\n", "content")
        elif msg_type == "ruby":
            self.text.insert("end", f"[{sender}]\n", "ruby")
            self.text.insert("end", f"{text}\n\n", "content")
        elif msg_type == "system":
            self.text.insert("end", f"{text}\n\n", "system")
        elif msg_type == "voice":
            self.text.insert("end", f"{text}\n\n", "voice")
        elif msg_type == "error":
            self.text.insert("end", f"[{sender} error]\n", "error")
            self.text.insert("end", f"{text}\n\n", "content")
        self.text.see("end")
        self.text.configure(state="disabled")

    def show_thinking(self):
        self.text.configure(state="normal")
        self.text.insert("end", "[ruby]\n", "ruby")
        self.thinking_mark = self.text.index("end-1c")
        self.text.insert("end", "> processing... <\n\n", "thinking")
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear_thinking(self):
        self.text.configure(state="normal")
        if self.thinking_mark:
            self.text.delete(self.thinking_mark, "end")
            self.thinking_mark = None
        self.text.configure(state="disabled")

    def clear_all(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def welcome(self, backend: str, vault: str, voice: str, mic: bool):
        lines = [
            "[system ready]",
            f"[*] brain: {backend}",
            f"[*] vault: {vault}",
            f"[*] voice: {voice}",
            f"[*] mic: {'rdy' if mic else 'n/a'}",
            "[/help for commands]",
        ]
        self.add("system", "SYS", "\n".join(lines))
