import requests
import json

base_url = "http://localhost:8011"

# 1. Create Session
print("Creating session...")
r = requests.post(f"{base_url}/game/new", json={"scenario_id": "war_game_2025"})
session_id = r.json()["session_id"]
print(f"Session: {session_id}")

# 1.5 Ack Briefing
print("Ack briefing...")
r = requests.post(f"{base_url}/game/{session_id}/briefing/ack")
print(f"Ack status: {r.status_code}")

# 2. Call Interpret
print("Calling interpret...")
r = requests.post(f"{base_url}/game/decision/interpret", json={
    "session_id": session_id,
    "action_text": "Deploy forces"
})

print(f"Status: {r.status_code}")
print(f"Response: {r.text}")

