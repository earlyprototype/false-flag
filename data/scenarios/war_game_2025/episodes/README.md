# Episode Injects - False Flag: The Wargame

This directory contains turn-by-turn injects (events) for the wargame scenario.

## Current Episodes

### ✅ Turn 1: COBRA Emergency Meeting (17:00)
**Source:** Podcast Episode 1 transcript  
**Key Events:**
- Initial briefing on Russian false flag accusations
- Two F-35 pilots murdered in Norfolk
- Russian naval exercise (15 submarines) in North Atlantic
- Cyber attacks increased 65%
- Russian diplomatic staff departing UK
- Infrastructure attacks (railways, ferries)

### ✅ Turn 2: Submarine Provocation (19:00)
**Source:** Extrapolated from wargame patterns  
**Key Events:**
- Russian submarine surfaces near Orkney Islands
- Witnessed by civilian ferry passengers
- Photos spreading on social media
- Public panic buying begins
- Russian Ambassador refuses meeting

### ✅ Turn 3: Infrastructure Attack (21:00)
**Source:** Extrapolated from wargame patterns  
**Key Events:**
- Drax Power Station explosion (sabotage suspected)
- 2 million homes without power
- 5-8 civilian casualties
- GCHQ intercepts suspicious communications
- Debate over invoking NATO Article 5

### ✅ Turn 4: NATO Consultation (00:00 - Midnight)
**Source:** Extrapolated from wargame patterns  
**Key Events:**
- Emergency NATO Article 4 consultation
- US expresses doubt, wants more proof
- France urges caution
- Poland supports strong action
- Germany urges diplomatic solution
- Alliance fracturing becomes apparent

### ✅ Turn 5: Missile Launch (03:00)
**Source:** Extrapolated from wargame patterns  
**Key Events:**
- Ballistic missile launch detected
- 8-12 minutes to potential UK impact
- Trajectory analysis: deliberate near-miss (North Sea)
- Critical decision point: how to respond?
- Escalation reaches peak

## Planned Episodes (Awaiting Podcast Transcripts)

### 🔄 Turn 6+: TBD
Awaiting transcripts from Podcast Episodes 2-6 to create canonical injects based on the actual wargame progression.

## Inject Structure

Each inject YAML file contains:

```yaml
id: unique_identifier
title: "Short Title"
description: |
  Full briefing text with:
  - Situation update
  - Advisor assessments
  - Decision prompts
channel: intelligence|emergency|diplomatic|military
effects:
  - metric: metric_name
    delta: min..max  # Range of effect on game metrics
```

## Adding New Injects

1. Create `turn_NNN.yaml` with zero-padded turn number
2. Follow the structure above
3. Include advisor perspectives (CDS, NSA, Foreign Secretary, etc.)
4. Define metric effects (escalation_risk, domestic_stability, etc.)
5. End with a clear decision prompt

## Notes

- Turns 1-5 provide approximately 10 hours of crisis time
- Each turn represents roughly 2 hours of game time
- Injects escalate from diplomatic provocation to near-military conflict
- Player decisions should meaningfully affect subsequent injects (via LLM generation or branching)

