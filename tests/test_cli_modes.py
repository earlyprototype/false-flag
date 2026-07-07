"""Test both CLI modes work in parallel."""

import subprocess
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

def test_original_cli_works():
    """Verify original CLI is untouched."""
    print("Testing original CLI...")
    result = subprocess.run(
        ["python", "-m", "cli.main", "--help"],
        capture_output=True,
        text=True,
        cwd=root
    )
    
    assert result.returncode == 0, f"Original CLI broken! Exit code: {result.returncode}"
    assert "FALSE FLAG" in result.stdout, "Original CLI output doesn't match expected format"
    print("[PASS] Original CLI: WORKING")
    return True

def test_dashboard_cli_works():
    """Verify dashboard CLI runs."""
    print("Testing dashboard CLI...")
    result = subprocess.run(
        ["python", "-m", "cli.main_dashboard", "--help"],
        capture_output=True,
        text=True,
        cwd=root
    )
    
    assert result.returncode == 0, f"Dashboard CLI broken! Exit code: {result.returncode}"
    assert "FALSE FLAG" in result.stdout, "Dashboard CLI output doesn't match expected format"
    print("[PASS] Dashboard CLI: WORKING")
    return True

def test_dashboard_import():
    """Test that dashboard module can be imported."""
    print("Testing dashboard module import...")
    result = subprocess.run(
        ["python", "-c", "from cli.dashboard import WargameDashboard; print('OK')"],
        capture_output=True,
        text=True,
        cwd=root
    )
    
    assert result.returncode == 0, f"Dashboard import failed! Exit code: {result.returncode}"
    assert "OK" in result.stdout, f"Dashboard import didn't produce expected output: {result.stdout}"
    print("[PASS] Dashboard import: WORKING")
    return True

def test_both_commands_available():
    """Verify both CLIs have the same commands available."""
    print("Testing command parity...")
    
    # Get original CLI commands
    original_result = subprocess.run(
        ["python", "-m", "cli.main", "--help"],
        capture_output=True,
        text=True,
        cwd=root
    )
    
    # Get dashboard CLI commands
    dashboard_result = subprocess.run(
        ["python", "-m", "cli.main_dashboard", "--help"],
        capture_output=True,
        text=True,
        cwd=root
    )
    
    # Both should have 'play', 'batch', 'intro', 'settings'
    required_commands = ["play", "batch", "intro", "settings"]
    
    for cmd in required_commands:
        assert cmd in original_result.stdout, f"Original CLI missing '{cmd}' command"
        assert cmd in dashboard_result.stdout, f"Dashboard CLI missing '{cmd}' command"
    
    print("[PASS] Command parity: VERIFIED")
    return True

def test_intro_command():
    """Test that intro command works in both CLIs."""
    print("Testing intro command on both CLIs...")
    
    # Test original
    original_result = subprocess.run(
        ["python", "-m", "cli.main", "intro"],
        capture_output=True,
        text=True,
        cwd=root,
        timeout=10
    )
    
    # Test dashboard
    dashboard_result = subprocess.run(
        ["python", "-m", "cli.main_dashboard", "intro"],
        capture_output=True,
        text=True,
        cwd=root,
        timeout=10
    )
    
    # Both should complete without errors
    assert original_result.returncode == 0, f"Original intro failed: {original_result.returncode}"
    assert dashboard_result.returncode == 0, f"Dashboard intro failed: {dashboard_result.returncode}"
    
    print("[PASS] Intro command: WORKING on both CLIs")
    return True

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

