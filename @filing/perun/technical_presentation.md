# Inside the Cross-Domain Command Wargame (2025) — Technical Documentation

**Speaker:** Perun (Independent Defence Analyst)
**Event:** NATO Allied Command Transformation — Cross Domain Command Concept Wargame
**Date:** 2025-10-21
**Technical Domain:** Military wargaming, multi-domain operations (MDO), command and control (C2), cyber/EW, space
**Audience Level:** Intermediate–Advanced
**Duration:** 01:04:33

## Technical Overview
This document transforms the presentation “I Wargamed with NATO — Inside the Cross-Domain Command Wargame (2025)” into implementable technical documentation. It captures scenario architecture, procedures, artefacts, and reproducible workflows for running and analysing a CDC (Cross-Domain Command) discovery wargame using a modified grand-tactical tabletop engine with digital adjudication and observer instrumentation.

Objectives covered:
- Explore CDC structures vs traditional command, with four decentralised multi-domain teams and a light-touch HQ.
- Measure effects of cyber/EW, space, and civilian “grey cell” integration on action economy, ISR and fires.
- Observe trust, friction, and coordination behaviours under time pressure and incomplete information.

---

## Prerequisites
### Required Knowledge
- Fundamentals of wargame design (objectives, adjudication, fog-of-war, initiative)
- Multi-Domain Operations, joint fires, ISR, air and missile defence basics
- Intro to cyber/EW effects on C2 and precision strike workflows

### Required Tools/Software
- Modified “Littoral Commander”-style hex grand-tactical engine (tabletop core + digital tracker)
- Dice: D20; action-point tracker; card decks for cyber/EW/space/civil options
- Observer instrumentation: influence meter (−10 … +10), decision logs, timeline capture

### System Requirements
- Room with central map table, two team areas (Blue/Red), umpire station, observer area
- Displays for digital COP (common operating picture) and timeline timer per turn

---

## Section 1: Wargaming Fundamentals and Study Design (00:00–14:00)

### Core Concepts
- **Discovery Wargame:** Optimised to learn about behaviours and structures rather than solely to train or win.
- **CDC vs Traditional Command:** Four semi-autonomous multi-domain teams under a light HQ vs Red’s single commander model.
- **Action Economy:** Finite action points (AP) to activate units/effects; key to trade-offs across domains.

### Technical Implementation
#### Step 1: Define Objectives and Measures (timestamp: 00:10)
- Study goals: observe coordination, trust, resource-sharing, sequencing of cyber/EW with kinetic actions.
- Measures: influence score trajectory, terrain control, attrition, AP efficiency, time-to-synchronise.

#### Step 2: Build Rule Overlays (timestamp: 00:13)
- Overlays add cyber/EW, space, grey-cell, AI liaison, and public opinion mechanics to the tabletop core.
- Cyber/EW cards grant modifiers to network quality and intercept/strike probabilities for limited windows.

---

## Section 2: Scenario and Order of Battle (14:00–29:30)

### Core Concepts
- **Actors:** Blue (Otso, highly capable NATO-style force); Red (Bothnia/De Novia, legacy Soviet/limited PRC kit); Nastria (neutral economic lever).
- **Map:** Hex-based; borders initially tense with limited incursions.
- **Victory Pressures:** Blue to defend cities, resources, restore borders, and blockade De Novia; Red to seize resources, cut sea access, break blockade, shape info space.

### Technical Implementation
#### Step 1: Initialise Forces (timestamp: 00:23)
- Blue OOB includes advanced air (F-35/F-22/B‑2), IADS (Patriot/THAAD), precision fires (HIMARS/ATACMS/PrSM), navy (Burke/DDX, 1× Virginia SSN).
- Red OOB larger in tubes/MLRS, fewer infantry screens; mixed legacy air/naval with select modern nodes.

#### Step 2: Initiative and Pre‑Kinetic Rules (timestamp: 00:26)
- Pre-kinetic phase: manoeuvre + ISR + jamming allowed; no kinetic engagements.
- Establish persistent capabilities: ISR or EW assets with per-turn use while not destroyed/denied.

---

## Section 3: Pre‑Kinetic Phase Procedures (29:30–33:00)

### Core Concepts
- **ISR Saturation vs Restraint:** Both sides may jam ISR but cannot shoot it down pre-kinetic.
- **Blue AP Allocation:** Early emphasis on ISR mapping and repositioning from peacetime posture.

### Technical Implementation
#### Step 1: ISR Laydown and EW Posture (timestamp: 00:30)
- Deploy MPA, satellites, drones; log coverage, blind spots, contested bands.
- Activate persistent EW nodes to complicate Red’s ISR collection.

#### Step 2: Defensive Geometry (timestamp: 00:31)
- Align defensive belts where terrain favours delay/attrition; preserve urban stand-off.
- Decide “hold-border” vs “elastic defence” policies based on political guidance and terrain.

---

## Section 4: Kinetic Phase and Fires Sequencing (33:00–48:00)

