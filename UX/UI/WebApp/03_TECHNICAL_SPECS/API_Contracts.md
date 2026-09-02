# WebApp API Contract Guide

`GET /openapi.json` is the executable source of truth for live FastAPI routes,
request models, and declared response models. This file is a curated WebApp
guide; it must not override the generated schema. For handlers without a
declared response model, the handler return value is authoritative.

**Current status:** Every endpoint documented below is implemented on `main`.
The phase headings are historical delivery groupings, not implementation
statuses. Proposed endpoints belong in the active roadmap until they exist in
`/openapi.json`.

Examples show representative shapes. Scenario content, identifiers, metrics,
transcripts, model names, and filesystem paths vary at runtime.

---

## Historical Phase 0 grouping: session and core actions

All endpoints in this section are implemented.

### POST `/game/new`

Creates a session and runs its first briefing.

**Status:** IMPLEMENTED

All body fields are optional:

```json
{
  "scenario_id": "war_game_2025",
  "variant": "standard",
  "difficulty": "standard",
  "play_mode": "immersive",
  "mystery_mode": false,
  "player_name": "Prime Minister",
  "facilitator": false
}
```

Defaults are the values shown above. `facilitator=true` may instead be supplied
as a query parameter. A facilitator session receives REFEREE-layer stream
events; a live session cannot be promoted later.

Success is `200 OK`, not `201 Created`:

```json
{
  "session_id": "9903388b-1050-4d86-83ba-a75eab6a6f7b",
  "turn": 1,
  "phase": "discussion",
  "metrics": {
    "escalation_risk": 63,
    "domestic_stability": 49,
    "alliance_cohesion": 40,
    "casualties_civ": 0,
    "casualties_mil": 2
  },
  "advisors": [
    {"role": "NSA", "status": "online"},
    {"role": "CDS", "status": "online"}
  ],
  "pending_encounter": null
}
```

`pending_encounter` is either `null` or an object containing `country`,
`context`, and `title` when the briefing opens a mandatory call.

### GET `/game/{session_id}/resources`

Returns flattened forces and stockpiles.

**Status:** IMPLEMENTED

```json
{
  "forces": [
    {
      "id": "Type23_Frigate_1",
      "branch": "naval",
      "unit_type": "asw_frigate",
      "location": "UK_waters",
      "status": "operational",
      "role": null,
      "readiness_turns": null,
      "notes": "Armament: Stingray_torpedoes, Harpoon"
    }
  ],
  "stockpiles": [
    {
      "category": "air_defence_missiles",
      "name": "sea_viper_type45",
      "count": 96,
      "note": "2 Type-45s x 48 VLS cells"
    }
  ]
}
```

Each force requires `id` and `branch`; `unit_type`, `location`, `status`,
`role`, `readiness_turns`, and `notes` are nullable. Each stockpile entry
requires `category`, `name`, and integer `count`; `note` is nullable.

### GET `/game/{session_id}/diplomacy/contacts`

Returns the current scenario's diplomatic contacts as an array.

**Status:** IMPLEMENTED

```json
[
  {
    "country_code": "USA",
    "title": "President of the United States",
    "access_level": "foreign_minister",
    "disposition": "Wary but publicly supportive",
    "notes": "Administration policy may affect its level of involvement."
  }
]
```

`country_code` uses the scenario's three-letter codes. `country_code` and
`access_level` are required; `title`, `disposition`, and `notes` are nullable.

### POST `/game/action/call`

Starts a diplomatic call. `country_name` accepts a supported country code,
name, or switchboard key.

**Status:** IMPLEMENTED

```json
{
  "session_id": "9903388b-1050-4d86-83ba-a75eab6a6f7b",
  "country_name": "USA"
}
```

```json
{
  "transcript": [
    "=== DIPLOMATIC CALL: US National Security Advisor (US) ===",
    "US National Security Advisor: The President asked me to coordinate with you on next steps."
  ],
  "active": true,
  "title": "US National Security Advisor",
  "outcome": null
}
```

The HTTP response contains the current call transcript. The route also emits a
`diplomacy` SSE event with `type: "call_started"`.

### POST `/game/action/diplomacy/reply`

Sends a message to the active diplomatic call.

**Status:** IMPLEMENTED

