# Manus — Role, Boundaries, and Task Queue

**What Manus is in this build**: an off-branch research and collateral agent. Its outputs enter the repo as *data and documents* (dossiers, tables, drafts) reviewed and committed by the engineering loop — **never as code on the branch**. The repo's golden-file determinism, re-golden commit discipline, bundle-stamp guards, and owner-diff rules make a second autonomous agent in the codebase churn, not progress.

**Hard boundaries**
- No repository write access; no pushes, no PRs. Outputs are pasted/attached back and land via the normal review path.
- No API keys, tokens, or private credentials into its sandbox — treat it as a third-party cloud environment (it is one). The public repo URL is fine.
- Every numeric claim in a dossier must carry a source URL; unsourced figures are discarded on intake.

**Credit state (2026-08-28)**: 60,900 credits (20k grant + 40k migration uptick). Reference points: multi-step research tasks run ~200–500 credits; deep research ~1,000+ ([pricing refs](https://www.lindy.ai/blog/manus-ai-pricing)). **The subscription lapses Sunday 30 Aug** — run one small calibration task first to observe real burn, then **front-load every P1 task before Sunday**. Renewal decision point: renew iff the P1/P2 outputs prove useful *and* M3 collateral (deck, video storyboard) still needs agent hours — judged at milestone D1, not before. Quality is never sacrificed to the credit budget; renewal is the fallback, not a failure.

---

## Priority queue

Run P1s immediately (this weekend), P2s behind them, P3s only with credits to spare or after renewal. Each brief below is written to be pasted into Manus verbatim.

### P1a · Gazetteer QA dossier *(feeds milestone M1 directly; a flagged study prerequisite)*

> Produce a verification table for the following ~30 named locations from a UK/Russia crisis-simulation scenario. For each: name · decimal lat/lon (4 dp) · one-line identification · at least one authoritative source URL (official MOD/RAF/RN pages, national mapping agencies, or Wikipedia with coordinates as a floor) · a confidence flag (HIGH = multiple agreeing sources, CHECK = sources disagree or ambiguous). Locations: London (Whitehall), Portsmouth naval base, Plymouth (Devonport), Faslane (HMNB Clyde), RAF Marham, RNAS Yeovilton, RAF Lossiemouth, RAF Coningsby, RAF Fylingdales, Northwood HQ, GCHQ Cheltenham, Drax power station, St Fergus gas terminal, Heathrow, Oxford Circus, Orkney Islands (Scapa Flow), Aberdeen, Scrabster, Severomorsk, Murmansk — plus sensible centroid definitions (with your method stated) for these areas: UK territorial waters (definition note only), North Atlantic rendezvous area, GIUK gap (three reference points: Greenland–Iceland midline, Iceland–Faroes, Faroes–Shetland). Deliverable: one CSV code block + a short exceptions list of anything ambiguous. Do not invent precision beyond your sources.

**Intake**: cross-check against the repo's three DMS strings (`engine/opening.py`), then author `gazetteer.yaml` with a `source` field per entry.

### P1b · IMR & judging-context brief *(dual-use: competition pitch + interview prep)*

> Build a concise brief (≤2 pages) on Irish Manufacturing Research (imr.ie): the four research pillars with one concrete active project each; everything public about their digital-twin work (REWIRE project scope, any Azure Digital Twins / DTDL usage or partners); their industrial membership model; recent news (last 12 months); named senior technical staff who publish or speak on digital twins or Industry 4.0. Close with: five ways a DTDL-modelled crisis-simulation demo could be framed to resonate with this audience, each tied to a cited IMR activity. Every claim sourced.

### P1c · Competition rubric & logistics hunt

> Find everything published about the 2026 Irish National AI Challenge: official pages, judging criteria/rubric, onsite-day format (live demo length? equipment provided? projector/HDMI specs?), finalist selection process, IP/eligibility terms, past editions and winning entries if any, and press coverage. Deliverable: a findings table with URLs, plus an explicit "not findable publicly" list so we know what to ask organisers directly.

### P2a · Blue-platform figures dossier *(feeds range rings; study claim 12)*

> For each system, compile the publicly documented figure with 2+ source URLs and note disagreements: Aster 30/Sea Viper engagement range; Sampson radar tracking range; Spearfish torpedo range; Tomahawk Block IV/V range; Harpoon range; CAMM/Sea Ceptor range; Storm Shadow official range; Stingray torpedo range; Typhoon FGR4 combat radius; F-35B combat radius; P-8 Poseidon mission radius; Type 45 / Type 23 / Astute cruise and top speeds; typical SSN/SSBN transit speeds. Separately list, clearly flagged DO-NOT-SOURCE: sonar detection ranges and Sea Viper BMD footprint — these are classified/environment-dependent; we need only a note confirming no reliable public figure exists, so the game labels them fictional doctrine. Deliverable: CSV + exceptions.

### P2b · Turn→clock table proposal

> Given a 6-turn scripted crisis campaign whose episode headers imply Sun 5 Oct 2025 17:00 → 19:00 → 21:00 → 00:00 → 03:00 (irregular +2h/+2h/+3h/+3h), and a design note claiming "6 hours over 6 turns" (inconsistent), propose a clean per-turn duration table (scripted turns + a default for generated turns 7+) that preserves the authored timestamps, keeps overnight darkness on turns 4–5, and yields plausible naval transit distances per turn at 12–20 kts. Show the arithmetic. Deliverable: a small YAML block + one paragraph of rationale.

### P3 · Collateral (post-renewal or spare credits; storyboard before deck)

- **Demo-video storyboard + shot list** for a 3-minute fallback film of the situation globe demo (attract loop → truth map → DTMI badges → facilitator moment), written against the milestone M3 rehearsal.
- **One-pager draft** for judges: the "LLM narrative engine + Microsoft-validated digital twin + living operational picture" story, EXERCISE/responsible-use framing included.
- **Deck outline** (10 slides max) with the ops-room VR vision as exactly one slide.
- **Context scan**: comparable AI-challenge entries / serious-games projects nationally, for positioning language.

---

## Intake checklist (every Manus deliverable)

1. Spot-check 3 random sourced figures against their URLs before use.
2. Strip anything unsourced; flag anything the fictional-doctrine policy covers.
3. Land data as YAML/CSV in the repo via a reviewed commit; land prose in `docs/` or the submission folder — never straight into player-facing content.