### Core Concepts
- **Red Zero-Chill Assault:** Reconnaissance-by-fire; stacked pushes to force Blue to reveal.
- **Blue Absorb-and-Attrit:** Prioritise counter-battery vs heavy MRLs; protect ammunition depth.
- **Naval-Subsurface Duel:** Blue SSN conducts steady high-value kills; Red diesel subs constrained by detection and poor rolls.

### Technical Implementation
#### Step 1: Fires Prioritisation (timestamp: 00:34)
- Target order: heavy MRLs > long-range SPGs > C2 relays > bridging/logistics nodes.
- Use precision windows while intercept odds remain favourable.

#### Step 2: Ammunition Governance (timestamp: 00:33)
- Implement per-mission ammo limits; escalate only to protect urban approaches and critical assets.
- Track resupply feasibility (e.g., ship VLS reload allowances in scenario rules).

#### Step 3: Naval Actions (timestamp: 00:38)
- ASW coverage for surface groups; SSN ambush cycles; deconflict long-range land-attack salvos with air corridors.

---

## Section 5: Cyber/EW and Space Employment (48:00–57:00)

### Core Concepts
- **Theatre-Wide Effects:** Cyber/EW concentrated centrally for stacked probability/impact.
- **Operation “B‑SOD” Pattern:** Build exploit, then mass multiple offensive cyber cards, overlay EW to suppress recovery.

### Technical Implementation
#### Step 1: Build Exploit Window (timestamp: 00:40)
- Acquire exploit via grey-cell cooperation or prior recon; e.g., +4 to cyber success rolls for the turn.

#### Step 2: Execute Combined Cyber/EW (timestamp: 00:42)
- Aim for negative modifiers on Red tactical network (C2), degrading long-range fires and intercepts (e.g., −7 → −4 over recovery).

#### Step 3: Denial/Resilience and Space (timestamp: 00:45)
- Model Red’s Kessler attempt; if debris threshold met, deny space services and force local sensor fighting.
- If failed, prioritise network repair and civilian backhaul (commercial satcom, public platforms) as contingencies.

---

## Section 6: Information Operations and Influence (36:00–46:00)

### Core Concepts
- **Influence Meter:** +10 strongly pro-Blue ↔ −10 collapse of support.
- **Causal Drivers:** Casualty asymmetry, territorial momentum, credible narratives/deepfakes, humanitarian posture.

### Technical Implementation
- Align kinetic timetables with info ops pushes; announce humanitarian corridors; expose adversary escalation.
- Engage Nastria with economic packages to unlock logistics corridors and aid shipments.

---

## Section 7: Observations and Design Tweaks (46:00–end)

### Key Observations
- Officers adapted quickly to team roles; frictions mostly within domains, not between.
- AP sharing for cyber/EW succeeded when effects were explicit; realism would hide some certainty to test trust.
- Red attrition exposed artillery without screens; Blue leveraged precision and SSN advantage.

### Future Design Tweaks
- Reduce fog-of-war at frontline; increase small-UAS availability to mirror modern transparency.
- Allow Red broader civilian comms fallback (e.g., public platforms, commercial satcom) under C2 degradation.
- Increase difficulty: resource scarcity, loss of initiative, surprise domain-denial events.

---

## Complete Code Examples

### Example 1: Turn Resolution Workflow (runnable procedure)
```yaml
turn:
  timer_minutes: 15
  order:
    - blue_initiative: true
    - declare_intents:
        - kinetic: [fires, manoeuvre]
        - non_kinetic: [cyber, EW, space, info]
    - resolve_non_kinetic:
        - apply_exploit_modifiers: true
        - network_effects:
            intercept_modifier: -4  # range -7..0
            fires_modifier: -4      # range -7..0
    - resolve_isr_and_detection:
        - uav_spotting: true
        - mpa_tracks: true
    - resolve_kinetics:
        - counter_battery_first: true
        - urban_proximity_rules: enforced
    - update_influence:
        - casualties: differential
        - territory: delta
        - narratives: queued_events
    - logistics_and_resupply:
        - vls_reload: allowed_by_rule
        - missile_stock: decrement
```

### Example 2: Cyber/EW Operation Playbook
```bash
# 1) Prepare exploit window (abstracted)
export CYBER_WINDOW_MOD=+4

# 2) Queue offensive actions (abstracted cards)
queue cyber:degrade_tactical_network --target=RED_C2 --chance=$((50+CYBER_WINDOW_MOD))
queue cyber:spoof_track_data --target=RED_IADS --chance=$((40+CYBER_WINDOW_MOD))
queue ew:widescan_jam --band=GNSS --sector=east --duration=1_turn

# 3) Execute stack within same turn window
execute --all-queued

# 4) Adjudication effects (example)
apply modifier --to red.intercept_prob --delta -7 --duration 1_turn
apply modifier --to red.long_range_fires --delta -7 --duration 1_turn
```

---

## Configuration and Setup

### Environment Setup
```bash
# Tabletop + Digital Adjudication Kit (illustrative)
# Ensure dice, hex map, counters, and cyber/EW/space card decks are available.
# Prepare shared COP (projector/large display) and 15-minute turn timer.
```

