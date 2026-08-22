# Episode Injects - False Flag: The Wargame

This directory contains turn-by-turn injects (events) for the wargame scenario.

## Current Episodes

### ✅ Turn 1: COBRA Emergency Meeting (17:00)
**Source:** Podcast Episode 1 transcript (re-paced 2026-08: the briefing covers the fleet detection alone)  
**Key Events:**
- NSA briefs the Northern Fleet deployment: 15 Russian submarines (7 ballistic missile, 8 attack) with escorts, out of Kola Bay and heading for the GIUK gap
- Moscow silent — no exercise notification; the deployment "was made to be found"
- NSC preliminary assessment: a deliberate test of UK and NATO resolve
- The other pre-game threads (Norfolk murders, Severomorsk accusation, cyber spike, diplomatic exodus) stay knowable via advisors but are no longer pushed here

*Fast start:* same fleet briefing, then the Orkney surfacing arrives as a breaking update carrying the turn-2 beats.

### ✅ Turn 2: Submarine Provocation (19:00)
**Source:** Extrapolated from wargame patterns  
**Key Events:**
- Russian Kilo-class submarine surfaces 12 nautical miles off the Orkney Islands
- Witnessed by MV Hamnavoe ferry passengers; photos and videos spread on social media
- Panic buying begins in northern Scotland
- Home Secretary connects the two F-35 pilots murdered in Norfolk to the crisis — special-forces tradecraft on British soil
- Foreign Secretary: Russian Ambassador refuses meeting; Moscow state media accuses the UK of the Severomorsk attack; diplomat families flying out of Heathrow

*Fast start:* these beats are folded into turn 1's breaking update.

### ✅ Turn 3: Infrastructure Attack (21:00)
**Source:** Extrapolated from wargame patterns  
**Key Events:**
- Drax Power Station explosion (sabotage suspected)
- 2 million homes without power
- 5-8 civilian casualties
- GCHQ reframes the week-long 65% cyber-attack spike as the run-up, with operative communications intercepted 30 minutes before the blast
- Debate over BIKINI BLACK SPECIAL readiness and grounds for invoking NATO Article 5

*Fast start:* lands in turn 2 (fast), combined with the NATO consultation and the US National Security Advisor call.

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
channel: briefing|intelligence|emergency|diplomatic|flash_alert
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

