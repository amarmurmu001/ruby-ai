import tkinter as tk


class Theme:
    BG_DARK = "#0a0a0a"
    BG_MED = "#111111"
    BG_LIGHT = "#1a1a1a"
    BG_PANEL = "#141414"
    BG_TITLE = "#1a1a1a"
    ACCENT = "#e0e0e0"
    ACCENT_DIM = "#666666"
    STATUS_ON = "#00d466"
    STATUS_OFF = "#444444"
    TEXT_PRIMARY = "#e0e0e0"
    TEXT_SECONDARY = "#888888"
    TEXT_DIM = "#555555"
    ERROR = "#ff3b30"
    WARNING = "#ff9f0a"
    INFO = "#007aff"
    SUCCESS = "#30d158"
    HAIRLINE = "#222222"
    SURFACE_DARK = "#1a1a1a"

    FONT_FAMILY = "Consolas"
    FONT_MONO = "Consolas"

    FONT_SIZES = {
        "title": 14,
        "hud": 11,
        "body": 13,
        "caption": 10,
        "input": 12,
        "btn": 11,
    }

    @classmethod
    def label(cls, parent, text="", size="body", weight="normal", color=None, **kwargs):
        kwargs.setdefault("fg", color or cls.TEXT_PRIMARY)
        kwargs.setdefault("bg", cls.BG_DARK)
        kwargs.setdefault("font", (cls.FONT_FAMILY, cls.FONT_SIZES[size], weight))
        return tk.Label(parent, text=text, **kwargs)

    @classmethod
    def canvas(cls, parent, **kwargs):
        kwargs.setdefault("bg", cls.BG_DARK)
        kwargs.setdefault("highlightthickness", 0)
        return tk.Canvas(parent, **kwargs)

    @classmethod
    def frame(cls, parent, bg=None, **kwargs):
        kwargs.setdefault("bg", bg or cls.BG_DARK)
        return tk.Frame(parent, **kwargs)

    @classmethod
    def text_widget(cls, parent, **kwargs):
        kwargs.setdefault("bg", cls.BG_DARK)
        kwargs.setdefault("fg", cls.TEXT_PRIMARY)
        kwargs.setdefault("insertbackground", cls.ACCENT)
        kwargs.setdefault("relief", "flat")
        kwargs.setdefault("borderwidth", 0)
        kwargs.setdefault("font", (cls.FONT_FAMILY, cls.FONT_SIZES["body"]))
        kwargs.setdefault("highlightthickness", 0)
        return tk.Text(parent, **kwargs)

    @classmethod
    def scrollbar(cls, parent, **kwargs):
        kwargs.setdefault("bg", cls.BG_DARK)
        kwargs.setdefault("troughcolor", cls.BG_DARK)
        kwargs.setdefault("activebackground", cls.TEXT_DIM)
        kwargs.setdefault("width", 8)
        kwargs.setdefault("relief", "flat")
        kwargs.setdefault("borderwidth", 0)
        return tk.Scrollbar(parent, **kwargs)
