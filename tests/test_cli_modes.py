"""Test both CLI modes work in parallel."""

import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

def _utf8_env():
    return {**os.environ, "PYTHONIOENCODING": "utf-8"}


def test_original_cli_works():
    """Verify original CLI is untouched."""
    print("Testing original CLI...")
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=_utf8_env(),
        cwd=root
    )
    
    assert result.returncode == 0, f"Original CLI broken! Exit code: {result.returncode}"
    assert "FALSE FLAG" in result.stdout, "Original CLI output doesn't match expected format"
    print("[PASS] Original CLI: WORKING")

def test_dashboard_cli_works():
    """Verify dashboard CLI runs."""
    print("Testing dashboard CLI...")
    result = subprocess.run(
        [sys.executable, "-m", "cli.main_dashboard", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=_utf8_env(),
        cwd=root
    )
    
    assert result.returncode == 0, f"Dashboard CLI broken! Exit code: {result.returncode}"
    assert "FALSE FLAG" in result.stdout, "Dashboard CLI output doesn't match expected format"
    print("[PASS] Dashboard CLI: WORKING")

def test_dashboard_import():
    """Test that dashboard module can be imported."""
    print("Testing dashboard module import...")
    result = subprocess.run(
        [sys.executable, "-c", "from cli.dashboard import WargameDashboard; print('OK')"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=_utf8_env(),
        cwd=root
    )
    
    assert result.returncode == 0, f"Dashboard import failed! Exit code: {result.returncode}"
    assert "OK" in result.stdout, f"Dashboard import didn't produce expected output: {result.stdout}"
    print("[PASS] Dashboard import: WORKING")

def test_both_commands_available():
    """Verify both CLIs have the same commands available."""
    print("Testing command parity...")
    
    # Get original CLI commands
    original_result = subprocess.run(
        [sys.executable, "-m", "cli.main", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=_utf8_env(),
        cwd=root
    )
    
    # Get dashboard CLI commands
    dashboard_result = subprocess.run(
        [sys.executable, "-m", "cli.main_dashboard", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=_utf8_env(),
        cwd=root
    )
    
    # Both should have 'play', 'batch', 'intro', 'settings'
    required_commands = ["play", "batch", "intro", "settings"]
    
    for cmd in required_commands:
        assert cmd in original_result.stdout, f"Original CLI missing '{cmd}' command"
        assert cmd in dashboard_result.stdout, f"Dashboard CLI missing '{cmd}' command"
    
    print("[PASS] Command parity: VERIFIED")

def test_intro_command():
    """Test that intro command works in both CLIs."""
    print("Testing intro command on both CLIs...")
    
    # Test original
    original_result = subprocess.run(
        [sys.executable, "-m", "cli.main", "intro"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=_utf8_env(),
        cwd=root,
        timeout=10
    )
    
    # Test dashboard
    dashboard_result = subprocess.run(
        [sys.executable, "-m", "cli.main_dashboard", "intro"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=_utf8_env(),
        cwd=root,
        timeout=10
    )
    
    # Both should complete without errors
    assert original_result.returncode == 0, f"Original intro failed: {original_result.returncode}"
    assert dashboard_result.returncode == 0, f"Dashboard intro failed: {dashboard_result.returncode}"
    
    print("[PASS] Intro command: WORKING on both CLIs")

def test_play_intro_smoke_non_tty():
    """`play --intro-only` on piped stdio: instant cinematics, scene cards.

    Exercises the non-TTY fast path of the title sequence and the scene
    stamp-ins end to end (the four numeric menus, the animated masthead's
    static frame, and all three intro scene cards).
    """
    print("Testing play --intro-only smoke (non-TTY cinematics)...")
    env = _utf8_env()
    env["WARGAME_LLM"] = "mock"
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "play", "--intro-only"],
        input="1\n1\n1\n1\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=root,
        timeout=120,
        env=env,
    )
    assert result.returncode == 0, (
        f"intro-only run failed ({result.returncode}): {result.stderr[-2000:]}")
    out = result.stdout
    assert "██" in out, "title masthead missing"
    assert "OPERATION TUMAN" in out, "tagline missing"
    assert "TOP SECRET" in out, "classification strips missing"
    for scene in ("SCENE I", "SCENE II", "SCENE III"):
        assert scene in out, f"{scene} card missing"
    assert "69°04'N 033°25'E" in out, "scene coordinates missing"
    print("[PASS] play --intro-only smoke: WORKING")


def test_no_stochastic_injects_is_honoured():
    """ER-026: --no-stochastic-injects must actually disable generation.

    The old loop forced the flag back on at the transition turn, so the
    option's only effect was to trigger (and pause on) the DYNAMIC
    GENERATION banner. The decision now lives in
    engine.sim_loop.stochastic_generation_status, which both CLI loops
    consume for the same (use_stochastic, show_banner) pair.
    """
    from engine.sim_loop import stochastic_generation_status

    # Flag off: generation never fires and the banner never shows, on any
    # turn either side of the transition point.
    for turn in (1, 6, 7, 8, 20):
        use, banner = stochastic_generation_status(
            turn, 7, stochastic_injects=False, banner_shown=False)
        assert use is False, f"turn {turn}: generation fired with the flag off"
        assert banner is False, f"turn {turn}: banner shown with the flag off"

    # Flag on: nothing before the transition...
    use, banner = stochastic_generation_status(6, 7, True, False)
    assert (use, banner) == (False, False)
    # ...then generation fires and the banner plays exactly once...
    use, banner = stochastic_generation_status(7, 7, True, False)
    assert (use, banner) == (True, True)
    # ...and never again once it has been shown.
    use, banner = stochastic_generation_status(8, 7, True, True)
    assert (use, banner) == (True, False)
    print("[PASS] --no-stochastic-injects honoured")


def test_cli_loops_no_longer_force_the_flag_back_on():
    """ER-026 regression tripwire: the override `stochastic_injects = True`
    is gone from both CLI loops, and both consume the shared helper."""
    for cli_file in ("cli/main.py", "cli/main_dashboard.py"):
        source = (root / cli_file).read_text(encoding="utf-8")
        assert "stochastic_injects = True" not in source, (
            f"{cli_file} still overrides --no-stochastic-injects at the "
            "transition turn")
        assert "stochastic_generation_status" in source, (
            f"{cli_file} does not use the shared transition helper")
    print("[PASS] CLI loops honour the flag")


if __name__ == "__main__":
    print("Running CLI integration tests...\n")
    
    try:
        test_original_cli_works()
        test_dashboard_cli_works()
        test_dashboard_import()
        test_both_commands_available()
        test_intro_command()
        print("\n[SUCCESS] All CLI integration tests passed!")
        print("\nBoth CLI modes are operational and compatible!")
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