### Configuration Files
**cdc_wargame.rules**
```ini
[initiative]
blue_starts=true

[pre_kinetic]
engagement=forbidden
isr_allowed=true
jamming_allowed=true

[cyber_ew]
exploit_stackable=true
max_modifier=-7
recovery_step=+3_per_turn

[space]
kessler_attempt=enabled
threshold=debris_index>=X

[influence]
scale_min=-10
scale_max=+10

[logistics]
vls_reload=allowed_by_umpire
```

### Environment Variables
- `CYBER_WINDOW_MOD`: Temporary bonus to cyber success during exploit window.

---

## Best Practices and Patterns

### Design Patterns Used
1. **Effect Stacking:** Sequence non-kinetic (cyber/EW) to shape kinetic outcomes within a limited window.
   - Implementation: exploit → offensive cyber → theatre EW → precision fires.
2. **Elastic Defence:** Trade space for time to preserve force and civilians; prevent urban encirclement.
3. **Action-Point Budgeting:** Allocate AP to highest marginal effect per turn; re-evaluate after ISR updates.

### Performance Optimisations
1. **Counter-Battery First:** Early removal of heavy MRLs reduces incoming volume disproportionately.
2. **SSN Ambush Cycle:** Repeatable high-value naval attrition with minimal exposure.

### Security Considerations
- Model civilian network use realistically; both sides may route around damage using public/commercial channels.
- Limit perfect certainty of cyber outcomes to encourage cross-domain trust decisions under ambiguity.

---

## Troubleshooting Guide

### Common Issues
**Problem:** Ammunition burn rates spike under pressure.
**Symptoms:** VLS cells and precision stocks deplete in a single turn.
**Solution:** Enforce per-mission ammo caps; reserve precision for windows created by cyber/EW.
**Prevention:** Pre-commit AP to logistics and staggered fires.

**Problem:** Artillery stacks exposed without infantry screens.
**Symptoms:** Cheap close-assault kills against unscreened tubes.
**Solution:** Maintain infantry screens; re-balance Red OOB if used for pedagogy.
**Prevention:** Attrition management and recon before push.

**Problem:** Over-thick fog-of-war reduces ISR realism.
**Symptoms:** Frontline unit identities rarely revealed.
**Solution:** Increase small-UAS density; relax reveal thresholds near FEBA.
**Prevention:** Add per-hex UAS availability and EW counterplay.

### Debugging Tips
- Use decision logs to correlate AP spend with influence swings and attrition changes.
- Snapshot network modifiers each turn to validate cyber/EW timing effects.

### Performance Issues
**Symptom:** Cyber effects feel over-centralised or too deterministic.
**Diagnosis:** Cards disclose exact success and effect magnitudes.
**Resolution:** Replace with bands/estimates and conceal some effect details from non-cyber leads.

---

## Advanced Topics Covered
- **Theatre-wide cyber/EW synergy:** Stacked effects on intercept and strike probability.
- **Space denial scenarios:** Kessler-style constraints and fallback comms.
- **AP efficiency analysis:** Marginal effect of AP per domain across phases.

---

## Tools and Resources Mentioned
- **Wargame Engine:** Modified “Littoral Commander” grand‑tactical core.
- **Facilitator:** Radius Defence (umpire/administration).
- **Civil/Defence Tech:** Commercial satellite imagery and satcom; big‑tech cyber defence/monitoring partnerships.

---

## Implementation Checklist
- [ ] Define discovery objectives and data capture plan
- [ ] Configure overlays for cyber/EW, space, grey cell, influence meter
- [ ] Validate OOB balance and small-UAS density
- [ ] Rehearse pre‑kinetic ISR/jam sequencing and timers
- [ ] Set AP budgets and ammunition caps by phase
- [ ] Dry-run Operation B‑SOD timing and adjudication
- [ ] Prepare humanitarian/PR injects and Nastria economic levers
- [ ] Agree domain-denial curveballs and recovery mechanics

---

## Next Steps and Further Learning
### Immediate Practice
- Run a short scenario variant with reduced fog-of-war and ubiquitous small-UAS.
- Re-run with successful space denial to test CDC resilience.

### Advanced Topics to Explore
- Cross-functional AP auctions for contested turns.
- Data-driven tuning of cyber/EW effect sizes from prior runs.

### Community and Support
- NATO wargaming handbooks; professional wargaming communities and journals.

---

## Technical Appendices

### Appendix A: Network Modifier Reference
- Intercept modifier: 0 (normal), −4 (degraded), −7 (severely degraded)
- Long-range fires modifier: mirroring ranges above
- Recovery: +3 per turn unless additional cyber/EW applied

### Appendix B: Influence Meter Drivers
- Casualty differential, territorial change, narrative events, humanitarian posture
- Thresholds for external support triggers should be defined pre-game

### Appendix C: Timing Template
```text
T-05: Intent declarations complete
T-12: Non-kinetic adjudication window
T-08: ISR detection updates
T-06: Kinetic fires sequencing freeze
T-00: Turn close; capture measures; logistics tick
```

---

## Speaker Notes
- **Expertise Level:** High; balanced historical grounding and modern system insight
- **Teaching Style:** Narrative with embedded technical detail and scenario instrumentation
- **Technical Accuracy:** High; suitable for discovery wargame design and CDC observation


