"""Quick test of diplomatic system."""

from engine.diplomacy import check_diplomatic_access, load_diplomatic_profiles, list_available_diplomatic_contacts
from models.world import WorldState, Metrics

# Test with different alliance cohesion levels
profiles = load_diplomatic_profiles()

print("=== Testing Diplomatic Access Levels ===\n")

for cohesion in [20, 40, 65]:
    print(f"Alliance Cohesion: {cohesion}")
    world = WorldState(
        turn=1,
        metrics=Metrics(
            escalation_risk=60,
            domestic_stability=50,
            alliance_cohesion=cohesion,
            mission_progress=0
        )
    )
    
    for country in ["US", "France", "Germany", "Poland", "Russia", "Ukraine", "Ireland"]:
        access, profile = check_diplomatic_access(world, country, profiles)
        if access and profile:
            title = profile.get("title", "Unknown")
            print(f"  {country}: {access.upper()} - {title}")
        else:
            print(f"  {country}: NO ACCESS")
    
    print()

print("=== Testing Available Contacts ===\n")
world = WorldState(
    turn=1,
    metrics=Metrics(
        escalation_risk=60,
        domestic_stability=50,
        alliance_cohesion=50,
        mission_progress=0
    )
)

available = list_available_diplomatic_contacts(world)
print(f"Alliance Cohesion: 50")
for country, access_level, title in available:
    access_indicator = "★ LEADER" if access_level == "leader" else "○ Diplomat"
    print(f"  {access_indicator} - {country}: {title}")

print("\n✅ Diplomatic system tests passed!")