```json
{
  "session_id": "9903388b-1050-4d86-83ba-a75eab6a6f7b",
  "message": "We need a firm commitment."
}
```

The response has the same `transcript`, `active`, nullable `title`, and
nullable `outcome` fields as call creation. It emits a `diplomacy` SSE event
with `type: "call_turn"`. When the call ends, `active` is `false` and
`outcome` contains `assessment` and integer `cohesion_delta`.

### POST `/game/discussion`

Asks the cabinet a question during the `discussion` phase.

**Status:** IMPLEMENTED

```json
{
  "session_id": "9903388b-1050-4d86-83ba-a75eab6a6f7b",
  "question": "What are Russia's likely next moves?",
  "advisor": "all"
}
```

`session_id` and `question` are required. `advisor` is nullable and optional.
The value `"all"` asks the whole room; other values currently use normal
question-keyword routing.

```json
{
  "status": "processed"
}
```

Advisor and narrator lines are emitted as `transcript` SSE events.

### POST `/game/decision`

Legacy one-shot decision route. It commits without a separate preview and
confirmation round; new clients should use the interpret and commit routes.

**Status:** IMPLEMENTED (LEGACY)

```json
{
  "session_id": "9903388b-1050-4d86-83ba-a75eab6a6f7b",
  "action_text": "Increase maritime patrols and consult NATO."
}
```

```json
{
  "status": "processed",
  "pushback": [
    {
      "role": "Attorney General",
      "concern": "Clarify the rules of engagement."
    }
  ]
}
```

There is no live `/game/decision/direct` route. The implemented one-shot path
is `/game/decision`.

---

## Historical Phase 1 grouping: decision preview and commit

Both endpoints in this section are implemented.

### POST `/game/decision/interpret`

Interprets a decision and returns advisor feedback without committing it.

**Status:** IMPLEMENTED

```json
{
  "session_id": "9903388b-1050-4d86-83ba-a75eab6a6f7b",
  "action_text": "Increase maritime patrols and consult NATO."
}
```

```json
{
  "interpretation": "INTERPRETATION: Sustain maritime patrols while consulting NATO.\nFORCES INVOLVED: P-8 patrols, Type 23 frigates\nRESOURCES CONSUMED: aviation fuel, sonobuoys\nTIMELINE: Within six hours\nFEASIBILITY: Feasible at current readiness",
  "critical_concerns": [
    {
      "role": "Chief of the Defence Staff",
      "concern": "The northern approaches may be exposed.",
      "recommendation": "Retain one frigate for the northern screen."
    }
  ],
  "pushback": [
    {
      "role": "Attorney General",
      "concern": "Clarify the rules of engagement."
    }
  ],
  "forces_involved": ["P-8 patrols", "Type 23 frigates"],
  "resources_consumed": ["aviation fuel", "sonobuoys"],
  "timeline": "Within six hours",
  "feasibility": "Feasible at current readiness",
  "raw_transcript": [
    "Prime Minister's Decision: Increase maritime patrols and consult NATO.",
    "",
    "Interpretation: INTERPRETATION: Sustain maritime patrols while consulting NATO.\nFORCES INVOLVED: P-8 patrols, Type 23 frigates\nRESOURCES CONSUMED: aviation fuel, sonobuoys\nTIMELINE: Within six hours\nFEASIBILITY: Feasible at current readiness",
    "",
    "Advisor Concerns:",
    "\nAttorney General: Clarify the rules of engagement.",
    "",
    "CRITICAL ADVISORY:",
    "\nChief of the Defence Staff: The northern approaches may be exposed.",
    "RECOMMENDATION: Retain one frigate for the northern screen.",
    ""
  ]
}
```

Every top-level field shown in the response is required by the declared
response model; the five collection fields may be empty arrays. `interpretation`
is the raw labelled model reply; clients should use the four parsed fields for
structured display. `raw_transcript` includes blank strings as separators.

### POST `/game/decision/commit`

Commits the final decision and runs adjudication.

**Status:** IMPLEMENTED

```json
{
  "session_id": "9903388b-1050-4d86-83ba-a75eab6a6f7b",
  "action_text": "Increase maritime patrols and retain a northern screen.",
  "user_choice": "apply_recommendations"
}
```

