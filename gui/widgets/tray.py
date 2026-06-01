import tkinter as tk
from ..theme import Theme


class SystemTray:
    def __init__(self, root):
        self.root = root
        self._tray_icon = None

    def setup(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            return False

        img = Image.new("RGB", (16, 16), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle((2, 2, 13, 13), outline="#ffffff")

        menu = pystray.Menu(
            pystray.MenuItem("Show Ruby", self._show_window),
            pystray.MenuItem("Quit", self._quit),
        )

        self._tray_icon = pystray.Icon("ruby", img, "Ruby", menu)
        return True

    def _show_window(self):
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)

    def _quit(self):
        self.root.after(0, self.root.destroy)

    def run(self):
        if self._tray_icon:
            import threading
            threading.Thread(target=self._tray_icon.run, daemon=True).start()

    def stop(self):
        if self._tray_icon:
            self._tray_icon.stop()
