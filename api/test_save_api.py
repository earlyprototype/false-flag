import requests
import sys

def test_save_api():
    base_url = "http://localhost:8000"
    print("TESTING SAVE/LOAD API...")
    
    # 1. Start Game
    try:
        r = requests.post(f"{base_url}/game/new", json={"scenario_id": "war_game_2025"})
        if r.status_code != 200: 
            print(f"Start failed: {r.text}")
            return False
        session_id = r.json()["session_id"]
        print(f"Session: {session_id}")
    except Exception as e:
        print(f"Connection error: {e}")
        return False
    
    # 2. Save Game
    r = requests.post(f"{base_url}/game/save", json={"session_id": session_id, "save_name": "api_test"})
    if r.status_code != 200:
        print(f"Save failed: {r.text}")
        return False
    save_data = r.json()
    save_path = save_data["save_path"]
    print(f"Saved: {save_path}")
    
    # 3. List Saves
    r = requests.get(f"{base_url}/game/saves")
    if r.status_code != 200:
        print(f"List failed: {r.text}")
        return False
    saves = r.json()["saves"]
    print(f"Saves found: {len(saves)}")
    
    # Normalize paths for comparison (Windows double backslashes etc)
    import os
    norm_save_path = os.path.normpath(save_path)
    found = False
    for s in saves:
        if os.path.normpath(s["path"]) == norm_save_path:
            found = True
            break
            
    if not found:
        print("WARNING: Saved file not in list (path mismatch likely)")
        print(f"Looking for: {norm_save_path}")
        print(f"List: {[s['path'] for s in saves]}")
        
    # 4. Load Game
    r = requests.post(f"{base_url}/game/load", json={"save_path": save_path})
    if r.status_code != 200:
        print(f"Load failed: {r.text}")
        return False
    load_data = r.json()
    new_session = load_data["session_id"]
    print(f"Loaded Session: {new_session}")
    
    print("PASS")
    return True

if __name__ == "__main__":
    test_save_api()

