import tkinter as tk
from ..theme import Theme


class Sidebar:
    WIDTH = 200

    def __init__(self, parent, controller):
        self.controller = controller
        self.visible = True

        self.frame = tk.Frame(parent, bg=Theme.BG_PANEL, width=self.WIDTH)
        self.frame.grid(row=0, column=0, sticky="ns")
        self.frame.grid_propagate(False)

        self._content_label = None
        self._build()

    def _build(self):
        f = (Theme.FONT_FAMILY, 10)

        sections = [
            ("[+] chats", self._on_chats),
            ("[+] tools", self._on_tools),
            ("[+] files", self._on_files),
            ("[+] memory", self._on_memory),
        ]

        for text, cmd in sections:
            lbl = tk.Label(self.frame, text=text, font=f,
                           fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL,
                           anchor="w", padx=14, pady=4, cursor="hand2")
            lbl.pack(fill="x")
            lbl.bind("<Button-1>", lambda e, c=cmd: c())
            lbl.bind("<Enter>", lambda e: e.widget.config(fg=Theme.ACCENT))
            lbl.bind("<Leave>", lambda e: e.widget.config(fg=Theme.TEXT_DIM))

        tk.Frame(self.frame, bg=Theme.HAIRLINE, height=1).pack(fill="x", padx=14, pady=4)

        self._content_label = tk.Label(self.frame, text="",
            font=(Theme.FONT_FAMILY, 9), fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL,
            anchor="nw", justify="left", padx=14, pady=4)
        self._content_label.pack(fill="both", expand=True)

    def _on_chats(self):
        self._content_label.config(text="conversation history\n\n(coming soon)")

    def _on_tools(self):
        names = []
        if self.controller.brain and self.controller.brain.registry:
            names = self.controller.brain.registry.list_names()
        text = "\n".join(f"  {n}" for n in names[:12]) if names else "(empty)"
        if len(names) > 12:
            text += f"\n  ... +{len(names)-12}"
        self._content_label.config(text=f"tools [{len(names)}]\n{text}")

    def _on_files(self):
        self._content_label.config(text="file browser\n\n(coming soon)")

    def _on_memory(self):
        self._content_label.config(text="memory browser\n\n(coming soon)")

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
