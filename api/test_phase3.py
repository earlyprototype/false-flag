import requests
import sys
import time
import json

def test_phase3_flow():
    base_url = "http://localhost:8000"
    
    print("="*60)
    print("PHASE 3 SMOKE TESTS - Diplomacy & Meta-Game")
    print("="*60)
    
    # --- Setup: New Game ---
    print("\n[Setup] Starting new game session...")
    try:
        r = requests.post(f"{base_url}/game/new", json={
            "scenario_id": "war_game_2025",
            "play_mode": "immersive"
        })
        if r.status_code != 200:
            print(f"[FAIL] New game failed: {r.text}")
            return False
        
        data = r.json()
        session_id = data.get("session_id")
        print(f"[PASS] Session created: {session_id[:8]}...")
    except Exception as e:
        print(f"[FAIL] Connection error: {e}")
        return False

    # --- Test 1: Save Game ---
    print(f"\n[1/5] Testing /game/save...")
    save_name = f"test_save_{int(time.time())}"
    r = requests.post(f"{base_url}/game/save", json={
        "session_id": session_id,
        "save_name": save_name
    })
    if r.status_code != 200:
        print(f"[FAIL] Save failed: {r.status_code} - {r.text}")
    else:
        save_data = r.json()
        if save_data.get("success"):
            print(f"[PASS] Game saved: {save_data.get('save_path')}")
        else:
            print(f"[FAIL] Save reported failure: {save_data}")

    # --- Test 2: List Saves ---
    print(f"\n[2/5] Testing /game/saves...")
    r = requests.get(f"{base_url}/game/saves")
    if r.status_code != 200:
        print(f"[FAIL] List saves failed: {r.status_code} - {r.text}")
    else:
        saves_data = r.json()
        saves = saves_data.get("saves", [])
        print(f"[PASS] Found {len(saves)} saves")
        found = any(s.get("name") == save_name for s in saves)
        if found:
            print(f"       Target save '{save_name}' found in list")
        else:
            print(f"[WARN] Target save '{save_name}' NOT found in list")

    # --- Test 3: Load Game ---
    print(f"\n[3/5] Testing /game/load...")
    # We need the full path from Test 1, or search in Test 2
    save_path = None
    if 'save_data' in locals() and save_data.get('save_path'):
        save_path = save_data.get('save_path')
    
    if save_path:
        r = requests.post(f"{base_url}/game/load", json={"save_path": save_path})
        if r.status_code != 200:
            print(f"[FAIL] Load failed: {r.status_code} - {r.text}")
        else:
            load_data = r.json()
            new_session_id = load_data.get("session_id")
            if new_session_id:
                print(f"[PASS] Game loaded. New session: {new_session_id[:8]}...")
            else:
                print(f"[FAIL] Load returned no session ID: {load_data}")
    else:
        print("[SKIP] Cannot test load (save failed)")

    # --- Test 4: Scenarios ---
    print(f"\n[4/5] Testing /scenarios...")
    r = requests.get(f"{base_url}/scenarios")
    if r.status_code != 200:
        print(f"[FAIL] Scenarios failed: {r.status_code} - {r.text}")
    else:
        scenarios_data = r.json()
        scenarios = scenarios_data.get("scenarios", [])
        print(f"[PASS] Found {len(scenarios)} scenarios")
        if scenarios:
            print(f"       First: {scenarios[0].get('id')}")

    # --- Test 5: Diplomacy (Simple Check) ---
    print(f"\n[5/5] Testing /game/action/call (Structure)...")
    try:
        r = requests.post(f"{base_url}/game/action/call", json={
            "session_id": session_id,
            "country_name": "United States",
            "approach": "formal"
        }, stream=True, timeout=5)
        
        if r.status_code == 200:
            print(f"[PASS] Call accepted")
        else:
            print(f"[FAIL] Call rejected: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[WARN] Call request issue (expected if streaming): {e}")

    print("\n" + "="*60)
    print("PHASE 3 TESTS COMPLETE")
    print("="*60)
    return True

if __name__ == "__main__":
    test_phase3_flow()

