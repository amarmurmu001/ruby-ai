import logging
import sys
from datetime import datetime
from config.settings import settings

logger = logging.getLogger("ruby.ui")

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich import box
    HAS_RICH = True
    console = Console(color_system="auto")
except ImportError:
    HAS_RICH = False
    console = None

class TerminalUI:
    def __init__(self):
        self.has_rich = HAS_RICH

    def show_banner(self):
        banner = """
  ,---.  ,--. ,--. ,---.  ,--.   ,--.
 /  O  \\ |  | |  ||  O  | |  |   |  |
|  .-.  ||  | |  ||  .-. | |  |   |  |
|  | |  ||  '-'  ||  | | | |  '--.|  |
`--' `--' `-----' `--' `--' `-----'`--'
  Your AI Assistant -- v{version}
  "Like Jarvis, but Ruby"
        """.format(version=settings.APP_VERSION)

        if self.has_rich:
            console.print(f"[bold magenta]{banner}[/bold magenta]")
            console.print(f"[dim]Model: {settings.HERMES_MODEL} | "
                         f"Vault: {settings.OBSIDIAN_VAULT_PATH}[/dim]\n")
        else:
            print(banner)

    def show_help(self):
        if self.has_rich:
            table = Table(title="Ruby Commands", box=box.ROUNDED)
            table.add_column("Command", style="cyan")
            table.add_column("Description", style="white")
            table.add_row("/help", "Show this help")
            table.add_row("/exit", "Exit Ruby")
            table.add_row("/reset", "Reset conversation")
            table.add_row("/save", "Save current conversation to memory")
            table.add_row("/tools", "List available tools")
            table.add_row("/voice", "Toggle voice mode")
            table.add_row("/auto", "Toggle autonomous mode")
            table.add_row("/plan", "Create and execute multi-step plan")
            console.print(table)
        else:
            print("""
Commands:
  /help   - Show help
  /exit   - Exit Ruby
  /reset  - Reset conversation
  /save   - Save current conversation to memory
  /tools  - List available tools
  /voice  - Toggle voice mode
  /auto   - Toggle autonomous mode
  /plan   - Create and execute multi-step plan
""")

    def show_tools(self, tools_list: list[str]):
        if self.has_rich:
            table = Table(title="Available Tools", box=box.ROUNDED)
            table.add_column("Tool Name", style="green")
            for t in tools_list:
                table.add_row(t)
            console.print(table)
        else:
            print("Tools:", ", ".join(tools_list))

    def show_thinking(self):
        if self.has_rich:
            console.print("[dim]Ruby is thinking...[/dim]")
        else:
            print("Ruby is thinking...")

    def show_response(self, text: str):
        if self.has_rich:
            md = Markdown(text)
            panel = Panel(md, title="[bold magenta]Ruby[/bold magenta]",
                          border_style="magenta", box=box.ROUNDED)
            console.print(panel)
        else:
            print(f"\nRuby: {text}\n")

    def show_response_stream(self, text: str):
        if self.has_rich:
            console.print(f"[magenta]{text}[/magenta]", end="")
        else:
            print(text, end="")

    def show_error(self, text: str):
        if self.has_rich:
            console.print(f"[bold red]Error:[/bold red] {text}")
        else:
            print(f"Error: {text}")

    def show_system(self, text: str):
        if self.has_rich:
            console.print(f"[dim]{text}[/dim]")
        else:
            print(text)

    def show_confirmation(self, text: str) -> bool:
        if self.has_rich:
            console.print(f"[bold yellow]{text} (y/n)[/bold yellow]")
        else:
            print(f"{text} (y/n)")
        answer = input("> ")
        return answer.lower() in ("y", "yes", "yeah", "yep")

    def get_input(self, prompt_text: str = "You") -> str:
        if self.has_rich:
            console.print(f"[bold cyan]{prompt_text}:[/bold cyan] ", end="")
        else:
            print(f"{prompt_text}: ", end="")
        return input("")

    def show_tool_result(self, result: str):
        if self.has_rich:
            console.print(f"[dim green]=> {result[:200]}[/dim green]")
        else:
            print(f"=> {result[:200]}")

ui = TerminalUI()