`session_id` and `action_text` are required. `user_choice` is an optional
string whose default is `"confirm"`. The current handler accepts the field but
does not validate it or branch on its value; the submitted `action_text` is
what is committed.

```json
{
  "status": "processed",
  "pushback": [
    {
      "role": "Attorney General",
      "concern": "Clarify the rules of engagement."
    }
  ]
}
```

Both commit routes emit player-facing `transcript`, `system`, and
`state_update` events. An `ending` event is emitted when applicable.
Facilitator streams additionally receive REFEREE-layer `adjudication` and
`parse_health` events.

The decision routes return `400` outside the `discussion` or `decision`
phases and `409` while a required diplomatic call remains active.

---

## Historical Phase 2 grouping: state and intelligence

All endpoints in this section are implemented.

### GET `/game/{session_id}/state/vibes`

**Status:** IMPLEMENTED

```json
{
  "vibes": [
    "Crisis Intensity: ELEVATED",
    "Allied Unity: WAVERING",
    "Domestic Support: WAVERING"
  ],
  "dominant": "ELEVATED",
  "intensity": 6
}
```

`intensity` is clamped to the integer range 1-10.

### GET `/game/{session_id}/state/advisors`

**Status:** IMPLEMENTED

```json
{
  "advisors": [
    {
      "role": "uk_nsa",
      "name": "National Security Advisor",
      "trust": 85,
      "relationship": "allied",
      "status": "active",
      "notes": "Coordinates intelligence."
    }
  ]
}
```

`role`, `name`, integer `trust`, `relationship`, and `status` are required;
`notes` is nullable.

### GET `/game/{session_id}/state/flags`

**Status:** IMPLEMENTED

```json
{
  "active_flags": [
    {
      "key": "risk_escalation",
      "label": "Risk Escalation",
      "severity": "monitoring",
      "turn_activated": 1
    }
  ],
  "inactive_flags": [
    {
      "key": "risk_unrest",
      "label": "Risk Unrest",
      "severity": "monitoring",
      "turn_activated": null
    }
  ]
}
```

Both arrays are required. Each flag requires `key`, `label`, and `severity`;
`turn_activated` is nullable.

### GET `/game/{session_id}/intel`

**Status:** IMPLEMENTED

```json
{
  "available_actors": [
    {
      "code": "RUS",
      "name": "Russian Federation",
      "category": "adversary",
      "last_updated": null
    }
  ]
}
```

`code`, `name`, and `category` are required. `last_updated` is a nullable
string on this list response.

### GET `/game/{session_id}/intel/{actor_code}`

**Status:** IMPLEMENTED

```json
{
  "actor": "Russian Federation",
  "code": "RUS",
  "assessment": {
    "raw": [
      "═══════════════════════════════════════════════════════════════════════════════",
      "         DETAILED ASSESSMENT - Russian Federation",
      "         Turn 5",
      "═══════════════════════════════════════════════════════════════════════════════",
      "",
      "Relationship Trend: STABLE →",
      "Current Assessment: 10/100",
      "",
      "Recent Indicators:",
      "• Minimal diplomatic engagement",
      "• Intelligence sharing: none (restrictive)",
      "• Public statements lack commitment",
      "",
      "Analyst Assessment: ADVERSARIAL. Actively working against UK interests.",
      "",
      "═══════════════════════════════════════════════════════════════════════════════"
    ]
  },
  "confidence": "medium",
  "last_updated": 5
}
```

The current assessment object has a `raw` list of display lines; it does not
expose the older invented `military_posture`, `political_intent`, or
`likely_next_moves` structure. `last_updated` is the integer game turn on this
detail response.

---

## Historical Phase 3 grouping: persistence and settings

All endpoints in this section are implemented.

### POST `/game/save`

**Status:** IMPLEMENTED

```json
{
  "session_id": "9903388b-1050-4d86-83ba-a75eab6a6f7b",
  "save_name": "Critical Decision Point"
}
```

```json
{
  "success": true,
  "save_path": "/repo/saves/Critical_Decision_Point_2026-09-02_14-30-00.json",
  "timestamp": "now"
}
```

