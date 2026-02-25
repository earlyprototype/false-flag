
import requests
import sys
import time

def test_api_flow():
    base_url = "http://localhost:8000"
    
    print("="*60)
    print("PHASE 0 SMOKE TESTS - Backend Contract Validation")
    print("="*60)
    
    # --- Test 1: Health Check ---
    print("\n[1/5] Checking API health...")
    try:
        r = requests.get(f"{base_url}/health")
        if r.status_code != 200:
            print(f"[FAIL] Status: {r.status_code}")
            return False
        health = r.json()
        print(f"[PASS] Health check OK. Active sessions: {health.get('sessions_active', 0)}")
    except Exception as e:
        print(f"[FAIL] Could not connect to server: {e}")
        print("   Make sure to run 'uvicorn api.server:app --port 8007' in a separate terminal.")
        return False

    # --- Test 2: New Game Session ---
    print("\n[2/5] Starting new game session...")
    r = requests.post(f"{base_url}/game/new", json={
        "scenario_id": "war_game_2025",
        "play_mode": "immersive"
    })
    if r.status_code != 200:
        print(f"[FAIL] New game failed: {r.text}")
        return False
    
    data = r.json()
    session_id = data.get("session_id")
    if not session_id:
        print("[FAIL] Missing session_id in response")
        return False
    
    print(f"[PASS] Session created: {session_id[:8]}...")
    print(f"  Turn: {data['turn']}, Phase: {data['phase']}")
    print(f"  Metrics: Risk={data['metrics'].get('escalation_risk')}, Cohesion={data['metrics'].get('alliance_cohesion')}")

    # --- Test 3: Resources Endpoint ---
    print(f"\n[3/5] Fetching resources from /game/{session_id[:8]}.../resources...")
    r = requests.get(f"{base_url}/game/{session_id}/resources")
    if r.status_code != 200:
        print(f"[FAIL] Resources fetch failed: {r.status_code}")
        return False
    
    resources = r.json()
    
    # Validate Phase 0 contract
    if "forces" not in resources or "stockpiles" not in resources:
        print(f"[FAIL] Missing 'forces' or 'stockpiles' keys in response")
        print(f"       Got: {list(resources.keys())}")
        return False
    
    forces = resources["forces"]
    stockpiles = resources["stockpiles"]
    
    if not isinstance(forces, list):
        print(f"[FAIL] 'forces' should be a list, got {type(forces)}")
        return False
    
    if not isinstance(stockpiles, list):
        print(f"[FAIL] 'stockpiles' should be a list, got {type(stockpiles)}")
        return False
    
    print(f"[PASS] Resources contract valid:")
    print(f"  Forces: {len(forces)} units")
    print(f"  Stockpiles: {len(stockpiles)} items")
    
    # Sample first force unit structure
    if forces:
        sample = forces[0]
        required_keys = ["id", "branch"]
        missing = [k for k in required_keys if k not in sample]
        if missing:
            print(f"[FAIL] Force unit missing required keys: {missing}")
            return False
        print(f"  Sample force: {sample.get('id')} ({sample.get('branch')})")
    
    # Sample first stockpile item
    if stockpiles:
        sample = stockpiles[0]
        required_keys = ["category", "name", "count"]
        missing = [k for k in required_keys if k not in sample]
        if missing:
            print(f"[FAIL] Stockpile item missing required keys: {missing}")
            return False
        print(f"  Sample stockpile: {sample.get('category')}/{sample.get('name')} = {sample.get('count')}")

    # --- Test 4: Diplomacy Contacts ---
    print(f"\n[4/5] Fetching diplomacy contacts from /game/{session_id[:8]}.../diplomacy/contacts...")
    r = requests.get(f"{base_url}/game/{session_id}/diplomacy/contacts")
    if r.status_code != 200:
        print(f"[FAIL] Contacts fetch failed: {r.status_code}")
        return False
    
    contacts = r.json()
    
    if not isinstance(contacts, list):
        print(f"[FAIL] Contacts should be a list, got {type(contacts)}")
        return False
    
    print(f"[PASS] Diplomacy contacts contract valid:")
    print(f"  Contacts: {len(contacts)} available")
    
    if contacts:
        sample = contacts[0]
        required_keys = ["country_code", "access_level"]
        missing = [k for k in required_keys if k not in sample]
        if missing:
            print(f"[FAIL] Contact missing required keys: {missing}")
            return False
        print(f"  Sample contact: {sample.get('country_code')} ({sample.get('access_level')})")

    # --- Test 5: Diplomatic Call ---
    print(f"\n[5/7] Testing diplomatic call endpoint...")
    if contacts:
        test_country = contacts[0].get("country_code")
        r = requests.post(f"{base_url}/game/action/call", json={
            "session_id": session_id,
            "country_name": test_country
        })
        if r.status_code != 200:
            print(f"[FAIL] Call failed: {r.status_code}")
            return False
        
        result = r.json()
        if result.get("status") != "processed":
            print(f"[FAIL] Unexpected call response: {result}")
            return False
        
        print(f"[PASS] Diplomatic call to {test_country} processed successfully")
    else:
        print("[SKIP] No contacts available")

    # --- Test 6: Decision Interpretation ---
    print(f"\n[6/7] Testing decision interpretation...")
    r = requests.post(f"{base_url}/game/decision/interpret", json={
        "session_id": session_id,
        "action_text": "Deploy HMS Queen Elizabeth to the North Sea"
    })
    if r.status_code != 200:
        print(f"[FAIL] Interpret failed: {r.status_code}")
        return False
    
    interpret_data = r.json()
    if "interpretation" not in interpret_data or "critical_concerns" not in interpret_data:
        print(f"[FAIL] Missing interpretation fields. Got: {list(interpret_data.keys())}")
        return False
    
    print(f"[PASS] Interpretation received:")
    print(f"  Summary length: {len(interpret_data['interpretation'])}")
    print(f"  Concerns: {len(interpret_data['critical_concerns'])}")

    # --- Test 7: Decision Commit ---
    print(f"\n[7/7] Testing decision commit...")
    r = requests.post(f"{base_url}/game/decision/commit", json={
        "session_id": session_id,
        "action_text": "Deploy HMS Queen Elizabeth to the North Sea",
        "user_choice": "confirm"
    })
    if r.status_code != 200:
        print(f"[FAIL] Commit failed: {r.status_code}")
        return False
        
    commit_data = r.json()
    if commit_data.get("status") != "processed":
        print(f"[FAIL] Unexpected commit response: {commit_data}")
        return False
    
    print(f"[PASS] Decision committed successfully")

    print("\n" + "="*60)
    print("[PASS] ALL PHASE 1 SMOKE TESTS PASSED")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_api_flow()
    sys.exit(0 if success else 1)

