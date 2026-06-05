# Scenario Selection - Quick Start

## What's New?

The wargame now has **2 scenario variants** to choose from at game start:

### 🎯 Standard Campaign (90-120 min)
- **6 scripted turns** before stochastic gameplay
- Gradual escalation over 10 hours of in-game time
- Full NATO consultation and diplomatic complexity
- **Recommended for:** First-time players

### ⚡ Fast Start (45-60 min)
- **3 scripted turns** before stochastic gameplay  
- Rapid escalation with breaking developments mid-turn
- All key narrative beats preserved but compressed
- **Recommended for:** Experienced players, replays, time-limited sessions

---

## How to Play

### Option 1: Interactive Menu (Recommended)
```powershell
.\.venv\Scripts\python.exe -m cli.main play
```

You'll see a scenario selection menu. Enter `1` for Standard or `2` for Fast Start.

### Option 2: Command Line
```powershell
# Standard Campaign
.\.venv\Scripts\python.exe -m cli.main play --variant standard

# Fast Start
.\.venv\Scripts\python.exe -m cli.main play --variant fast_start

# Disable dynamic generation (scripted content only)
.\.venv\Scripts\python.exe -m cli.main play --variant fast_start --no-stochastic-injects
```

**Note:** Dynamic scenario generation is **enabled by default**. The game will automatically transition to LLM-generated content after scripted turns end.

---

## What's the Difference?

| Feature | Standard | Fast Start |
|---------|----------|------------|
| **Scripted Turns** | 6 | 3 |
| **In-Game Time** | 10 hours | 3 hours |
| **Estimated Real Time** | 90-120 min | 45-60 min |
| **Pacing** | Gradual | Rapid |
| **Stochastic From** | Turn 7 | Turn 4 |
| **Narrative Beats** | Full detail | Compressed |

### Fast Start Timeline

**Turn 1** (17:00-19:00):  
- COBRA briefing (F-35 pilots, Russian fleet)
- **Breaking:** Submarine surfaces near Orkney (mid-turn interrupt)

**Turn 2** (21:00-00:00):  
- Drax Power Station explosion
- **Incoming Call:** US National Security Advisor (NATO fracturing)

**Turn 3** (03:00):  
- Ballistic missile launch (8-12 minute warning)
- **Stochastic gameplay begins Turn 4**

---

## Full Documentation

See [`docs/SCENARIO_VARIANTS.md`](docs/SCENARIO_VARIANTS.md) for:
- Detailed timeline comparisons
- Compression strategy explanation
- How to create custom variants
- Technical implementation details

---

## Quick Test

Want to see the menu?

```powershell
.\.venv\Scripts\python.exe -m cli.main play
```

Press `1` or `2` to select, then experience the crisis! 🎮

