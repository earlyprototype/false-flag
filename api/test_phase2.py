import requests
import sys
import time

def test_phase2_flow():
    base_url = "http://localhost:8000"
    
    print("="*60)
    print("PHASE 2 SMOKE TESTS - Deep State & Intel")
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

    # --- Test 1: Vibes Endpoint ---
    print(f"\n[1/5] Testing /state/vibes...")
    r = requests.get(f"{base_url}/game/{session_id}/state/vibes")
    if r.status_code != 200:
        print(f"[FAIL] Vibes fetch failed: {r.status_code} - {r.text}")
    else:
        vibes_data = r.json()

    # --- Test 2: Advisors Endpoint ---
    print(f"\n[2/5] Testing /state/advisors...")
    r = requests.get(f"{base_url}/game/{session_id}/state/advisors")
    if r.status_code != 200:
        print(f"[FAIL] Advisors fetch failed: {r.status_code} - {r.text}")
    else:
        advisors_data = r.json()

    # --- Test 3: Flags Endpoint ---
    print(f"\n[3/5] Testing /state/flags...")
    r = requests.get(f"{base_url}/game/{session_id}/state/flags")
    if r.status_code != 200:
        print(f"[FAIL] Flags fetch failed: {r.status_code} - {r.text}")
    else:
        flags_data = r.json()

    # --- Test 4: Intel List Endpoint ---
    print(f"\n[4/5] Testing /intel...")
    r = requests.get(f"{base_url}/game/{session_id}/intel")
    if r.status_code != 200:
        print(f"[FAIL] Intel list failed: {r.status_code} - {r.text}")
    else:
        intel_data = r.json()

    # --- Test 5: Intel Detail Endpoint ---
    # Pick an actor from the previous list if possible, else guess 'RUS'
    actor_code = "RUS"
    print(f"\n[5/5] Testing /intel/{actor_code}...")
    r = requests.get(f"{base_url}/game/{session_id}/intel/{actor_code}")
    if r.status_code != 200:
        print(f"[FAIL] Intel detail failed: {r.status_code} - {r.text}")
        # Try US just in case RUS is missing
        r = requests.get(f"{base_url}/game/{session_id}/intel/US")
        if r.status_code == 200:
             print("       (Retrying with US... Success)")
    else:
        detail = r.json()
        if "assessment" in detail:
            print(f"[PASS] Assessment received for {detail.get('actor')}")
            print(f"       Confidence: {detail.get('confidence')}")
            print(f"       Keys: {list(detail['assessment'].keys())}")
        else:
            print(f"[FAIL] Invalid detail structure: {list(detail.keys())}")

    print("\n" + "="*60)
    print("PHASE 2 TESTS COMPLETE")
    print("="*60)
    return True

if __name__ == "__main__":
    test_phase2_flow()

