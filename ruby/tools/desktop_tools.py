import logging
import os
import subprocess
from pathlib import Path
from datetime import datetime
from .base import Tool

logger = logging.getLogger("ruby.tools.desktop")


class OpenFile(Tool):
    name = "open_file"
    description = "Open a file or folder with its default application. Use for opening documents, folders, launching apps."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to file or folder to open"}
        },
        "required": ["path"]
    }

    def execute(self, path: str) -> str:
        try:
            p = Path(path).expanduser().resolve()
            if not p.exists():
                return f"Path not found: {p}"
            os.startfile(str(p))
            return f"Opened: {p}"
        except Exception as e:
            return f"Error opening: {e}"


class ReadClipboard(Tool):
    name = "read_clipboard"
    description = "Read the current text content from the system clipboard"
    parameters = {
        "type": "object",
        "properties": {}
    }

    def execute(self) -> str:
        try:
            import pyperclip
            text = pyperclip.paste()
            if text:
                return f"Clipboard: {text[:2000]}"
            return "Clipboard is empty"
        except Exception as e:
            return f"Clipboard error: {e}"


class WriteClipboard(Tool):
    name = "write_clipboard"
    description = "Write text to the system clipboard"
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to copy to clipboard"}
        },
        "required": ["text"]
    }

    def execute(self, text: str) -> str:
        try:
            import pyperclip
            pyperclip.copy(text)
            return f"Copied to clipboard ({len(text)} chars)"
        except Exception as e:
            return f"Clipboard error: {e}"


class ShowNotification(Tool):
    name = "show_notification"
    description = "Show a Windows toast notification"
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Notification title"},
            "message": {"type": "string", "description": "Notification body text"}
        },
        "required": ["title", "message"]
    }

    def execute(self, title: str, message: str) -> str:
        try:
            import winrt.windows.ui.notifications as notifications
            import winrt.windows.data.xml.dom as dom

            app = notifications.ToastNotificationManager.get_template(
                notifications.ToastTemplateType.TOAST_TEXT02
            )
            xml = dom.XmlDocument()
            xml.load_xml(app.get_xml())
            nodes = xml.select_single_node("/toast/visual/binding/text[@id='1']")
            if nodes:
                nodes.inner_text = title
            nodes2 = xml.select_single_node("/toast/visual/binding/text[@id='2']")
            if nodes2:
                nodes2.inner_text = message

            toast = notifications.ToastNotification(xml)
            notifications.ToastNotificationManager.create_toast_notifier().show(toast)
            return "Notification shown"
        except ImportError:
            pass
        try:
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $xml = New-Object -TypeName Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template.GetXml())
            $nodes = $xml.SelectSingleNode("/toast/visual/binding/text[@id='1']")
            $nodes.InnerText = '{title}'
            $nodes2 = $xml.SelectSingleNode("/toast/visual/binding/text[@id='2']")
            $nodes2.InnerText = '{message}'
            $toast = New-Object -TypeName Windows.UI.Notifications.ToastNotification -ArgumentList $xml
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier().Show($toast)
            '''
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=10)
            return "Notification shown"
        except Exception as e:
            return f"Notification error: {e}"


class Screenshot(Tool):
    name = "screenshot"
    description = "Take a screenshot and optionally extract text from it via OCR"
    parameters = {
        "type": "object",
        "properties": {
            "ocr": {"type": "boolean", "description": "Whether to extract text via OCR (default: false)"}
        }
    }

    def execute(self, ocr: bool = False) -> str:
        try:
            import PIL.ImageGrab
            img = PIL.ImageGrab.grab()
            tmp = os.path.join(os.environ["TEMP"], "ruby_screenshot.png")
            img.save(tmp)
            if not ocr:
                return f"Screenshot saved to {tmp}"

            import pytesseract
            text = pytesseract.image_to_string(img)
            if text.strip():
                return f"Screenshot text:\n{text[:3000]}"
            return "No text found in screenshot"
        except Exception as e:
            return f"Screenshot error: {e}"


class GetActiveWindow(Tool):
    name = "get_active_window"
    description = "Get the title of the currently active window"
    parameters = {
        "type": "object",
        "properties": {}
    }

    def execute(self) -> str:
        try:
            import ctypes
            user32 = ctypes.windll.user32
            handle = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(handle)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(handle, buf, length + 1)
            title = buf.value
            return f"Active window: {title}" if title else "Could not get active window"
        except Exception as e:
            return f"Window error: {e}"


class ListWindows(Tool):
    name = "list_windows"
    description = "List all open window titles"
    parameters = {
        "type": "object",
        "properties": {}
    }

    def execute(self) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object -ExpandProperty MainWindowTitle"],
                capture_output=True, text=True, timeout=10
            )
            windows = [w.strip() for w in result.stdout.split("\n") if w.strip()]
            if windows:
                return "Open windows:\n" + "\n".join(windows[:30])
            return "No visible windows found"
        except Exception as e:
            return f"List windows error: {e}"
