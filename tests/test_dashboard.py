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

def _world(turn=4, phase="discussion"):
    world = WorldState(
        turn=turn,
        scene=turn,
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
    world.phase = phase
    return world


def _render(console, renderable) -> str:
    with console.capture() as cap:
        console.print(renderable)
    return cap.get()


def test_dashboard_speaks_tuman_language():
    """The Live chrome carries the Operation Tuman visual language:
    classification strips, sonar dividers, reference codes, fog trims —
    while the SITREP table keeps its full labels intact."""
    console = Console(width=100, force_terminal=False)
    dashboard = WargameDashboard(_world(turn=4), console)

    # Header: classification strip + masthead rule + turn/phase, ref code
    header = _render(console, dashboard.render_header())
    assert "TOP SECRET ── UK EYES ONLY" in header
    assert "FALSE FLAG" in header and "OPERATION TUMAN" in header
    assert "TURN 004 │ DISCUSSION" in header
    assert "COBRA/TU/" in header  # deterministic reference code

    # Footer: quick-help row over the closing strip. Short command set only —
    # the full list lives in /menu, and the longer string cropped past 80
    # columns in the no-wrap footer row.
    footer = _render(console, dashboard.render_footer())
    for cmd in ("/status", "/menu", "/advise", "/intel", "/decide", "/quit"):
        assert cmd in footer
    assert "/resources" not in footer and "/briefing" not in footer
    assert "TOP SECRET ── UK EYES ONLY" in footer

    # Feed: classification-strip style title + sonar divider between phases
    dashboard.add_divider("TURN 4 BRIEFING")
    dashboard.add_message("SYSTEM", "Channel check")
    main = _render(console, dashboard.render_main())
    assert "COBRA BRIEFING FEED" in main
    assert "●" in main and "[ TURN 4 BRIEFING ]" in main  # sonar divider
    assert "SYSTEM: Channel check" in main


def test_dashboard_header_trim_is_seeded_per_turn():
    """Each turn's chrome differs deterministically (turn number is the seed)."""
    console = Console(width=100, force_terminal=False)
    header_t1 = _render(console, WargameDashboard(_world(turn=1), console).render_header())
    header_t1_again = _render(console, WargameDashboard(_world(turn=1), console).render_header())
    header_t2 = _render(console, WargameDashboard(_world(turn=2), console).render_header())
    assert header_t1 == header_t1_again  # deterministic
    assert header_t1 != header_t2       # per-turn variation


def test_dashboard_sitrep_keeps_integrity_with_tuman_trim():
    """The SITREP sidebar gains a fog trim and reference code without
    losing any metric labels at its fixed 30-column width."""
    console = Console(width=30, force_terminal=False)
    dashboard = WargameDashboard(_world(), console)
    out = _render(console, dashboard.render_sidebar())
    assert "SITREP" in out
    assert "COBRA/TU/" in out
    for label in ("Risk", "Stability", "Cohesion", "Casualties"):
        assert label in out, f"{label} truncated in SITREP sidebar"
    assert "…" not in out


def test_overlay_speaks_tuman_language():
    """Modal overlays open with a classification strip and close with a
    sonar trace over the return instructions."""
    from cli.dashboard_modal import show_overlay
    from cli.theme import theme_manager

    class FakeLive:
        def stop(self):
            pass

        def start(self):
            pass

    console = Console(width=80, height=24, force_terminal=False)
    with console.capture() as cap:
        show_overlay(console, FakeLive(), "SITUATION STATUS",
                     "All quiet on the northern flank.",
                     theme_manager.get_colors())
    out = cap.get()
    assert "COBRA COMMAND ── SITUATION STATUS" in out
    assert "COBRA/TU/" in out
    assert "All quiet on the northern flank." in out
    assert "Press ENTER to return to dashboard" in out


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
    test_dashboard_speaks_tuman_language()
    test_dashboard_header_trim_is_seeded_per_turn()
    test_dashboard_sitrep_keeps_integrity_with_tuman_trim()
    test_overlay_speaks_tuman_language()
    print("\n[SUCCESS] All dashboard tests passed!")

