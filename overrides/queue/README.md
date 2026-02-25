# Control-Cell Override Queue

Place override items as JSON files conforming to `overrides/queue/schema.json`.
A maintainer reviews, approves or rejects, and the engine applies approved overrides.

Fields:
- id: unique identifier
- scene: scene index
- rationale: short text explanation
- suggestion: bounded change request (for example, adjust metric by ±X)
- author: human or model name
- status: pending|approved|rejected


