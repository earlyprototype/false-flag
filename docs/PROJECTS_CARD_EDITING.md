# Projects Card Editing via GraphQL

Rules and recipes for editing cards on GitHub Project #15 (`@FalseFlag`), the
mirror of `_kanban.md`. Sync is one-way (markdown → Projects) and writes
**Status only** — every other card field survives sync untouched. All mutation
and input names below are verified against the live schema (31 Aug 2026).

## Handles

| Thing | Value |
|---|---|
| Project | `PVT_kwHOCkn-fc4Bh_kp` — [user project #15](https://github.com/users/earlyprototype/projects/15) |
| Repository | `R_kgDORYJOpQ` (`earlyprototype/false-flag`) |
| Item ids (`PVTI_…`) | `.kanban.json`, keyed by task title |

## Field rules

| Field | Edit? | How |
|---|---|---|
| Title | **Never on GitHub** | Title is the sync join key — retitle locally via kanbanger |
| Status | **Never by hand** | Owned by kanbanger (`move_task` → sync) |
| Body | Yes | `updateProjectV2DraftIssue` — needs the `DI_…` content id, not `PVTI_…` |
| Assignees | Yes | Same mutation, `assigneeIds` (user node ids) |
| Custom fields (Priority, Size, dates, …) | Yes | `updateProjectV2ItemFieldValue` / `clearProjectV2ItemFieldValue` |
| Labels / Milestone | Not on drafts | Convert the card to a real issue first, then normal issue mutations |
| Archive / delete | **Never by hand** | Sync archives cards whose local task was removed |

## Recipes

Get a card's draft-issue content id (`DI_…`) from its item id:

```bash
gh api graphql -f query='{ node(id:"PVTI_…"){ ... on ProjectV2Item { content { ... on DraftIssue { id } } } } }'
```

Edit a card body:

```bash
gh api graphql -f query='mutation { updateProjectV2DraftIssue(input:{ draftIssueId:"DI_…", body:"…" }) { draftIssue { id } } }'
```

List the project's fields with their single-select options:

```bash
gh api graphql -f query='{ node(id:"PVT_kwHOCkn-fc4Bh_kp"){ ... on ProjectV2 { fields(first:30){ nodes { ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }'
```

Set a field value on a card (single-select shown; other kinds take
`value:{ text:"…" }`, `{ number: 3 }`, or `{ date:"2026-09-01" }`):

```bash
gh api graphql -f query='mutation { updateProjectV2ItemFieldValue(input:{ projectId:"PVT_kwHOCkn-fc4Bh_kp", itemId:"PVTI_…", fieldId:"PVTSSF_…", value:{ singleSelectOptionId:"…" } }) { projectV2Item { id } } }'
```

Convert a draft card to a repo issue (unlocks labels/milestone; the card keeps
its place and item id on the board):

```bash
gh api graphql -f query='mutation { convertProjectV2DraftIssueItemToIssue(input:{ itemId:"PVTI_…", repositoryId:"R_kgDORYJOpQ" }) { item { id } } }'
```

After converting a first card, confirm the next sync still moves its Status
before converting more.
