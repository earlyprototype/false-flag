@echo off
setlocal

rem Change to repo root (this script's directory)
cd /d "%~dp0"

set PY="%CD%\.venv\Scripts\python.exe"

echo === Wargame Preview ===
echo 1) Run Intro (text)
echo 2) Run Animation Preview
echo Q) Quit
choice /C 12Q /N /M "Select option: "
if errorlevel 3 goto end
if errorlevel 2 goto run_anim
if errorlevel 1 goto run_intro

:run_intro
if exist %PY% (
  %PY% -m cli.main --intro-only
) else (
  rem Fallback to py launcher or system python
  where py >nul 2>nul && (py -m cli.main --intro-only) || (
    python -m cli.main --intro-only
  )
)
goto end

:run_anim
if exist %PY% (
  %PY% -m Graphics.Animations.tools.runtime_player "%CD%\compiled_scene.json" --fps 14 --duration 10 --overlay --noinput
) else (
  rem Fallback to py launcher or system python
  where py >nul 2>nul && (py -m Graphics.Animations.tools.runtime_player "%CD%\compiled_scene.json" --fps 14 --duration 10 --overlay --noinput) || (
    python -m Graphics.Animations.tools.runtime_player "%CD%\compiled_scene.json" --fps 14 --duration 10 --overlay --noinput
  )
)
goto end

endlocal



