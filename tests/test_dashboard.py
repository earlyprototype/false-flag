"""Test suite for dashboard UI implementation."""

from pathlib import Path
import sys

# Add project root to path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from cli.dashboard import WargameDashboard
from models.world import WorldState, Metrics
from rich.console import Console

def test_dashboard_initialization():
    """Test dashboard can be created."""
    console = Console()
    world = WorldState(
        turn=1,
        scene=1,
        difficulty="standard",
        metrics=Metrics(
            escalation_risk=60,
            domestic_stability=50,
            alliance_cohesion=40,
            casualties_mil=2,
            casualties_civ=0
        ),
        flags={},
        posture={}
    )
    
    dashboard = WargameDashboard(world, console)
    assert dashboard is not None
    assert dashboard.layout is not None
    print("[PASS] Dashboard initialization")

def test_dashboard_render_header():
    """Test header rendering."""
    console = Console()
    world = WorldState(
        turn=4,
        scene=4,
        difficulty="standard",
        metrics=Metrics(
            escalation_risk=60,
            domestic_stability=50,
            alliance_cohesion=40,
            casualties_mil=2,
            casualties_civ=0
        ),
        flags={},
        posture={}
    )
    
    dashboard = WargameDashboard(world, console)
    header = dashboard.render_header()
    assert header is not None
    print("[PASS] Header rendering")

def test_dashboard_render_sidebar():
    """Test sidebar rendering."""
    console = Console()
    world = WorldState(
        turn=1,
        scene=1,
        difficulty="standard",
        metrics=Metrics(
            escalation_risk=60,
            domestic_stability=50,
            alliance_cohesion=40,
            casualties_mil=2,
            casualties_civ=0
        ),
        flags={},
        posture={}
    )
    
    dashboard = WargameDashboard(world, console)
    sidebar = dashboard.render_sidebar()
    assert sidebar is not None
    print("[PASS] Sidebar rendering")

def test_dashboard_add_message():
    """Test message logging."""
    console = Console()
    world = WorldState(
        turn=1,
        scene=1,
        difficulty="standard",
        metrics=Metrics(
            escalation_risk=60,
            domestic_stability=50,
            alliance_cohesion=40,
            casualties_mil=2,
            casualties_civ=0
        ),
        flags={},
        posture={}
    )
    
    dashboard = WargameDashboard(world, console)
    dashboard.add_message("PM", "What's the threat level?")
    dashboard.add_message("NSA", "CRITICAL - Russian subs approaching")
    
    assert len(dashboard.conversation_log) == 2
    print("[PASS] Message logging")

def test_dashboard_update():
    """Test dashboard can update without errors."""
    console = Console()
    world = WorldState(
        turn=1,
        scene=1,
        difficulty="standard",
        metrics=Metrics(
            escalation_risk=60,
            domestic_stability=50,
            alliance_cohesion=40,
            casualties_mil=2,
            casualties_civ=0
        ),
        flags={},
        posture={}
    )
    
    dashboard = WargameDashboard(world, console)
    dashboard.update()  # Should not raise
    print("[PASS] Dashboard update")

def test_dashboard_render_main():
    """Test main panel rendering."""
    console = Console()
    world = WorldState(
        turn=1,
        scene=1,
        difficulty="standard",
        metrics=Metrics(
            escalation_risk=60,
            domestic_stability=50,
            alliance_cohesion=40,
            casualties_mil=2,
            casualties_civ=0
        ),
        flags={},
        posture={}
    )
    
    dashboard = WargameDashboard(world, console)
    
    # Test with no messages
    main_panel = dashboard.render_main()
    assert main_panel is not None
    
    # Test with messages
    dashboard.add_message("PM", "Test message")
    main_panel = dashboard.render_main()
    assert main_panel is not None
    print("[PASS] Main panel rendering")

def test_dashboard_render_footer():
    """Test footer rendering."""
    console = Console()
    world = WorldState(
        turn=1,
        scene=1,
        difficulty="standard",
        metrics=Metrics(
            escalation_risk=60,
            domestic_stability=50,
            alliance_cohesion=40,
            casualties_mil=2,
            casualties_civ=0
        ),
        flags={},
        posture={}
    )
    
    dashboard = WargameDashboard(world, console)
    footer = dashboard.render_footer()
    assert footer is not None
    print("[PASS] Footer rendering")

def test_dashboard_conversation_log_limit():
    """Test conversation log stays under 100 messages."""
    console = Console()
    world = WorldState(
        turn=1,
        scene=1,
        difficulty="standard",
        metrics=Metrics(
            escalation_risk=60,
            domestic_stability=50,
            alliance_cohesion=40,
            casualties_mil=2,
            casualties_civ=0
        ),
        flags={},
        posture={}
    )
    
    dashboard = WargameDashboard(world, console)
    
    # Add 150 messages
    for i in range(150):
        dashboard.add_message("PM", f"Message {i}")
    
    # Should only keep last 100
    assert len(dashboard.conversation_log) == 100
    assert "Message 149" in dashboard.conversation_log[-1]
    print("[PASS] Conversation log limit")

if __name__ == "__main__":
    print("Running dashboard unit tests...\n")
    test_dashboard_initialization()
    test_dashboard_render_header()
    test_dashboard_render_sidebar()
    test_dashboard_add_message()
    test_dashboard_update()
    test_dashboard_render_main()
    test_dashboard_render_footer()
    test_dashboard_conversation_log_limit()
    print("\n[SUCCESS] All dashboard tests passed!")

