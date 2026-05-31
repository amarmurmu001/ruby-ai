#!/usr/bin/env python3
"""
Ruby — AI Assistant
Built from scratch. Custom neural brain. No APIs. No cloud.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from gui.chat_window import RubyGUI

def main():
    app = RubyGUI()
    app.run()

if __name__ == "__main__":
    main()
