# API Contracts Reference
**Purpose:** Definitive API contract documentation for all backend endpoints  
**Status:** Phase 0 contracts defined, Phase 1-4 to be added as implemented  

---

## Table of Contents

1. [Phase 0 Contracts](#phase-0-contracts) (Stabilisation)
2. [Phase 1 Contracts](#phase-1-contracts) (Decision Parity)
3. [Phase 2 Contracts](#phase-2-contracts) (Deep State & Intel)
4. [Phase 3 Contracts](#phase-3-contracts) (Diplomacy & Meta-Game)
5. [Contract Conventions](#contract-conventions)

---

## Phase 0 Contracts

### POST `/game/new`
**Purpose:** Create new game session

**Request:**
```json
{
  "scenario_id": "war_game_2025",
  "variant": "standard",
  "difficulty": "standard",
  "play_mode": "immersive",
  "player_name": "Prime Minister"
}
```

**Response:**
```json
{
  "session_id": "abc123",
  "turn": 1,
  "phase": "briefing",
  "metrics": {
    "escalation_risk": 35,
    "domestic_stability": 65,
    "alliance_cohesion": 70,
    "casualties_mil": 0,
    "casualties_civ": 0
  },
  "advisors": [
    {
      "role": "NSA",
      "status": "active"
    },
    {
      "role": "CDS",
      "status": "active"
    }
  ]
}
```

**Required Fields:**
- `scenario_id` (string)
- `difficulty` (string: "easy" | "standard" | "hard")
- `play_mode` (string: "classic" | "immersive" | "emergent")

**Optional Fields:**
- `variant` (string, defaults to "standard")
- `player_name` (string, defaults to "Prime Minister")

---

### GET `/game/{id}/resources`
**Purpose:** Get UK military forces and stockpiles

**URL Parameters:**
- `id` (string) - Session ID

**Response:**
```json
{
  "forces": [
    {
      "id": "carrier_qe",
      "branch": "Royal Navy",
      "unit_type": "Aircraft Carrier",
      "location": "Mediterranean",
      "status": "Ready",
      "role": "Power projection",
      "readiness_turns": 0,
      "notes": "Flagship of carrier strike group"
    },
    {
      "id": "typhoon_sqn_1",
      "branch": "RAF",
      "unit_type": "Fighter Squadron",
      "location": "RAF Coningsby",
      "status": "Ready",
      "readiness_turns": 0
    }
  ],
  "stockpiles": [
    {
      "category": "Munitions",
      "name": "Storm Shadow",
      "count": 24,
      "note": "Air-launched cruise missile"
    },
    {
      "category": "Munitions",
      "name": "GMLRS",
      "count": 150
    }
  ]
}
```

**Force Fields:**
- `id` (string, required) - Unique identifier
- `branch` (string, required) - Service branch
- `unit_type` (string, optional) - Type of unit
- `location` (string, optional) - Current deployment
- `status` (string, optional) - Operational status
- `role` (string, optional) - Mission role
- `readiness_turns` (int, optional) - Turns until ready
- `notes` (string, optional) - Additional info

**Stockpile Fields:**
- `category` (string, required) - Munitions/Equipment/Supplies
- `name` (string, required) - Item name
- `count` (int, required) - Quantity
- `note` (string, optional) - Description

**Client Handling:**
- If field missing, treat as `null`
- If entire array missing, show fallback UI

---

### GET `/game/{id}/diplomacy/contacts`
**Purpose:** Get available diplomatic contacts

**URL Parameters:**
- `id` (string) - Session ID

**Response:**
```json
[
  {
    "country_code": "US",
    "title": "President (direct line)",
    "access_level": "leader",
    "disposition": "Supportive",
    "notes": "Special relationship"
  },
  {
    "country_code": "FR",
    "title": "Foreign Minister",
    "access_level": "foreign_minister",
    "disposition": "Cautious",
    "notes": null
  },
  {
    "country_code": "DE",
    "title": "Ambassador",
    "access_level": "ambassador",
    "disposition": "Neutral"
  }
]
```

**Contact Fields:**
- `country_code` (string, required) - ISO 2-letter code
- `title` (string, optional) - Contact's title
- `access_level` (string, required) - "leader" | "foreign_minister" | "ambassador" | "restricted"
- `disposition` (string, optional) - Current attitude toward UK
- `notes` (string, optional) - Additional context

---

### POST `/game/action/call`
**Purpose:** Initiate diplomatic phone call

**Request:**
```json
{
  "session_id": "abc123",
  "country_name": "United States"
}
```

**Response:**
```json
{
  "status": "processed"
}
```

**SSE Stream Events:**
- `dialogue` - Conversation exchanges
- `inject` - Narrative injects
- `state_update` - Metrics/phase changes

**Notes:**
- Primary content delivered via SSE, not HTTP response
- HTTP response only confirms request accepted

---

### POST `/game/discussion`
**Purpose:** Ask advisor question during discussion phase

**Request:**
```json
{
  "session_id": "abc123",
  "question": "What are Russia's likely next moves?"
}
```

**Response:**
```json
{
  "status": "processed"
}
```

**SSE Stream Events:**
- `advisor_response` - Advisor answers
- `inject` - Additional context

---

### POST `/game/decision`
**Purpose:** Submit decision and trigger adjudication (LEGACY - use Phase 1 endpoints)

**Request:**
```json
{
  "session_id": "abc123",
  "action_text": "Deploy carrier strike group to Baltic Sea"
}
```

**Response:**
```json
{
  "status": "processed"
}
```

**SSE Stream Events:**
- `reasoning` - AI thinking steps
- `inject` - Narrative outcomes
- `state_update` - Metrics changes, phase transition

**Deprecation Notice:**
This endpoint skips the interpretation/pushback step. Phase 1 introduces `/game/decision/interpret` and `/game/decision/commit` for proper decision workflow.

---

## Phase 1 Contracts

### POST `/game/decision/interpret`
**Purpose:** Interpret player's decision and gather critical concerns (Phase 1)

**Request:**
```json
{
  "session_id": "abc123",
  "action_text": "Deploy carrier strike group to Baltic Sea"
}
```

**Response:**
```json
{
  "interpretation": {
    "summary": "Deploy HMS Queen Elizabeth CSG to Baltic to demonstrate resolve",
    "forces_involved": ["HMS Queen Elizabeth CSG", "RAF Typhoon squadron"],
    "timeline": "24-48 hours for deployment",
    "estimated_risk": "Moderate escalation potential"
  },
  "critical_concerns": [
    {
      "role": "CDS",
      "concern": "Insufficient air cover during transit",
      "recommendation": "Deploy additional Typhoon squadron to Estonia"
    },
    {
      "role": "NSA",
      "concern": "Risk of Russian submarine contact",
      "recommendation": "Increase ASW assets in convoy"
    }
  ]
}
```

**Status:** PLANNED (not yet implemented)

---

### POST `/game/decision/commit`
**Purpose:** Commit to decision after review (Phase 1)

**Request:**
```json
{
  "session_id": "abc123",
  "action_text": "Deploy carrier strike group to Baltic Sea with additional Typhoon squadron",
  "user_choice": "apply_recommendations"
}
```

**Fields:**
- `action_text` (string) - Final decision text (may be modified)
- `user_choice` (string) - "confirm" | "override" | "apply_recommendations"

**Response:**
```json
{
  "status": "processed"
}
```

**SSE Stream Events:**
- Same as legacy `/game/decision` endpoint

**Status:** PLANNED (not yet implemented)

---

## Phase 2 Contracts

### GET `/game/{id}/state/vibes`
**Purpose:** Get current situation atmosphere descriptors

**Response:**
```json
{
  "vibes": ["tense", "uncertainty", "resolve"],
  "dominant": "tense",
  "intensity": 7
}
```

**Status:** PLANNED (not yet implemented)

---

### GET `/game/{id}/state/advisors`
**Purpose:** Get advisor trust and relationship data

**Response:**
```json
{
  "advisors": [
    {
      "role": "NSA",
      "name": "Sir Humphrey Appleby",
      "trust": 65,
      "relationship": "cautious",
      "status": "active",
      "notes": "Skeptical of military action"
    },
    {
      "role": "CDS",
      "name": "General Sarah Mitchell",
      "trust": 85,
      "relationship": "supportive",
      "status": "active"
    }
  ]
}
```

**Trust Scale:** 0-100  
**Relationship Types:** "professional" | "supportive" | "cautious" | "adversarial"

**Status:** PLANNED (not yet implemented)

---

### GET `/game/{id}/state/flags`
**Purpose:** Get active world crisis flags

**Response:**
```json
{
  "active_flags": [
    {
      "key": "russian_mobilisation",
      "label": "Russian Mobilisation Detected",
      "severity": "critical",
      "turn_activated": 3
    }
  ],
  "inactive_flags": [
    {
      "key": "nato_article_5",
      "label": "NATO Article 5 Invoked"
    }
  ]
}
```

**Severity Levels:** "critical" | "elevated" | "monitoring"

**Status:** PLANNED (not yet implemented)

---

### GET `/game/{id}/intel`
**Purpose:** List available intelligence actors

**Response:**
```json
{
  "available_actors": [
    {
      "code": "RUS",
      "name": "Russia",
      "category": "adversary",
      "last_updated": "Turn 5"
    },
    {
      "code": "US",
      "name": "United States",
      "category": "ally",
      "last_updated": "Turn 4"
    }
  ]
}
```

**Categories:** "ally" | "neutral" | "adversary"

**Status:** PLANNED (not yet implemented)

---

### GET `/game/{id}/intel/{actor_code}`
**Purpose:** Get detailed intelligence assessment for specific actor

**URL Parameters:**
- `actor_code` (string) - Country code (e.g. "RUS", "US")

**Response:**
```json
{
  "actor": "Russia",
  "code": "RUS",
  "assessment": {
    "military_posture": "Aggressive buildup along NATO borders...",
    "political_intent": "Seeking to fracture NATO cohesion...",
    "economic_factors": "Sanctions causing domestic strain...",
    "likely_next_moves": [
      "Escalate hybrid warfare",
      "Test NATO resolve with probes"
    ],
    "vulnerabilities": [
      "Economic isolation",
      "Domestic unrest potential"
    ]
  },
  "confidence": "medium",
  "last_updated": 5
}
```

**Confidence Levels:** "high" | "medium" | "low"

**Status:** PLANNED (not yet implemented)

---

## Phase 3 Contracts

### POST `/game/save`
**Purpose:** Save current game state

**Request:**
```json
{
  "session_id": "abc123",
  "save_name": "Critical Decision Point"
}
```

**Response:**
```json
{
  "success": true,
  "save_path": "saves/critical_decision_point_2025-11-23.json",
  "timestamp": "2025-11-23T16:30:00Z"
}
```

**Status:** PLANNED (not yet implemented)

---

### POST `/game/load`
**Purpose:** Load saved game

**Request:**
```json
{
  "save_path": "saves/critical_decision_point_2025-11-23.json"
}
```

**Response:**
```json
{
  "session_id": "xyz789",
  "turn": 5,
  "phase": "discussion",
  "metrics": { ... }
}
```

**Status:** PLANNED (not yet implemented)

---

### GET `/game/saves`
**Purpose:** List all available saved games

**Response:**
```json
{
  "saves": [
    {
      "path": "saves/critical_decision_point_2025-11-23.json",
      "name": "Critical Decision Point",
      "timestamp": "2025-11-23T16:30:00Z",
      "turn": 5,
      "scenario": "war_game_2025"
    }
  ]
}
```

**Status:** PLANNED (not yet implemented)

---

### GET `/scenarios`
**Purpose:** List available game scenarios

**Response:**
```json
{
  "scenarios": [
    {
      "id": "war_game_2025",
      "name": "War Game 2025",
      "description": "Rapid escalation in Eastern Europe...",
      "difficulty_options": ["easy", "standard", "hard"],
      "mode_options": ["classic", "immersive", "emergent"]
    }
  ]
}
```

**Status:** PLANNED (not yet implemented)

---

### GET `/settings/llm`
**Purpose:** Get current LLM configuration

**Response:**
```json
{
  "provider": "openai",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Status:** PLANNED (not yet implemented)

---

### POST `/settings/llm`
**Purpose:** Update LLM configuration

**Request:**
```json
{
  "provider": "openai",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response:**
```json
{
  "success": true
}
```

**Status:** PLANNED (not yet implemented)

---

## Contract Conventions

### HTTP Status Codes
- `200 OK` - Request successful
- `201 Created` - Resource created (new session)
- `400 Bad Request` - Invalid request body
- `404 Not Found` - Session/resource not found
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "error": true,
  "message": "Session not found",
  "code": "SESSION_NOT_FOUND"
}
```

### SSE Event Format
```
event: advisor_response
data: {"speaker": "NSA", "text": "I recommend...", "timestamp": 1700000000}

event: state_update
data: {"metrics": {...}, "phase": "adjudication"}
```

### Timestamp Format
ISO 8601: `2025-11-23T16:30:00Z`

### Null Handling
- Missing optional fields treated as `null`
- Clients must handle `null` gracefully (don't assume field exists)

### Array Handling
- Empty arrays returned as `[]`, not `null`
- Clients should check `.length` before iterating

---

**Last Updated:** 23 Nov 2025  
**Next Update:** After Phase 1 implementation


