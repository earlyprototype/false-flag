import requests
import sys

def test_diplomacy_flow():
    base_url = "http://localhost:8000"
    print("="*60)
    print("PHASE 3 SMOKE TESTS - Diplomacy")
    print("="*60)

    # 1. Setup
    print("\n[Setup] Starting new game session...")
    try:
        r = requests.post(f"{base_url}/game/new", json={"scenario_id": "war_game_2025"})
        if r.status_code != 200: 
            print(f"[FAIL] New game failed: {r.text}")
            return False
        session_id = r.json()["session_id"]
        print(f"[PASS] Session: {session_id}")
    except Exception as e:
        print(f"[FAIL] Connection error: {e}")
        return False

    # 2. Initiate Call (e.g., to USA)
    print("\n[1/3] Initiating call to USA...")
    r = requests.post(f"{base_url}/game/action/call", json={
        "session_id": session_id,
        "country_name": "US"
    })
    if r.status_code != 200:
        print(f"[FAIL] Call init failed: {r.status_code} - {r.text}")
    else:
        data = r.json()
        if "transcript" in data and len(data["transcript"]) > 0:
            print(f"[PASS] Call started. Opening: {data['transcript'][-1]}")
        else:
            print(f"[FAIL] No transcript returned: {data}")

    # 3. Send Reply
    print("\n[2/3] Sending reply...")
    r = requests.post(f"{base_url}/game/action/diplomacy/reply", json={
        "session_id": session_id,
        "message": "We need your immediate support in the North Atlantic."
    })
    if r.status_code != 200:
        print(f"[FAIL] Reply failed: {r.status_code} - {r.text}")
    else:
        data = r.json()
        if "transcript" in data:
            # Print the last line which should be the counterpart response
            print(f"[PASS] Reply processed. Response len: {len(data['transcript'])}")
        else:
            print(f"[FAIL] No transcript in reply")

    # 4. End Call
    print("\n[3/3] Ending call...")
    r = requests.post(f"{base_url}/game/action/diplomacy/reply", json={
        "session_id": session_id,
        "message": "Thank you, we will be in touch through official channels."
    })
    if r.status_code != 200:
        print(f"[FAIL] End call failed: {r.status_code} - {r.text}")
    else:
        data = r.json()
        print(f"[PASS] Call ended. Data keys: {list(data.keys())}")
        if "outcome" in data:
            print(f"       Outcome: {data['outcome']}")

    print("\n" + "="*60)
    return True

if __name__ == "__main__":
    test_diplomacy_flow()

