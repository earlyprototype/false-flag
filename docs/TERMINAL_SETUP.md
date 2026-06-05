# Terminal Setup for Dashboard UI

The dashboard looks MUCH better with a dark terminal background. Here's how to set it up:

## Windows PowerShell

### Method 1: Quick Fix (Current Session Only)

Right-click the PowerShell title bar → Properties:
1. Go to "Colors" tab
2. Set Screen Background to **dark** (RGB: 10, 14, 39)
3. Set Screen Text to **white** (RGB: 241, 250, 238)
4. Click OK

### Method 2: Permanent Fix (Windows Terminal)

If you're using Windows Terminal (recommended):

1. Press `Ctrl+,` to open settings
2. Click on your PowerShell profile
3. Go to "Appearance"
4. Choose a dark colour scheme:
   - **Campbell** (classic)
   - **One Half Dark** (recommended)
   - **Solarized Dark**
5. Save and restart

### Method 3: Install Windows Terminal (Best Option)

If you don't have Windows Terminal:

```powershell
winget install Microsoft.WindowsTerminal
```

Then follow Method 2.

## Test the Dashboard

After changing to dark mode:

```powershell
python -m cli.main_dashboard play --flash-only
```

You should now see:
- **Dark navy background** (#0A0E27)
- **Deep orange borders** (#FF6B35)
- **Colour-coded metrics** (red/amber/teal)
- **High-contrast text** (off-white #F1FAEE)

## Still Looks Wrong?

If the dashboard still has white background:
1. Close PowerShell completely
2. Reopen PowerShell
3. Verify background is dark
4. Run the game again

The dashboard now **forces dark backgrounds** on all panels, but your terminal background should also be dark for the best experience.


