import time
import tkinter as tk
from ..theme import Theme


class StatusBar:
    HEIGHT = 24

    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = tk.Frame(parent, bg=Theme.BG_MED, height=self.HEIGHT)
        self.frame.grid(row=0, column=0, sticky="ew")
        self.frame.grid_propagate(False)

        self._labels = []
        self._build()

    def _build(self):
        items = tk.Frame(self.frame, bg=Theme.BG_MED)
        items.pack(fill="x", padx=12, pady=2)

        f = (Theme.FONT_FAMILY, 9)
        dim = {"bg": Theme.BG_MED, "fg": Theme.TEXT_DIM, "font": f}

        self._dot = tk.Label(items, text="[*]", font=f,
                             fg=Theme.STATUS_ON, bg=Theme.BG_MED)
        self._dot.pack(side="left", padx=(0, 6))
        self._labels.append(("status", self._dot))

        for key, default, editable in [
            ("brain", "brain: --", True),
            ("vault", "vault: --", True),
            ("voice", "voice: --", True),
            ("mic", "mic: --", True),
            ("clock", "", False),
        ]:
            tk.Label(items, text="|", **dim).pack(side="left", padx=5)
            lbl = tk.Label(items, text=default, **dim)
            lbl.pack(side="left")
            self._labels.append((key, lbl, editable))

        self._update_clock()

    def refresh(self):
        for entry in self._labels:
            key = entry[0]
            widget = entry[1]
            editable = entry[2] if len(entry) > 2 else False
            if not editable:
                continue
            if key == "brain":
                widget.config(text=f"brain: {self.controller.backend_name}")
            elif key == "vault":
                try:
                    from config.settings import settings
                    widget.config(text=f"vault: {settings.OBSIDIAN_VAULT_PATH.name}")
                except Exception:
                    widget.config(text="vault: --")
            elif key == "voice":
                widget.config(text="voice: on" if self.controller.has_voice else "voice: off")
            elif key == "mic":
                widget.config(text="mic: rdy" if self.controller.has_mic else "mic: n/a")

    def _update_clock(self):
        now = time.strftime("%H:%M")
        for entry in self._labels:
            if entry[0] == "clock":
                entry[1].config(text=now)
                break
        self.frame.after(5000, self._update_clock)
