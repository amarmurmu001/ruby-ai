import re
import tkinter as tk
from ..theme import Theme


class ChatPanel:
    def __init__(self, parent):
        self.parent = parent
        self.thinking_mark = None
        self._auto_scroll = True
        self._search_bar = None
        self._search_var = None
        self._search_matches = []
        self._search_index = 0

        self.frame = tk.Frame(parent, bg=Theme.BG_DARK)
        self.frame.grid(row=0, column=1, sticky="nsew")
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        self._build()

    def _build(self):
        search_frame = tk.Frame(self.frame, bg=Theme.BG_MED, height=28)
        search_frame.grid(row=0, column=0, sticky="ew", columnspan=2)
        search_frame.grid_propagate(False)
        search_frame.grid_remove()
        self._search_frame = search_frame

        f = (Theme.FONT_FAMILY, 9)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *a: self._do_search())
        entry = tk.Entry(search_frame, textvariable=self._search_var,
                         font=f, bg=Theme.BG_LIGHT, fg=Theme.TEXT_PRIMARY,
                         insertbackground=Theme.ACCENT,
                         relief="flat", borderwidth=0,
                         highlightthickness=0)
        entry.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=3)
        entry.bind("<Return>", lambda e: self._search_next())
        entry.bind("<Escape>", lambda e: self._hide_search())

        self._search_count = tk.Label(search_frame, text="", font=f,
                                       fg=Theme.TEXT_DIM, bg=Theme.BG_MED)
        self._search_count.pack(side="left", padx=4)

        nav_f = (Theme.FONT_FAMILY, 9, "bold")
        for cmd, lbl_text in [("prev", "▲"), ("next", "▼"), ("close", "✕")]:
            btn = tk.Label(search_frame, text=lbl_text, font=nav_f,
                           fg=Theme.TEXT_DIM, bg=Theme.BG_MED, cursor="hand2",
                           padx=4)
            btn.pack(side="left")
            if cmd == "prev":
                btn.bind("<Button-1>", lambda e: self._search_prev())
            elif cmd == "next":
                btn.bind("<Button-1>", lambda e: self._search_next())
            else:
                btn.bind("<Button-1>", lambda e: self._hide_search())
            btn.bind("<Enter>", lambda e: btn.config(fg=Theme.ACCENT))
            btn.bind("<Leave>", lambda e: btn.config(fg=Theme.TEXT_DIM))

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
        self.text.grid(row=1, column=0, sticky="nsew")

        scrollbar = Theme.scrollbar(self.frame, command=self.text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.text.configure(yscrollcommand=self._on_scroll)

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

        self.text.tag_config("bold", font=(Theme.FONT_FAMILY, Theme.FONT_SIZES["body"], "bold"))
        self.text.tag_config("code", font=(Theme.FONT_MONO, Theme.FONT_SIZES["caption"]),
                             foreground=Theme.WARNING, spacing1=2, spacing2=2, spacing3=2)
        self.text.tag_config("codeblock", font=(Theme.FONT_MONO, Theme.FONT_SIZES["caption"]),
                             foreground=Theme.TEXT_SECONDARY, spacing1=4, spacing2=4, spacing3=4,
                             lmargin1=20, lmargin2=20)
        self.text.tag_config("search_hit", background="#555500", foreground=Theme.TEXT_PRIMARY)
        self.text.tag_config("search_current", background="#887700", foreground=Theme.TEXT_PRIMARY)

    def _on_scroll(self, *args):
        if args and args[0] == "moveto":
            frac = float(args[1])
            self._auto_scroll = frac >= 0.99
        if self._search_bar is not None:
            self.text.configure(yscrollcommand=self._on_scroll)

    def show_search(self):
        self._search_frame.grid()
        self._search_frame.winfo_children()[0].focus_set()
        self._do_search()

    def _hide_search(self):
        self._search_frame.grid_remove()
        self.text.tag_remove("search_hit", "1.0", "end")
        self.text.tag_remove("search_current", "1.0", "end")
        self.text.focus_set()

    def _do_search(self):
        query = self._search_var.get().strip().lower()
        self.text.tag_remove("search_hit", "1.0", "end")
        self.text.tag_remove("search_current", "1.0", "end")
        self._search_matches = []
        self._search_index = 0

        if not query:
            self._search_count.config(text="")
            return

        pos = "1.0"
        while True:
            pos = self.text.search(query, pos, nocase=True, stopindex="end")
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self._search_matches.append(pos)
            self.text.tag_add("search_hit", pos, end)
            pos = end

        if self._search_matches:
            self._search_index = 0
            self._highlight_current()
            self._search_count.config(text=f"{1}/{len(self._search_matches)}")
        else:
            self._search_count.config(text="0/0")

    def _highlight_current(self):
        self.text.tag_remove("search_current", "1.0", "end")
        if not self._search_matches:
            return
        pos = self._search_matches[self._search_index]
        end = f"{pos}+{len(self._search_var.get())}c"
        self.text.tag_add("search_current", pos, end)
        self.text.see(pos)

    def _search_next(self):
        if not self._search_matches:
            return
        self._search_index = (self._search_index + 1) % len(self._search_matches)
        self._highlight_current()
        self._search_count.config(text=f"{self._search_index + 1}/{len(self._search_matches)}")

    def _search_prev(self):
        if not self._search_matches:
            return
        self._search_index = (self._search_index - 1) % len(self._search_matches)
        self._highlight_current()
        self._search_count.config(text=f"{self._search_index + 1}/{len(self._search_matches)}")

    def add(self, msg_type: str, sender: str, text: str):
        self.text.configure(state="normal")
        if msg_type == "user":
            self.text.insert("end", f"[{sender}]\n", "user")
            self._insert_markdown(text)
            self.text.insert("end", "\n")
        elif msg_type == "ruby":
            self.text.insert("end", f"[{sender}]\n", "ruby")
            self._insert_markdown(text)
            self.text.insert("end", "\n")
        elif msg_type == "system":
            self.text.insert("end", f"{text}\n\n", "system")
        elif msg_type == "voice":
            self.text.insert("end", f"{text}\n\n", "voice")
        elif msg_type == "error":
            self.text.insert("end", f"[{sender} error]\n", "error")
            self._insert_markdown(text)
            self.text.insert("end", "\n")
        if self._auto_scroll:
            self.text.see("end")
        self.text.configure(state="disabled")

    def _insert_markdown(self, text: str):
        pos = 0
        while pos < len(text):
            codeblock = re.search(r"```(\w*)\n(.*?)```", text[pos:], re.DOTALL)
            if codeblock:
                before = text[pos:pos + codeblock.start()]
                if before:
                    self._insert_inline(before)
                lang = codeblock.group(1)
                code = codeblock.group(2).rstrip()
                self.text.insert("end", f"[code: {lang or 'text'}]\n")
                self.text.insert("end", code + "\n", "codeblock")
                self.text.insert("end", "[/code]\n")
                pos += codeblock.end()
            else:
                self._insert_inline(text[pos:])
                break

    def _insert_inline(self, text: str):
        parts = re.split(r"(\*\*.*?\*\*|`[^`]+`)", text)
        for p in parts:
            if p.startswith("**") and p.endswith("**"):
                self.text.insert("end", p[2:-2], "bold")
            elif p.startswith("`") and p.endswith("`"):
                self.text.insert("end", p[1:-1], "code")
            else:
                self.text.insert("end", p)

    def show_thinking(self):
        self.text.configure(state="normal")
        self.text.insert("end", "[ruby]\n", "ruby")
        self.thinking_mark = self.text.index("end-1c")
        self.text.insert("end", "> processing... <\n\n", "thinking")
        if self._auto_scroll:
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
        self._search_matches = []
        self._search_index = 0
        self._auto_scroll = True
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
