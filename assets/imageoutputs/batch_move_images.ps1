# Batch Image Sorting Script
# This script moves and renames all identified images to their proper batch folders

Write-Host "Starting batch image sorting..." -ForegroundColor Cyan

# Create a mapping of source files to their target batch and filename
$imageMappings = @{}

# Helper function to add mapping
function Add-Mapping {
    param($sourceFile, $batch, $targetFile)
    $imageMappings[$sourceFile] = @($batch, $targetFile)
}

# BATCH 1 - UI Assets (9_08AM series)
Add-Mapping "Generated Image October 27, 2025 - 9_08AM.png" "1" "title_the_war_game.png"
Add-Mapping "Generated Image October 27, 2025 - 9_08AM (1).png" "1" "episode_title_false_flag.png"
Add-Mapping "Generated Image October 27, 2025 - 9_08AM (2).png" "1" "news_ticker_bg.png"
Add-Mapping "Generated Image October 27, 2025 - 9_08AM (3).png" "1" "lower_third_template.png"
Add-Mapping "Generated Image October 27, 2025 - 9_08AM (4).png" "1" "icon_map_marker.png"
Add-Mapping "Generated Image October 27, 2025 - 9_08AM (5).png" "1" "icon_clock.png"
Add-Mapping "Generated Image October 27, 2025 - 9_08AM (6).png" "1" "bg_war_room.png"
Add-Mapping "Generated Image October 27, 2025 - 9_08AM (7).png" "1" "bg_news_studio.png"
Add-Mapping "Generated Image October 27, 2025 - 9_08AM (8).png" "1" "bg_barents_sea_dark.png"

# BATCH 2 - Scene Sprites (9_09AM series)
Add-Mapping "Generated Image October 27, 2025 - 9_09AM.png" "2" "sprite_moon_crescent.png"
Add-Mapping "Generated Image October 27, 2025 - 9_09AM (1).png" "2" "sprite_submarine_silhouette.png"
Add-Mapping "Generated Image October 27, 2025 - 9_09AM (2).png" "2" "sprite_observer_binoculars.png"
Add-Mapping "Generated Image October 27, 2025 - 9_09AM (3).png" "2" "bg_map_north_atlantic.png"
Add-Mapping "Generated Image October 27, 2025 - 9_09AM (4).png" "2" "icon_force_blue.png"
Add-Mapping "Generated Image October 27, 2025 - 9_09AM (5).png" "2" "icon_force_red.png"
Add-Mapping "Generated Image October 27, 2025 - 9_09AM (6).png" "2" "bg_operations_room.png"
Add-Mapping "Generated Image October 27, 2025 - 9_09AM (7).png" "2" "sprite_commander_navy.png"
Add-Mapping "Generated Image October 27, 2025 - 9_09AM (8).png" "2" "icon_phone_ringing.png"

# BATCH 3 - COBRA Assets (9_10AM to 9_19AM series)
Add-Mapping "Generated Image October 27, 2025 - 9_10AM.png" "3" "subtitle_you_are_pm.png"
Add-Mapping "Generated Image October 27, 2025 - 9_10AM (1).png" "3" "title_false_flag.png"
Add-Mapping "Generated Image October 27, 2025 - 9_10AM (2).png" "3" "effect_water_ripple.png"
Add-Mapping "Generated Image October 27, 2025 - 9_10AM (3).png" "3" "effect_pulse_glow.png"
Add-Mapping "Generated Image October 27, 2025 - 9_10AM (4).png" "3" "transition_fade_black.png"

Add-Mapping "Generated Image October 27, 2025 - 9_11AM.png" "2" "sprite_sweat_drop.png"

Add-Mapping "Generated Image October 27, 2025 - 9_12AM.png" "3" "bg_uk_gov_iconography.png"
Add-Mapping "Generated Image October 27, 2025 - 9_12AM (1).png" "3" "sprite_pm_stern.png"
Add-Mapping "Generated Image October 27, 2025 - 9_12AM (2).png" "3" "bg_war_room_table_perspective.png"
Add-Mapping "Generated Image October 27, 2025 - 9_12AM (3).png" "3" "sprite_advisor_seated_small.png"
Add-Mapping "Generated Image October 27, 2025 - 9_12AM (4).png" "3" "sprite_pm_face_closeup.png"
Add-Mapping "Generated Image October 27, 2025 - 9_12AM (5).png" "3" "ui_dialogue_box.png"

Add-Mapping "Generated Image October 27, 2025 - 9_13AM.png" "3" "ui_location_timestamp.png"
Add-Mapping "Generated Image October 27, 2025 - 9_13AM (1).png" "3" "bg_operations_room.png"
Add-Mapping "Generated Image October 27, 2025 - 9_13AM (2).png" "3" "bg_map_north_atlantic.png"
Add-Mapping "Generated Image October 27, 2025 - 9_13AM (3).png" "3" "bg_news_studio.png"
Add-Mapping "Generated Image October 27, 2025 - 9_13AM (4).png" "3" "bg_war_room.png"

Add-Mapping "Generated Image October 27, 2025 - 9_14AM.png" "3" "transition_fade_black.png"
Add-Mapping "Generated Image October 27, 2025 - 9_14AM (1).png" "3" "sprite_pm_back_of_head.png"
Add-Mapping "Generated Image October 27, 2025 - 9_14AM (2).png" "3" "sprite_commander_navy.png"
Add-Mapping "Generated Image October 27, 2025 - 9_14AM (3).png" "3" "bg_operations_room.png"
Add-Mapping "Generated Image October 27, 2025 - 9_14AM (4).png" "3" "bg_map_north_atlantic.png"
Add-Mapping "Generated Image October 27, 2025 - 9_14AM (5).png" "3" "bg_news_studio.png"

