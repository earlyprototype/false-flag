# Rich Colour Display Issue Report

## Problem Summary
After converting all `typer.secho()` calls to Rich `console.print()`, colours are not displaying in the Windows PowerShell terminal.

## Root Cause
**Windows PowerShell (5.1) has limited ANSI colour support.** Rich detects this and may fall back to plain text output.

## Evidence
1. ✅ All code conversions completed successfully (26 instances)
2. ✅ No linter errors
3. ✅ Imports are correct (`console` and `COLORS` available at module level)
4. ❌ Colours not displaying in terminal output
5. ❌ Unicode bullet character `•` displays as `ò`

## Test Results
```powershell
.\.venv\Scripts\python.exe -c "from rich.console import Console; c = Console(); c.print('[green bold]GREEN TEST[/green bold]')"
# Output: GREEN TEST (no colour)
```

## Solutions

### Option 1: Use Windows Terminal (RECOMMENDED)
Windows Terminal has full ANSI colour support.

**Steps:**
1. Install Windows Terminal from Microsoft Store (if not already installed)
2. Open Windows Terminal
3. Run the game: `.\.venv\Scripts\python.exe -m cli.main play`

### Option 2: Enable Virtual Terminal Processing in PowerShell
Add this to your PowerShell profile to force ANSI support:

```powershell
# Add to: $PROFILE (C:\Users\YourName\Documents\PowerShell\Microsoft.PowerShell_profile.ps1)
$null = [System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSStyle.OutputRendering = 'Ansi'
```

### Option 3: Use Command Prompt (cmd.exe)
Windows 10+ Command Prompt has better ANSI support than PowerShell 5.1.

**Steps:**
1. Open Command Prompt (not PowerShell)
2. Navigate to: `cd C:\Users\Fab2\Desktop\AI\wargame`
3. Activate venv: `.venv\Scripts\activate.bat`
4. Run game: `python -m cli.main play`

### Option 4: Force Rich Colour Output
We can force Rich to always use colours regardless of terminal detection:

```python
# In cli/rich_ui.py, modify console initialization:
console = Console(
    legacy_windows=True,
    force_interactive=False,
    force_terminal=True,  # ADD THIS
    color_system="windows"  # ADD THIS
)
```

## Recommended Action
**Try Windows Terminal first** - it's the most reliable solution for modern Windows development.

If you need PowerShell 5.1 specifically, I can implement Option 4 (force colours).

## Additional Fix Applied
Changed Unicode bullet `•` to simple dash `-` for better Windows compatibility in selection screens.

## Files Modified
- `cli/main.py` - Removed duplicate imports, fixed bullets
- `engine/sim_loop.py` - Fixed Rich markup bug

## Status
- ✅ Code fixes complete
- ⚠️ Terminal colour support needed
- ✅ Bullet character fixed