The returned `save_path` is generated for the host filesystem. The response's
`timestamp` is currently the literal string `"now"`; the saved file metadata
contains the ISO timestamp used by the saves list.

### POST `/game/load`

Loads a save into a new session identifier.

**Status:** IMPLEMENTED

```json
{
  "save_path": "/repo/saves/Critical_Decision_Point_2026-09-02_14-30-00.json"
}
```

```json
{
  "session_id": "bb47b99c-eb31-49cb-9f22-ae7a84bf67cd",
  "turn": 5,
  "phase": "discussion",
  "metrics": {
    "escalation_risk": 60,
    "domestic_stability": 50,
    "alliance_cohesion": 40,
    "casualties_civ": 0,
    "casualties_mil": 2
  },
  "transcript": [],
  "active_call": null
}
```

`active_call` is either `null` or an object containing `country`, `title`,
`required`, and `transcript`.

### GET `/game/saves`

**Status:** IMPLEMENTED

```json
{
  "saves": [
    {
      "path": "/repo/saves/Critical_Decision_Point_2026-09-02_14-30-00.json",
      "name": "Critical Decision Point",
      "timestamp": "2026-09-02T14:30:00.000000",
      "turn": 5,
      "scenario": "war_game_2025"
    }
  ]
}
```

The `saves` array may be empty.

### GET `/scenarios`

**Status:** IMPLEMENTED

```json
{
  "scenarios": [
    {
      "id": "war_game_2025",
      "name": "Standard Campaign",
      "description": "Experience the full crisis as it unfolds over 6 scripted turns",
      "variants": ["standard", "fast_start"]
    }
  ]
}
```

Every scenario requires `id`, `name`, `description`, and `variants`. This route
does not return `difficulty_options` or `mode_options`.

### GET `/settings/llm`

**Status:** IMPLEMENTED

```json
{
  "provider": "Google Gemini",
  "contexts": {
    "advisor_qa": "gemini-2.5-pro",
    "decision_interpretation": "gemini-2.5-flash"
  },
  "models": {
    "flash": "gemini-2.5-flash",
    "pro": "gemini-2.5-pro"
  }
}
```

The context and model maps reflect the active configuration.

### POST `/settings/llm`

**Status:** IMPLEMENTED

```json
{
  "contexts": {
    "mode": "flash"
  }
}
```

Both `provider` and `contexts` are optional. The current handler acts only on
`contexts.mode` values `"flash"` and `"pro"`; `provider` is accepted but not
applied.

```json
{
  "status": "updated"
}
```

---

## Contract conventions

### Status and errors

- Successful routes documented here return `200 OK`.
- `400 Bad Request` is used for invalid game phase or action state.
- `404 Not Found` is used for an unknown session.
- `409 Conflict` is used when a required diplomatic call blocks a decision.
- FastAPI request validation returns `422 Unprocessable Entity`.
- Handler failures return `500 Internal Server Error`.

Application errors use FastAPI's `detail` field:

```json
{
  "detail": "Session not found"
}
```

Validation errors use a `detail` array generated by FastAPI. There is no
general `{error, message, code}` response envelope.

### SSE stream

Clients subscribe with `GET /stream/{session_id}`. Each emitted event has an
SSE event name and JSON data. The server adds `layer`, `turn`, `t_plus_s`, and
`event_seq` to object payloads:

```text
event: transcript
data: {"type":"advisor","role":"National Security Advisor","content":"...","layer":"cabinet","turn":1,"t_plus_s":2.4,"event_seq":7}
```

Player sessions never receive REFEREE-layer events. Event names include
`transcript`, `diplomacy`, `intel`, `system`, `state_update`, and `ending`; facilitator
sessions can additionally receive `llm_call`, `adjudication`, and
`parse_health`.

### Nulls and arrays

Declared optional response fields are serialized as `null` unless a route
provides a value. Declared collection fields are arrays and may be empty.

---

## Planned contracts

None are specified in this live guide. Historical unchecked phase-plan items
are planning records, not promises that an endpoint is absent or forthcoming.
Facilitator controls, HTML pages, health, demo, and DTDL support routes are
outside this curated player-WebApp guide; omission here does not imply status.

**Maintenance:** Reconcile this guide whenever the FastAPI routes or models
change; use `/openapi.json` to detect drift.
