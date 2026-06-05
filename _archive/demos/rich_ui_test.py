"""Test Rich console compatibility with msvcrt keyboard input.

Run this FIRST before making any other changes.

Usage:
    python cli/rich_ui_test.py
    or
    .\.venv\Scripts\python.exe cli\rich_ui_test.py
"""

import sys
import msvcrt
from rich.console import Console

console = Console(
    legacy_windows=(sys.platform == "win32"),
    force_terminal=True,
    force_interactive=False
)

console.print("[green bold]Rich Console Initialized[/green bold]")
console.print("")
console.print("Testing msvcrt.kbhit() compatibility...")
console.print("Press SPACE to test keyboard detection...")
console.print("")

while True:
    if msvcrt.kbhit():
        key = msvcrt.getch()
        if key == b' ':
            console.print("[yellow bold]SUCCESS: SPACE detected![/yellow bold]")
            console.print("[green]msvcrt.kbhit() works with Rich Console[/green]")
            break
        else:
            console.print(f"[dim]Other key pressed: {key}[/dim]")

console.print("")
console.print("[green bold]Test Passed - Safe to proceed[/green bold]")

