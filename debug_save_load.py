import sys
import os
import shutil

# Add project root to path
sys.path.append(os.getcwd())

from engine.game_manager import GameManager

def test_save_load():
    print("Testing Save/Load...")
    
    # 1. Create and modify state
    try:
        gm = GameManager()
        print(f"Initial Turn: {gm.world.turn}")
    except Exception as e:
        print(f"Init failed: {e}")
        return

    gm.world.turn = 5
    gm.world.metrics.escalation_risk = 99
    gm.transcript.append("Test line")
    
    if gm.world.actor_system:
        # Assuming 'RUS' exists
        if "RUS" in gm.world.actor_system.actors:
            gm.world.actor_system.actors["RUS"].relationship_uk = 10
            print("Modified RUS relationship to 10")
        else:
            print("RUS actor not found")

    # 2. Save
    try:
        save_path = gm.save_game("test_save_debug")
        print(f"Saved to {save_path}")
    except Exception as e:
        print(f"Save failed: {e}")
        import traceback; traceback.print_exc()
        return

    # 3. Load
    try:
        gm2 = GameManager.load_game(save_path)
        print(f"Loaded Turn: {gm2.world.turn}")
    except Exception as e:
        print(f"Load failed: {e}")
        import traceback; traceback.print_exc()
        return
    
    # 4. Verify
    assert gm2.world.turn == 5, f"Turn mismatch: {gm2.world.turn}"
    assert gm2.world.metrics.escalation_risk == 99, f"Metric mismatch: {gm2.world.metrics.escalation_risk}"
    assert "Test line" in gm2.transcript, "Transcript mismatch"
    
    if gm2.world.actor_system and "RUS" in gm2.world.actor_system.actors:
        rel = gm2.world.actor_system.actors["RUS"].relationship_uk
        print(f"Loaded RUS relationship: {rel}")
        assert rel == 10, f"Relationship mismatch: {rel}"
    
    print("PASS")
    
    # Clean up
    try:
        os.remove(save_path)
        print("Cleaned up save file.")
    except:
        pass

if __name__ == "__main__":
    test_save_load()