Add-Mapping "Generated Image October 27, 2025 - 9_15AM.png" "3" "subtitle_you_are_pm.png"

Add-Mapping "Generated Image October 27, 2025 - 9_16AM.png" "3" "sprite_pm_stern.png"
Add-Mapping "Generated Image October 27, 2025 - 9_16AM (1).png" "3" "bg_uk_gov_iconography.png"
Add-Mapping "Generated Image October 27, 2025 - 9_16AM (2).png" "3" "bg_operations_room.png"
Add-Mapping "Generated Image October 27, 2025 - 9_16AM (3).png" "3" "bg_map_north_atlantic.png"

Add-Mapping "Generated Image October 27, 2025 - 9_17AM.png" "3" "bg_uk_gov_iconography.png"
Add-Mapping "Generated Image October 27, 2025 - 9_17AM (1).png" "3" "sprite_pm_stern.png"
Add-Mapping "Generated Image October 27, 2025 - 9_17AM (2).png" "3" "bg_war_room_table_perspective.png"
Add-Mapping "Generated Image October 27, 2025 - 9_17AM (3).png" "3" "sprite_advisor_seated_small.png"
Add-Mapping "Generated Image October 27, 2025 - 9_17AM (4).png" "3" "sprite_pm_face_closeup.png"
Add-Mapping "Generated Image October 27, 2025 - 9_17AM (5).png" "3" "ui_dialogue_box.png"
Add-Mapping "Generated Image October 27, 2025 - 9_17AM (6).png" "3" "ui_location_timestamp.png"
Add-Mapping "Generated Image October 27, 2025 - 9_17AM (7).png" "2" "sprite_sweat_drop.png"
Add-Mapping "Generated Image October 27, 2025 - 9_17AM (8).png" "2" "sprite_moon_crescent.png"
Add-Mapping "Generated Image October 27, 2025 - 9_17AM (9).png" "2" "sprite_submarine_silhouette.png"
Add-Mapping "Generated Image October 27, 2025 - 9_17AM (10).png" "2" "sprite_observer_binoculars.png"
Add-Mapping "Generated Image October 27, 2025 - 9_17AM (11).png" "2" "icon_phone_ringing.png"

Add-Mapping "Generated Image October 27, 2025 - 9_18AM.png" "3" "sprite_pm_back_of_head.png"
Add-Mapping "Generated Image October 27, 2025 - 9_18AM (1).png" "3" "bg_operations_room.png"

Add-Mapping "Generated Image October 27, 2025 - 9_19AM.png" "3" "sprite_pm_back_of_head.png"
Add-Mapping "Generated Image October 27, 2025 - 9_19AM (1).png" "3" "bg_war_room_table_perspective.png"
Add-Mapping "Generated Image October 27, 2025 - 9_19AM (2).png" "3" "sprite_advisor_seated_small.png"
Add-Mapping "Generated Image October 27, 2025 - 9_19AM (3).png" "3" "sprite_pm_face_closeup.png"
Add-Mapping "Generated Image October 27, 2025 - 9_19AM (4).png" "2" "sprite_sweat_drop.png"
Add-Mapping "Generated Image October 27, 2025 - 9_19AM (5).png" "3" "ui_location_timestamp.png"
Add-Mapping "Generated Image October 27, 2025 - 9_19AM (6).png" "3" "ui_dialogue_box.png"

# BATCH 4 - Titles & Effects (limited assets)
Add-Mapping "Generated Image October 27, 2025 - 9_10AM (3).png" "4" "effect_pulse_glow.png"

# Folder mappings
$batchFolders = @{
    "1" = "sorted/batch_1_ui_assets"
    "2" = "sorted/batch_2_scene_sprites"
    "3" = "sorted/batch_3_cobra_assets"
    "4" = "sorted/batch_4_titles_effects"
    "u" = "sorted/unsorted"
}

$successCount = 0
$errorCount = 0

foreach ($sourceFile in $imageMappings.Keys) {
    $batch = $imageMappings[$sourceFile][0]
    $targetFile = $imageMappings[$sourceFile][1]
    $targetFolder = $batchFolders[$batch]

    $sourcePath = Join-Path "." $sourceFile
    $targetPath = Join-Path $targetFolder $targetFile

    if (Test-Path $sourcePath) {
        try {
            # Create target directory if it doesn't exist
            if (-not (Test-Path $targetFolder)) {
                New-Item -ItemType Directory -Path $targetFolder -Force | Out-Null
            }

            Move-Item -Path $sourcePath -Destination $targetPath -Force
            Write-Host "SUCCESS [$batch] $sourceFile → $targetFile" -ForegroundColor Green
            $successCount++
        }
        catch {
            Write-Host "ERROR [$batch] Failed to move $sourceFile`: $($_.Exception.Message)" -ForegroundColor Red
            $errorCount++
        }
    }
    else {
        Write-Host "WARNING [$batch] Source file not found: $sourceFile" -ForegroundColor Yellow
        $errorCount++
    }
}

# Summary
Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "SORTING COMPLETE!" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan
Write-Host "Successfully moved: $successCount images" -ForegroundColor Green
Write-Host "Errors: $errorCount" -ForegroundColor Red

if ($errorCount -eq 0) {
    Write-Host "All images sorted successfully!" -ForegroundColor Green
}
else {
    Write-Host "Some images could not be moved. Check the errors above." -ForegroundColor Yellow
}

Write-Host "`nFiles have been organized into:" -ForegroundColor White
foreach ($batch in (1..4)) {
    $folder = $batchFolders[$batch.ToString()]
    if (Test-Path $folder) {
        $fileCount = (Get-ChildItem -Path $folder -File).Count
        Write-Host "   Batch $batch ($folder): $fileCount files" -ForegroundColor Gray
    }
}
