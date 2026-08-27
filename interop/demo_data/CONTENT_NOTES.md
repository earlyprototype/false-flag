# Content notes — demo run for the dashboard visual

Run: `war_game_2025` (standard variant), seed 42, 10 turns, deterministic mock
driver, emergent play mode. Scripted episodes cover turns 1–6; turns 7–10 are
engine-generated. The run ends on turn 10 with the terminal defeat ending
**THE GUNS OF OCTOBER** (escalation_risk reached 100). All figures below
reconcile with `dashboard_pack.json`. Speakers are roles only — the game uses
no personal names.

## Turn by turn (from the transcript)

- **T+0 baseline** — the crisis opens already hot: two F-35 pilots found dead in Norfolk, sabotage suspected; escalation_risk 60, domestic_stability 50, alliance_cohesion 40, 2 military casualties on the board.
- **T1 · briefing (scripted)** — COBRA convenes over 48 hours of hostile incidents; the PM opens a direct diplomatic channel to Moscow and informs NATO allies first (alliance_cohesion +8).
- **T2 · intelligence (scripted)** — a Russian submarine surfaces near UK waters; the PM deploys the carrier strike group to shadow it, overriding pushback from the Chief of the Defence Staff — the run's first trust cost.
- **T3 · emergency (scripted)** — major explosion at Drax power station (~6% of UK electricity): first civilian casualties (0 → 6); the PM convenes the North Atlantic Council under Article 4 and holds the deployment.
- **T4 · diplomatic (scripted)** — emergency NATO consultation under Article 4; the PM authorises defensive patrols only and orders an Attorney General review of the legal basis — the only turn where escalation_risk barely moves.
- **T5 · emergency (scripted)** — ballistic missile launch detected by RAF Fylingdales from a Russian submarine in the Norwegian Sea, 8–12 minutes to potential impact, assessed as a single missile (attack, test, or deliberate near-miss all live options); the PM raises readiness across home commands; alliance_cohesion jumps +13.
- **T6 · briefing (scripted, last scripted turn)** — Washington demands coordination; a mandatory secure call from the US President interrupts the turn — assets offered, but no commitment "to a shooting war on ambiguous intelligence"; the PM restates the NATO-first line; cohesion climbs to 78 while domestic_stability slides to 30.
- **T7 · flash_alert (emergent from here on)** — Moscow delivers a public ultimatum (Royal Navy to withdraw beyond the 62nd parallel, "support for terrorism" to cease); the PM re-deploys the carrier group, again over CDS objection — second trust cost; escalation_risk 94.
- **T8 · diplomatic (emergent)** — Berlin, with Hungary and Slovakia, breaks ranks on the sanctions energy annex ("without it the package is a travel ban and a list of names"); the PM convenes the NAC again to hold the alliance line.
- **T9 · emergency (emergent)** — ransomware locks six NHS acute trusts in the North West with no ransom demand; NCSC attributes the tooling to a crew long tolerated on Russian territory; the PM keeps to defensive patrols plus legal review; domestic_stability down to 19.
- **T10 · flash_alert (emergent, ending)** — an RAF Typhoon on Quick Reaction Alert is down in the North Sea, last transmission the single word "engaged", a Russian Su-35 inside two miles; military casualties tick to 3, escalation_risk hits 100 and the campaign terminates: **THE GUNS OF OCTOBER — defeat** ("the escalation spiral has passed the point of no return").

## Arc and instrumentation notes for captioning

- **Metric arc**: escalation_risk climbs monotonically 60 → 100; domestic_stability collapses 50 → 15; alliance_cohesion rises 40 → 93 — the decision loop buys allies, not calm. Casualties: civilian 0 → 7 (Drax), military 2 → 3 (Typhoon).
- **Trust economy**: the only two pushback events are the carrier deployments (T2, T7), both committed unamended — the Chief of the Defence Staff pays the override cost twice (trust 80 → 78); the Attorney General's relationship warms neutral → allied across the legal-review decisions.
- **Scripted/emergent seam**: after T6 the inject ids switch from authored episode ids (`turn_001_cobra_briefing` …) to generated `turn_007_inject` …, and the `flash_alert` channel appears only in the emergent phase.
- **Mock-driver flatness**: all 10 quality verdicts are "adequate" and interpretation text is templated — expected from the deterministic mock driver; caption metric movement and the trust/pushback events, not decision-prose nuance.
