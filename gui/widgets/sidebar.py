import tkinter as tk
import tkinter.ttk as ttk
from pathlib import Path
from ..theme import Theme


class Sidebar:
    WIDTH = 220

    def __init__(self, parent, controller, on_switch_conv=None):
        self.controller = controller
        self.on_switch_conv = on_switch_conv
        self.visible = True
        self._current_section = "chats"

        self.frame = tk.Frame(parent, bg=Theme.BG_PANEL, width=self.WIDTH)
        self.frame.grid(row=0, column=0, sticky="ns")
        self.frame.grid_propagate(False)

        self._content_frame = None
        self._build()

    def _build(self):
        f = (Theme.FONT_FAMILY, 10)

        for text, cmd in [
            ("[+] chats", lambda: self._show_section("chats")),
            ("[+] tools", lambda: self._show_section("tools")),
            ("[+] files", lambda: self._show_section("files")),
            ("[+] memory", lambda: self._show_section("memory")),
        ]:
            lbl = tk.Label(self.frame, text=text, font=f,
                           fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL,
                           anchor="w", padx=14, pady=4, cursor="hand2")
            lbl.pack(fill="x")
            lbl.bind("<Button-1>", lambda e, c=cmd: c())
            lbl.bind("<Enter>", lambda e: e.widget.config(fg=Theme.ACCENT))
            lbl.bind("<Leave>", lambda e: e.widget.config(fg=Theme.TEXT_DIM))

        tk.Frame(self.frame, bg=Theme.HAIRLINE, height=1).pack(fill="x", padx=14, pady=4)

        self._content_frame = tk.Frame(self.frame, bg=Theme.BG_PANEL)
        self._content_frame.pack(fill="both", expand=True, padx=10, pady=2)

        self._show_section("chats")

    def _show_section(self, section: str):
        self._current_section = section
        for w in self._content_frame.winfo_children():
            w.destroy()

        if section == "chats":
            self._draw_chats()
        elif section == "tools":
            self._draw_tools()
        elif section == "files":
            self._draw_files()
        elif section == "memory":
            self._draw_memory()

    def _draw_chats(self):
        f = (Theme.FONT_FAMILY, 9)
        bf = (Theme.FONT_FAMILY, 9, "bold")

        tk.Label(self._content_frame, text="conversations", font=bf,
                 fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, anchor="w"
                 ).pack(fill="x", pady=(0, 4))

        convos = self.controller.brain.get_conversations() if self.controller.brain else []
        if not convos:
            tk.Label(self._content_frame, text="(none)", font=f,
                     fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, anchor="w"
                     ).pack(fill="x")
            return

        for c in convos[:20]:
            row = tk.Frame(self._content_frame, bg=Theme.BG_PANEL)
            row.pack(fill="x", pady=1)

            marker = "*" if c["active"] else " "
            title = c["title"][:25] + ("..." if len(c["title"]) > 25 else "")
            lbl = tk.Label(row, text=f"[{marker}] {title}", font=f,
                           fg=Theme.ACCENT if c["active"] else Theme.TEXT_DIM,
                           bg=Theme.BG_PANEL, anchor="w", cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True)
            if not c["active"]:
                lbl.bind("<Button-1>", lambda e, cid=c["id"]: self._switch_conv(cid))
                lbl.bind("<Enter>", lambda e: e.widget.config(fg=Theme.ACCENT))
                lbl.bind("<Leave>", lambda e, cid=c["id"]: e.widget.config(
                    fg=Theme.TEXT_DIM))

    def _draw_tools(self):
        f = (Theme.FONT_FAMILY, 9)
        names = []
        if self.controller.brain and self.controller.brain.registry:
            names = self.controller.brain.registry.list_names()
        text = "\n".join(f"  {n}" for n in names[:15]) if names else "(empty)"
        if len(names) > 15:
            text += f"\n  ... +{len(names)-15}"
        tk.Label(self._content_frame, text=f"tools [{len(names)}]", font=f,
                 fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, anchor="nw", justify="left"
                 ).pack(fill="x")

    def _draw_files(self):
        f = (Theme.FONT_FAMILY, 9)
        bf = (Theme.FONT_FAMILY, 9, "bold")

        header = tk.Frame(self._content_frame, bg=Theme.BG_PANEL)
        header.pack(fill="x", pady=(0, 2))
        tk.Label(header, text="obsidian vault", font=bf,
                 fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, anchor="w"
                 ).pack(side="left")
        refresh_btn = tk.Label(header, text="[↻]", font=bf,
                               fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, cursor="hand2")
        refresh_btn.pack(side="right")
        refresh_btn.bind("<Button-1>", lambda e: self.refresh())
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.config(fg=Theme.ACCENT))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.config(fg=Theme.TEXT_DIM))

        from config.settings import settings
        vault = settings.OBSIDIAN_VAULT_PATH

        if not vault.exists():
            tk.Label(self._content_frame, text="  vault not found", font=f,
                     fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, anchor="w"
                     ).pack(fill="x")
            return

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=Theme.BG_PANEL, foreground=Theme.TEXT_DIM,
                        fieldbackground=Theme.BG_PANEL, font=f, rowheight=20)
        style.configure("Treeview.Item", padding=(0, 0))
        style.map("Treeview", background=[("selected", Theme.BG_LIGHT)],
                  foreground=[("selected", Theme.ACCENT)])

        tree_frame = tk.Frame(self._content_frame, bg=Theme.BG_PANEL)
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(tree_frame, columns=(), show="tree",
                            height=12, style="Treeview")
        tree.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(tree_frame, command=tree.yview, bg=Theme.BG_PANEL,
                              troughcolor=Theme.BG_PANEL, width=6)
        scroll.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scroll.set)

        def populate_tree(parent_node, dir_path: Path, depth=0):
            if depth > 4:
                return
            entries = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for entry in entries:
                if entry.name.startswith("."):
                    continue
                if entry.is_dir():
                    node = tree.insert(parent_node, "end", text=f"  {entry.name}/",
                                       open=False)
                    populate_tree(node, entry, depth + 1)
                elif entry.suffix == ".md":
                    rel = entry.relative_to(vault)
                    tree.insert(parent_node, "end", text=f"  {entry.stem}",
                                tags=(str(entry),))

        populate_tree("", vault)

        def on_tree_click(event):
            item = tree.identify("item", event.x, event.y)
            if not item:
                return
            tags = tree.item(item, "tags")
            if tags:
                self._open_note(Path(tags[0]))

        tree.bind("<ButtonRelease-1>", on_tree_click)

    def _draw_memory(self):
        f = (Theme.FONT_FAMILY, 9)
        bf = (Theme.FONT_FAMILY, 9, "bold")

        tk.Label(self._content_frame, text="saved memories", font=bf,
                 fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, anchor="w"
                 ).pack(fill="x", pady=(0, 4))

        try:
            from ruby.tools.knowledge_tools import ListMemories
            tool = ListMemories()
            result = tool.execute()
            lines = result.split("\n")[:10]
            for line in lines:
                tk.Label(self._content_frame, text=f"  {line[:35]}", font=f,
                         fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, anchor="w"
                         ).pack(fill="x")
        except Exception:
            tk.Label(self._content_frame, text="  (no memories)", font=f,
                     fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL, anchor="w"
                     ).pack(fill="x")

    def _open_note(self, path):
        try:
            import subprocess
            subprocess.Popen(["notepad.exe", str(path)])
        except Exception:
            pass

    def _switch_conv(self, conv_id: str):
        if self.controller.brain and self.on_switch_conv:
            self.controller.brain.switch_conversation(conv_id)
            self.on_switch_conv(conv_id)

    def refresh(self):
        self._show_section(self._current_section)

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
