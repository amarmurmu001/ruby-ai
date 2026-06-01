import tkinter as tk
from ..theme import Theme


class InfoPanel:
    WIDTH = 200

    def __init__(self, parent, controller):
        self.controller = controller
        self.visible = True

        self.frame = tk.Frame(parent, bg=Theme.BG_PANEL, width=self.WIDTH)
        self.frame.grid(row=0, column=2, sticky="ns")
        self.frame.grid_propagate(False)

        self._actions = []
        self._stat_labels = {}
        self._build()

    def _build(self):
        f = (Theme.FONT_FAMILY, 9)

        tk.Label(self.frame, text="[ system ]", font=(Theme.FONT_FAMILY, 10),
                 fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, anchor="w",
                 padx=14).pack(fill="x", pady=(14, 4))

        sf = tk.Frame(self.frame, bg=Theme.BG_PANEL)
        sf.pack(fill="x", padx=14, pady=2)

        for key, label in [("tools", "tools"), ("convos", "convos"), ("facts", "facts")]:
            row = tk.Frame(sf, bg=Theme.BG_PANEL)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, font=f,
                     fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, anchor="w"
                     ).pack(side="left")
            val = tk.Label(row, text="--", font=(Theme.FONT_FAMILY, 9, "bold"),
                           fg=Theme.TEXT_SECONDARY, bg=Theme.BG_PANEL, anchor="e")
            val.pack(side="right")
            self._stat_labels[key] = val

        tk.Frame(sf, bg=Theme.HAIRLINE, height=1).pack(fill="x", pady=6)

        tk.Label(sf, text="[ recent ]", font=(Theme.FONT_FAMILY, 10),
                 fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, anchor="w"
                 ).pack(fill="x", pady=(0, 4))

        for _ in range(6):
            lbl = tk.Label(sf, text="", font=f,
                           fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, anchor="w")
            lbl.pack(fill="x")
            self._actions.append(lbl)

    def refresh(self):
        if not self.controller.brain:
            return
        try:
            stats = self.controller.brain.get_stats()
            self._stat_labels["tools"].config(text=str(stats.get("tools", 0)))
            self._stat_labels["convos"].config(text=str(stats.get("conversations", 0)))
            self._stat_labels["facts"].config(text=str(stats.get("facts_learned", 0)))
        except Exception:
            pass

    def log_action(self, action: str):
        for i in range(len(self._actions) - 1, 0, -1):
            prev = self._actions[i - 1].cget("text")
            self._actions[i].config(text=prev)
        self._actions[0].config(text=f"> {action}", fg=Theme.TEXT_SECONDARY)

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            self.frame.grid()
        else:
            self.frame.grid_remove()
        return self.visible

    def toggle_on(self):
        if not self.visible:
            self.visible = True
            self.frame.grid()
        return self.visible

    def toggle_off(self):
        if self.visible:
            self.visible = False
            self.frame.grid_remove()
        return self.visible
