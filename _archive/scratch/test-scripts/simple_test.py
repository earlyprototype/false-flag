"""Simple test"""
import sys
sys.path.insert(0, '.')

try:
    print("Starting test...")
    from models.narrative_state import create_initial_narrative_state
    from models.world import Metrics
    
    print("Imports successful")
    
    metrics = Metrics(
        escalation_risk=75,
        domestic_stability=42,
        alliance_cohesion=35,
        casualties_mil=2,
        casualties_civ=8
    )
    
    print("Metrics created")
    
    ns = create_initial_narrative_state(metrics)
    
    print(f"SUCCESS: Narrative state created with {len(ns.characters)} characters")
    print(f"Play mode: {ns.play_mode}")
    print(f"Hidden risk: {ns.hidden_metrics.escalation_risk}")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()



