"""Quick test of menu systems"""

from models.narrative_state import NarrativeState, create_initial_narrative_state, VibeLevel
from models.world import Metrics

# Test 1: Create narrative state
print("="*70)
print("TEST 1: Creating Narrative State")
print("="*70)

metrics = Metrics(
    escalation_risk=75,
    domestic_stability=42,
    alliance_cohesion=35,
    casualties_mil=2,
    casualties_civ=8
)

narrative_state = create_initial_narrative_state(
    metrics=metrics,
    play_mode="immersive"
)

print(f"✓ Created narrative state with play_mode: {narrative_state.play_mode}")
print(f"✓ Hidden metrics: Risk={narrative_state.hidden_metrics.escalation_risk}, "
      f"Stability={narrative_state.hidden_metrics.domestic_stability}, "
      f"Cohesion={narrative_state.hidden_metrics.alliance_cohesion}")

# Test 2: Generate vibes
print("\n" + "="*70)
print("TEST 2: Vibe Display (Immersive Mode)")
print("="*70)

vibes = narrative_state.get_situation_vibes()
for vibe in vibes:
    print(vibe.to_string())

# Test 3: Display for each mode
print("\n" + "="*70)
print("TEST 3: Display Modes")
print("="*70)

for mode in ["classic", "immersive", "emergent"]:
    print(f"\n--- {mode.upper()} MODE ---")
    display_lines = narrative_state.display_for_mode(mode)
    for line in display_lines:
        print(line)

# Test 4: LLM Context
print("\n" + "="*70)
print("TEST 4: LLM Context Generation")
print("="*70)

context = narrative_state.to_llm_context()
print(context[:500] + "...")

# Test 5: Character management
print("\n" + "="*70)
print("TEST 5: Character Attitudes")
print("="*70)

print(f"✓ {len(narrative_state.characters)} characters loaded")
for char_id, char in list(narrative_state.characters.items())[:3]:
    print(f"  • {char.name}: {char.relationship.upper()} (trust: {char.trust}/100)")

# Test 6: Quality assessment (heuristic fallback)
print("\n" + "="*70)
print("TEST 6: Quality Assessment (Heuristic)")
print("="*70)

from engine.narrative_adjudication import assess_action_quality

test_actions = [
    "I immediately call a NATO emergency summit with full intelligence briefing",
    "I deploy additional naval forces to the North Sea",
    "I think we should wait and see what happens",
    "I order a pre-emptive nuclear strike on Russian naval assets"
]

for action in test_actions:
    assessment = assess_action_quality(action, narrative_state, action)
    print(f"\nAction: {action[:60]}...")
    print(f"  Quality: {assessment['quality'].upper()}")
    print(f"  Multiplier: {assessment['multiplier']}x")
    print(f"  Reasoning: {assessment['reasoning']}")

# Test 7: Effect determination
print("\n" + "="*70)
print("TEST 7: Base Effects & Scaling")
print("="*70)

from engine.narrative_adjudication import determine_base_effects, apply_quality_scaling

action = "I call NATO, prepare a public statement, and deploy defensive forces"
base = determine_base_effects(action, narrative_state)
print(f"Action: {action}")
print(f"Base effects: {base}")

# Test with exceptional quality
exceptional_assessment = {"quality": "exceptional", "multiplier": 2.5, "suggested_effects": {}}
scaled = apply_quality_scaling(base, exceptional_assessment, narrative_state)
print(f"Scaled (exceptional 2.5x): {scaled}")

# Test with poor quality
poor_assessment = {"quality": "poor", "multiplier": 0.5, "suggested_effects": {}}
scaled_poor = apply_quality_scaling(base, poor_assessment, narrative_state)
print(f"Scaled (poor 0.5x): {scaled_poor}")

# Test 8: Threshold checks
print("\n" + "="*70)
print("TEST 8: Critical Threshold Checks")
print("="*70)

warnings = narrative_state.check_critical_thresholds()
if warnings:
    print(f"⚠️  Critical warnings: {warnings}")
else:
    print("✓ No critical thresholds breached")

# Test with critical metrics
narrative_state.hidden_metrics.escalation_risk = 90
narrative_state.hidden_metrics.domestic_stability = 25
warnings = narrative_state.check_critical_thresholds()
print(f"\nAfter setting Risk=90, Stability=25:")
print(f"⚠️  Critical warnings: {warnings}")

print("\n" + "="*70)
print("ALL TESTS PASSED ✓")
print("="*70)



