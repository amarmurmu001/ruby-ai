import tkinter as tk
from ..theme import Theme


class SettingsPanel:
    def __init__(self, parent, controller):
        self.controller = controller
        self.visible = False

        self.overlay = tk.Frame(parent, bg="#000000")
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay.lower()

        content = tk.Frame(self.overlay, bg=Theme.BG_MED)
        content.place(relx=0.5, rely=0.5, anchor="center",
                      width=400, height=400)

        self._build(content)

    def _build(self, parent):
        f = (Theme.FONT_FAMILY, 11)
        bf = (Theme.FONT_FAMILY, 10, "bold")
        cf = (Theme.FONT_FAMILY, 9)

        tk.Label(parent, text="[ settings ]", font=(Theme.FONT_FAMILY, 14, "bold"),
                 fg=Theme.ACCENT, bg=Theme.BG_MED).pack(pady=(20, 10))

        tk.Frame(parent, bg=Theme.HAIRLINE, height=1).pack(fill="x", padx=20)

        sections_frame = tk.Frame(parent, bg=Theme.BG_MED)
        sections_frame.pack(fill="both", expand=True, padx=20, pady=10)

        def add_row(label, value_widget):
            row = tk.Frame(sections_frame, bg=Theme.BG_MED)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=f,
                     fg=Theme.TEXT_DIM, bg=Theme.BG_MED, anchor="w",
                     width=12).pack(side="left")
            value_widget.pack(side="right", fill="x", expand=True)

        # Brain backend
        backend = self.controller.backend_name
        lbl = tk.Label(sections_frame, text=backend, font=cf,
                       fg=Theme.TEXT_SECONDARY, bg=Theme.BG_MED, anchor="w")
        add_row("brain", lbl)

        # Voice toggle
        voice_var = tk.BooleanVar(value=self.controller.has_voice)
        voice_btn = tk.Checkbutton(sections_frame, text="voice output",
                                   variable=voice_var, font=f,
                                   fg=Theme.TEXT_DIM, bg=Theme.BG_MED,
                                   activebackground=Theme.BG_MED,
                                   selectcolor=Theme.BG_MED,
                                   command=lambda: self._toggle_voice())
        tk.Label(sections_frame, text="voice", font=f,
                 fg=Theme.TEXT_DIM, bg=Theme.BG_MED, anchor="w",
                 width=12).pack(anchor="w", pady=3)
        voice_btn.pack(anchor="w", padx=(100, 0))

        # Vault path
        try:
            from config.settings import settings
            vault_path = str(settings.OBSIDIAN_VAULT_PATH)
        except Exception:
            vault_path = "(not set)"
        lbl = tk.Label(sections_frame, text=vault_path, font=cf,
                       fg=Theme.TEXT_SECONDARY, bg=Theme.BG_MED, anchor="w",
                       wraplength=250)
        add_row("vault", lbl)

        # Mic status
        mic_status = "ready" if self.controller.has_mic else "unavailable"
        lbl = tk.Label(sections_frame, text=mic_status, font=cf,
                       fg=Theme.STATUS_ON if self.controller.has_mic else Theme.TEXT_DIM,
                       bg=Theme.BG_MED, anchor="w")
        add_row("mic", lbl)

        # Tools count
        tools_count = 0
        if self.controller.brain and self.controller.brain.registry:
            tools_count = len(self.controller.brain.registry.list_names())
        lbl = tk.Label(sections_frame, text=str(tools_count), font=cf,
                       fg=Theme.TEXT_SECONDARY, bg=Theme.BG_MED, anchor="w")
        add_row("tools", lbl)

        tk.Frame(parent, bg=Theme.HAIRLINE, height=1).pack(fill="x", padx=20)

        close_btn = tk.Label(parent, text="[ close ]",
                             font=bf, fg=Theme.TEXT_DIM, bg=Theme.BG_MED,
                             cursor="hand2")
        close_btn.pack(pady=(10, 20))
        close_btn.bind("<Button-1>", lambda e: self.hide())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=Theme.ACCENT))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=Theme.TEXT_DIM))

    def _toggle_voice(self):
        if self.controller.voice:
            self.controller.voice.toggle()

    def show(self):
        self.visible = True
        self.overlay.lift()

    def hide(self):
        self.visible = False
        self.overlay.lower()

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()
        return self.visible
