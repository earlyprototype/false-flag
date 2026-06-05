# Image Sorting Workflow

This folder contains tools to help you organise the generated pixel art images into their proper batch folders.

## 📁 Folder Structure

```
imageoutputs/
├── sorted/
│   ├── batch_1_ui_assets/       ← 9 UI elements
│   ├── batch_2_scene_sprites/   ← 9 scene sprites
│   ├── batch_3_cobra_assets/    ← 9 COBRA scene assets
│   ├── batch_4_titles_effects/  ← 5 titles and effects
│   └── unsorted/                ← Images that don't match prompts
├── Sort-Images.ps1              ← Interactive PowerShell sorting tool
├── SORTING_REFERENCE.md         ← Detailed descriptions of all 32 assets
└── [Your generated images].png
```

## 🚀 Quick Start

### Step 1: Open PowerShell in this folder
```powershell
cd C:\Users\Fab2\Desktop\AI\wargame\imageoutputs
```

### Step 2: Run the sorting script
```powershell
.\Sort-Images.ps1
```

### Step 3: Use the interactive commands

**View unsorted images:**
```powershell
Show-UnsortedImages
```

**See what a batch expects:**
```powershell
Show-BatchAssets 1    # Shows all 9 expected filenames for Batch 1
```

**Move and rename an image:**
```powershell
Move-Image 'Generated Image October 27, 2025 - 9_19AM (6).png' '1' 'title_the_war_game.png'
```

## 📋 Sorting Workflow

1. **Start with easy ones** - Look for distinctive images:
   - Solid black screen → `transition_fade_black.png`
   - Maps with land masses → batch 2
   - Text/titles → batches 1 or 4
   
2. **Use dimensions as clues**:
   - 8x8 = Very small icons (3 total)
   - 16x16 = Small icons (5 total)
   - 320x180 = Full backgrounds (7 total)
   - 320x64/96 = Title graphics
   
3. **Check the reference guide** (`SORTING_REFERENCE.md`) for detailed descriptions

4. **Move non-matching images** to the `unsorted` folder with descriptive names

## 💡 Pro Tips

- Images can be opened in Windows Photo Viewer to see them larger
- Right-click → Properties → Details shows dimensions
- The PowerShell script shows dimensions automatically
- Don't worry about getting everything perfect - focus on the ones you can clearly identify
- Keep similar-looking images grouped for easier comparison

## 🎯 Expected Asset Count

- **Batch 1:** 9 assets (UI elements, icons, backgrounds)
- **Batch 2:** 9 assets (sprites, maps, icons)
- **Batch 3:** 9 assets (COBRA scene, PM sprites, UI)
- **Batch 4:** 5 assets (titles, effects)
- **Total:** 32 unique assets

Since you have ~100 images, there will be multiple variations of each prompt to choose from!

## 🆘 Need Help?

Inside the PowerShell script, type:
```powershell
Show-Help
```

This displays all available commands with examples.







