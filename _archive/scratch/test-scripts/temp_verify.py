import json

with open('saves/war_game_2025_autosave.json', 'r') as f:
    data = json.load(f)

print("=== SAVE FILE VERIFICATION ===\n")
print(f"Turn: {data['world']['turn']}")
print(f"Phase: {data['world']['phase']}")

metrics = data['world']['metrics']
print(f"\nCurrent Metrics:")
print(f"  Escalation Risk: {metrics['escalation_risk']}")
print(f"  Alliance Cohesion: {metrics['alliance_cohesion']}")
print(f"  Domestic Stability: {metrics['domestic_stability']}")

# Check advisors
advisors = data['world']['advisors']
print(f"\nAdvisors ({len(advisors)} total):")
for adv in advisors:
    print(f"  {adv['name']}: Attitude {adv['attitude']}")

# Check transcript
transcript = data.get('transcript', [])
print(f"\nTranscript Entries: {len(transcript)}")

# Look for nuclear-related entries
nuclear_mentions = 0
for i, entry in enumerate(transcript):
    content = str(entry).lower()
    if 'nuclear' in content or 'kaliningrad' in content or 'moscow' in content:
        nuclear_mentions += 1

print(f"Nuclear-related transcript entries: {nuclear_mentions}")

# Check for cabinet firing
cabinet_fire_mentions = 0
for entry in transcript:
    content = str(entry).lower()
    if 'fire' in content and ('cabinet' in content or 'staff' in content or 'advisor' in content):
        cabinet_fire_mentions += 1

print(f"Cabinet/staff firing mentions: {cabinet_fire_mentions}")

