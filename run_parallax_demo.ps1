# Run the parallax scene demo with scrolling news ticker and news studio background
# Usage: 
#   .\run_parallax_demo.ps1              (runs with news studio background)
#   .\run_parallax_demo.ps1 -breaking    (runs with dramatic red tones)
#   .\run_parallax_demo.ps1 -daytime     (runs with blue daytime tones)

param(
    [switch]$breaking,
    [switch]$daytime
)

.venv\Scripts\Activate.ps1

# Recompile scene with appropriate background variant if requested
if ($breaking) {
    Write-Host "Compiling BREAKING NEWS background (red tones)..." -ForegroundColor Red
    Copy-Item "assets\news_studio_bg\variants\tile_breaking_news_16x16.png" `
              -Destination "assets\news_studio_bg\tile_16x16.png" `
              -Force
    python -m Graphics.Animations.tools.compile_scene Graphics/Animations/tools/scene_news_studio.yaml --out compiled_news_studio.json --width 120 --height 30 | Out-Null
} elseif ($daytime) {
    Write-Host "Compiling DAYTIME background (blue tones)..." -ForegroundColor Cyan
    Copy-Item "assets\news_studio_bg\variants\tile_daytime_16x16.png" `
              -Destination "assets\news_studio_bg\tile_16x16.png" `
              -Force
    python -m Graphics.Animations.tools.compile_scene Graphics/Animations/tools/scene_news_studio.yaml --out compiled_news_studio.json --width 120 --height 30 | Out-Null
} else {
    Write-Host "Using NEWS STUDIO background (night cityscape)..." -ForegroundColor Blue
}

$ticker = "BREAKING: Royal Navy patrol reports close encounter in GIUK gap | Adversary frigate conducting 'defensive patrol' | NATO allies monitoring situation | PM convenes emergency NSC meeting | Opposition calls for de-escalation | Ministry of Defence reviewing operational posture | "

Write-Host "Starting parallax demo with news ticker..."
Write-Host "Press any key to stop" -ForegroundColor Gray
Write-Host ""

python Graphics/Animations/tools/runtime_player.py `
    compiled_news_studio.json `
    --loop `
    --ticker $ticker `
    --ticker-speed 2 `
    --fps 14

