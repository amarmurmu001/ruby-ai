import math
import tkinter as tk
from ..theme import Theme


class WaveVisualizer:
    def __init__(self, parent):
        self.amplitude = 3.0
        self.target_amplitude = 3.0
        self.phase = 0.0

        self.frame = tk.Frame(parent, bg=Theme.BG_DARK, height=80)
        self.frame.grid(row=0, column=0, sticky="ew")
        self.frame.grid_propagate(False)

        self.canvas = tk.Canvas(self.frame, bg=Theme.BG_DARK,
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def update(self, dt: float, is_active: bool):
        self.phase += dt * 4.0
        self.target_amplitude = 40.0 if is_active else 3.0
        self.amplitude += (self.target_amplitude - self.amplitude) * 0.08

    def draw(self):
        self.canvas.delete("wave")
        w = self.canvas.winfo_width() or 1000
        h = self.canvas.winfo_height() or 80
        mid_y = h / 2

        colors = ["#1a1a1a", "#333333", "#555555"]
        for i, color in enumerate(colors):
            pts = []
            freq = 0.02 + (i * 0.006)
            speed = self.phase * (1.0 + i * 0.2)

            for x in range(0, w + 4, 4):
                y = math.sin(x * freq + speed) * self.amplitude
                y += math.sin(x * freq * 0.5 - speed) * (self.amplitude * 0.3)
                taper = math.sin((x / w) * math.pi) ** 2
                pts.append((x, mid_y - y * taper + i * 1.5))

            for x in range(w, -1, -4):
                y = math.sin(x * freq + speed) * self.amplitude
                y += math.sin(x * freq * 0.5 - speed) * (self.amplitude * 0.3)
                taper = math.sin((x / w) * math.pi) ** 2
                pts.append((x, mid_y + y * taper - i * 1.5))

            flat = [v for p in pts for v in p]
            self.canvas.create_polygon(*flat, fill=color, outline="", tags="wave")
