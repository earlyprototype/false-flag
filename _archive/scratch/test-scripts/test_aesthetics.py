"""Visual test of all UI components for CLI aesthetics.

Run this script to preview all Rich UI components in isolation.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from cli.rich_ui import (
    console, phase_header, metrics_table,
    advisor_menu_panel, diplomatic_contacts_table,
    resources_tables, command_menu, metrics_guide_panel
)
from cli.theme import COLORS, SYMBOLS
from cli.formatters import format_advisor_response
from models.world import WorldState, Metrics


def test_phase_headers():
    """Test all phase headers."""
    print("\n" + "=" * 79)
    print("TESTING PHASE HEADERS")
    print("=" * 79 + "\n")
    
    for phase in ["BRIEFING", "DISCUSSION", "DECISION", "ADJUDICATION"]:
        console.print(phase_header(phase, 1))
        print()
        input("Press ENTER to continue...")
        print()


def test_metrics_table():
    """Test metrics table with various values."""
    print("\n" + "=" * 79)
    print("TESTING METRICS TABLE")
    print("=" * 79 + "\n")
    
    # Create test world state
    world = WorldState(
        turn=1,
        scene=1,
        metrics=Metrics(
            escalation_risk=65,
            domestic_stability=45,
            alliance_cohesion=38,
            casualties_mil=2,
            casualties_civ=0
        ),
        flags={},
        posture={}
    )
    world.phase = "discussion"
    
    console.print(metrics_table(world))
    print()
    input("Press ENTER to see with deltas...")
    print()
    
    # Test with deltas
    previous = Metrics(
        escalation_risk=60,
        domestic_stability=50,
        alliance_cohesion=40,
        casualties_mil=2,
        casualties_civ=0
    )
    
    console.print(metrics_table(world, show_deltas=True, previous_metrics=previous))
    print()
    input("Press ENTER to continue...")
    print()


def test_advisor_menu():
    """Test advisor menu panel."""
    print("\n" + "=" * 79)
    print("TESTING ADVISOR MENU")
    print("=" * 79 + "\n")
    
    console.print(advisor_menu_panel())
    print()
    input("Press ENTER to continue...")
    print()


def test_diplomatic_contacts():
    """Test diplomatic contacts table."""
    print("\n" + "=" * 79)
    print("TESTING DIPLOMATIC CONTACTS")
    print("=" * 79 + "\n")
    
    # With contacts
    contacts = [
        ("United States", "leader", "President"),
        ("France", "diplomat", "Ambassador"),
        ("Germany", "diplomat", "Foreign Minister"),
    ]
    
    console.print(diplomatic_contacts_table(contacts))
    print()
    input("Press ENTER to see empty state...")
    print()
    
    # Empty contacts
    console.print(diplomatic_contacts_table([]))
    print()
    input("Press ENTER to continue...")
    print()


def test_resources():
    """Test resources tables."""
    print("\n" + "=" * 79)
    print("TESTING RESOURCES TABLES")
    print("=" * 79 + "\n")
    
    # Mock initial conditions
    initial_conditions = {
        "uk_forces": {
            "naval": [
                {
                    "id": "HMS Queen Elizabeth",
                    "type": "Aircraft Carrier",
                    "location": "Portsmouth",
                    "status": "Operational"
                },
                {
                    "id": "HMS Prince of Wales",
                    "type": "Aircraft Carrier",
                    "location": "Rosyth",
                    "status": "Limited availability"
                }
            ],
            "air": [
                {
                    "id": "617 Squadron",
                    "type": "F-35B Lightning II",
                    "location": "RAF Marham",
                    "status": "Operational",
                    "aircraft_count": 21,
                    "operational_aircraft": 18
                }
            ]
        },
        "stockpiles": {
            "aster_15": {"count": 150, "note": "Short-range air defence"},
            "aster_30": {"count": 100, "note": "Long-range air defence"},
            "tomahawk_cruise_missiles": {"count": 65, "note": "Land-attack capability"},
            "storm_shadow_cruise_missiles": {"count": 50, "note": "Air-launched precision strike"},
            "spearfish_torpedoes": {"count": 80, "note": "Heavy submarine torpedo"}
        }
    }
    
    forces_table, stockpiles_table = resources_tables(initial_conditions)
    
    console.print(forces_table)
    print()
    input("Press ENTER to see stockpiles...")
    print()
    
    console.print(stockpiles_table)
    print()
    input("Press ENTER to continue...")
    print()


def test_command_menu():
    """Test command menu."""
    print("\n" + "=" * 79)
    print("TESTING COMMAND MENU")
    print("=" * 79 + "\n")
    
    console.print(command_menu())
    print()
    input("Press ENTER to continue...")
    print()


def test_metrics_guide():
    """Test metrics guide panel."""
    print("\n" + "=" * 79)
    print("TESTING METRICS GUIDE")
    print("=" * 79 + "\n")
    
    console.print(metrics_guide_panel())
    print()
    input("Press ENTER to continue...")
    print()


def test_advisor_response():
    """Test formatted advisor response."""
    print("\n" + "=" * 79)
    print("TESTING ADVISOR RESPONSE FORMATTING")
    print("=" * 79 + "\n")
    
    # Test normal response
    response1 = "Prime Minister, we assess that Russian intent is to test NATO resolve through a limited incursion. Their cyber operations suggest pre-positioning for infrastructure attacks."
    
    console.print(f"  [{COLORS['secondary']} bold]National Security Advisor[/{COLORS['secondary']} bold]")
    print()
    console.print(format_advisor_response("", response1))
    print()
    input("Press ENTER to see response with warnings...")
    print()
    
    # Test response with warnings
    response2 = "Prime Minister, we assess a high probability of escalation.\n\nCRITICAL: Their cyber operations suggest pre-positioning for infrastructure attacks. We must act immediately.\n\nRECOMMENDATION: Deploy defensive cyber measures and alert critical infrastructure operators within the next 6 hours."
    
    console.print(f"  [{COLORS['secondary']} bold]National Security Advisor[/{COLORS['secondary']} bold]")
    print()
    console.print(format_advisor_response("", response2))
    print()
    input("Press ENTER to continue...")
    print()


def main():
    """Run all visual tests."""
    print("\n" + "=" * 79)
    print("CLI AESTHETICS VISUAL TEST SUITE")
    print("=" * 79)
    print("\nThis script will show you all UI components.")
    print("Press ENTER after each component to continue.")
    print()
    input("Press ENTER to begin...")
    
    test_phase_headers()
    test_metrics_table()
    test_advisor_menu()
    test_diplomatic_contacts()
    test_resources()
    test_command_menu()
    test_metrics_guide()
    test_advisor_response()
    
    print("\n" + "=" * 79)
    print("ALL TESTS COMPLETE")
    print("=" * 79)
    print("\nVisual inspection checklist:")
    print("  [ ] Phase headers display correctly with rounded boxes")
    print("  [ ] Metrics table shows color-coded values and progress bars")
    print("  [ ] Advisor menu is scannable and well-formatted")
    print("  [ ] Diplomatic contacts show leader/diplomat indicators")
    print("  [ ] Resources tables are clear and color-coded")
    print("  [ ] Command menu is easy to read")
    print("  [ ] Metrics guide explains all metrics clearly")
    print("  [ ] Advisor responses have proper structure and highlighting")
    print("  [ ] ASCII characters render correctly (no boxes/question marks)")
    print("  [ ] Colors are restrained and professional")
    print("  [ ] Whitespace creates breathing room")
    print("  [ ] Overall aesthetic is ADHD-friendly and scannable")
    print()


if __name__ == "__main__":
    main()



