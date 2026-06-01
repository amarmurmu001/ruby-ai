import tkinter as tk
from ..theme import Theme


class InputBar:
    HEIGHT = 60

    def __init__(self, parent, on_send, on_mic_press, on_mic_release):
        self.on_send = on_send
        self.on_mic_press = on_mic_press
        self.on_mic_release = on_mic_release

        self.frame = tk.Frame(parent, bg=Theme.BG_DARK, height=self.HEIGHT)
        self.frame.grid(row=0, column=0, sticky="ew")
        self.frame.grid_propagate(False)

        self._build()

    def _build(self):
        f = (Theme.FONT_FAMILY, Theme.FONT_SIZES["input"])
        btn_f = (Theme.FONT_FAMILY, Theme.FONT_SIZES["btn"])

        outer = tk.Frame(self.frame, bg=Theme.BG_LIGHT)
        outer.pack(fill="x", padx=30, pady=(0, 14), ipady=3, ipadx=3)

        self.entry = tk.Text(
            outer, height=1, wrap="word",
            bg=Theme.BG_LIGHT, fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.ACCENT,
            relief="flat", borderwidth=0,
            padx=12, pady=8,
            font=f,
            highlightthickness=0,
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Shift-Return>", lambda e: self.entry.insert("insert", "\n"))
        self.entry.focus_set()

        self.mic_btn = tk.Label(outer, text="<mic>",
            font=btn_f, fg=Theme.TEXT_DIM,
            bg=Theme.BG_LIGHT, cursor="hand2",
            padx=10, pady=4)
        self.mic_btn.pack(side="right")
        self.mic_btn.bind("<ButtonPress-1>", lambda e: self.on_mic_press() if self.on_mic_press else None)
        self.mic_btn.bind("<ButtonRelease-1>", lambda e: self.on_mic_release() if self.on_mic_release else None)

    def _on_enter(self, event):
        if not event.state & 0x1:
            self._send()
            return "break"

    def _send(self):
        text = self.entry.get("1.0", "end-1c").strip()
        if text:
            self.entry.delete("1.0", "end")
            self.on_send(text)

    def get_text(self) -> str:
        return self.entry.get("1.0", "end-1c").strip()

    def set_text(self, text: str):
        self.entry.delete("1.0", "end")
        self.entry.insert("1.0", text)

    def clear(self):
        self.entry.delete("1.0", "end")

    def focus(self):
        self.entry.focus_set()
