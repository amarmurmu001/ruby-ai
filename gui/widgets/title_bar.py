import ctypes
import tkinter as tk
from ..theme import Theme


class TitleBar:
    HEIGHT = 28

    def __init__(self, parent, on_close=None, on_minimize=None, on_maximize=None):
        self.parent = parent
        self.on_close = on_close
        self.on_minimize = on_minimize
        self.on_maximize = on_maximize
        self._drag_data = {"x": 0, "y": 0}

        self.frame = tk.Frame(parent, bg=Theme.BG_TITLE, height=self.HEIGHT)
        self.frame.grid(row=0, column=0, sticky="ew")
        self.frame.grid_propagate(False)

        self._build()
        self._bind_drag()

    def _build(self):
        f = (Theme.FONT_FAMILY, 10)

        lbl = tk.Label(self.frame, text="[ RUBY ]", font=f,
                       fg=Theme.TEXT_DIM, bg=Theme.BG_TITLE)
        lbl.pack(side="left", padx=10)

        btn_frame = tk.Frame(self.frame, bg=Theme.BG_TITLE)
        btn_frame.pack(side="right")

        for text, cmd in [
            ("[—]", self._on_minimize),
            ("[□]", self._on_maximize),
            ("[✕]", self._on_close),
        ]:
            b = tk.Label(btn_frame, text=text, font=f,
                         fg=Theme.TEXT_DIM, bg=Theme.BG_TITLE,
                         padx=6, cursor="hand2")
            b.pack(side="left")
            b.bind("<Button-1>", lambda e, c=cmd: c() if c else None)
            b.bind("<Enter>", lambda e, t=text: e.widget.config(
                fg=Theme.ERROR if "✕" in t else Theme.ACCENT))
            b.bind("<Leave>", lambda e: e.widget.config(fg=Theme.TEXT_DIM))

    def _on_minimize(self):
        if self.on_minimize:
            self.on_minimize()
        else:
            self.parent.iconify()

    def _on_maximize(self):
        if self.on_maximize:
            self.on_maximize()
        else:
            root = self.parent.winfo_toplevel()
            if root.state() == "zoomed":
                root.state("normal")
            else:
                root.state("zoomed")

    def _on_close(self):
        if self.on_close:
            self.on_close()
        else:
            self.parent.winfo_toplevel().destroy()

    def _bind_drag(self):
        def start(e):
            self._drag_data["x"] = e.x_root
            self._drag_data["y"] = e.y_root

        def move(e):
            dx = e.x_root - self._drag_data["x"]
            dy = e.y_root - self._drag_data["y"]
            root = self.parent.winfo_toplevel()
            x = root.winfo_x() + dx
            y = root.winfo_y() + dy
            root.geometry(f"+{int(x)}+{int(y)}")
            self._drag_data["x"] = e.x_root
            self._drag_data["y"] = e.y_root

        self.frame.bind("<ButtonPress-1>", start)
        self.frame.bind("<B1-Motion>", move)
        for child in self.frame.winfo_children():
            child.bind("<ButtonPress-1>", start)
            child.bind("<B1-Motion>", move)
