# Handover — delivery system + PM session, 31 Aug–1 Sep 2026

**Read this if you are picking up the PM role** (orchestrating work on this
repo) in a fresh session. It records the delivery system built across 31
Aug–1 Sep, the operating agreement with the owner, the exact state at
handover, and the ordered next actions. Product/plan state lives in
[PLAN.md](../../PLAN.md) and [BUILD_STATE.md](../BUILD_STATE.md) — both
current as of PR #110; this file covers the *machinery and the process*.

---

## 1 · The delivery system (built this session)

**Kanban board, in-repo, mirrored.** The board is `_kanban.md` at the repo
root (moved into the repo by PR #101 with its `.kanban.json` sync state, so
it travels with clones). Drive it ONLY through the kanbanger MCP tools;
never hand-edit. One-way sync (markdown → GitHub) mirrors it to
[GitHub Project #15](https://github.com/users/earlyprototype/projects/15).
Credentials live per-machine in `.claude/settings.local.json` (`env` block:
`GITHUB_TOKEN` = classic PAT with repo+project scopes, `GITHUB_REPO`,
`GITHUB_PROJECT_NUMBER=15`). If the MCP server loses its env (it does after
a crash-restart), the CLI path `kanban-sync _kanban.md` works from the repo
root using the same session env. Card titles are the join key to the mirror
— **never retitle a card**; GitHub-side edits to Status/titles are
forbidden, other card fields are fair game
([docs/PROJECTS_CARD_EDITING.md](../PROJECTS_CARD_EDITING.md)).

**Three-stage CI (PR #103, ported from LCCL after assessment).**
- `checks` (ci.yml): pytest + the verdict classifier's own 47 tests. No
  lint gate yet — 200 `ruff --select E9,F` findings deferred to a board
  card.
- `review` (claude-pr-review.yml): hosted Claude reviews every PR push and
  must end `AUTOMERGE_VERDICT: PASS|BLOCK`; a gate step fails the check on
  any CRITICAL/HIGH/MEDIUM finding. Needs repo secret
  `CLAUDE_CODE_OAUTH_TOKEN` (set). A PR that edits the review workflow
  itself is self-skipped by the action and must be merged manually (the
  bootstrap case — happened on #103, by design).
- Arm Auto-Merge (auto-merge.yml): arms native auto-merge only on a genuine
  PASS verdict, never on a skip.

**KNOWN HOLE — the ruleset does not exist yet.** With no branch protection,
`gh pr merge --auto` merges *immediately* on a PASS verdict without waiting
for `checks`. Six machine merges happened this way (#104–#106, #108, #110);
checks happened to finish first each time. **The single most important
outstanding console action**: a ruleset on `main` requiring `checks` +
`review`. Owner decision attached: empty bypass (pure, but PM board commits
to main then need PRs) vs repo-admin bypass (recommended — board reconciles
keep flowing, code stays gated).

**Gate track record (for stage-3 trust):** two BLOCK verdicts (#108 twice,
#110 once) carrying nine genuine findings — one HIGH (Cesium
camera.changed fires per frame, so a same-tick guard flag can never work;
ray-zoom under tilt drifts sideways), three MEDIUM, five LOW — all correct,
all fixed before merge. No false blocks so far.

## 2 · Operating agreement (owner-ratified rules)

1. **Every task**: GitHub issue first → board card (issue # in title) →
   own branch → PR with `Closes #N` → card to REVIEW at PR-ready.
2. **Merged PR = owner approval** ⇒ PM may gate the card REVIEW→DONE
   (owner ruling 31 Aug). Match the card's *own deliverable* to the merged
   PR — never by issue-number pattern alone (a card was once wrongly
   auto-closed against a same-numbered predecessor PR). PR closed unmerged
   → card back to DOING/TODO and flag the owner.
3. **No-PR tasks** (e.g. branch pruning) have no merge event: they wait in
   REVIEW for the owner's explicit approve.
4. **Worker lanes (Sol instances) drive their own cards**; PM reconciles
   from PR/repo evidence only when a lane cannot (no kanbanger in its
   session). PM never gates its own work without the merge event.
5. **Auto-close does not fire on machine merges** — 3 of 3 `Closes #N`
   keywords failed when github-actions merged. Close issues manually with
   a one-line ship record.
6. **Shared checkout protocol**: check `git branch --show-current` before
   any git operation in the primary checkout; a dispatched card in DOING
   means a worker may hold HEAD. Board commits ride whatever branch is
   active (they merge in); PM commits board state to main only when HEAD
   is free. Extra lanes get worktrees, and every extra lane MUST set
   `KANBANGER_WORKSPACE` to the primary checkout path before session start
   or its kanbanger binds the worktree's *copy* of the board (split
   brain). Cleanup (branch/worktree deletion) only after a **verified**
   `MERGED` state — never on a watch/poll exit alone — and inspect any
   dirty worktree before removing it (one held nine files of real
   uncommitted work this session; rescued via issue #109/PR #110).
7. **Decision issues** ("Decision N#") are answered by commenting and
   closing; each carries a stated default. The audience is **users, not
   judges** (owner correction, 1 Sep — some older issue bodies still say
   judges).

## 3 · State at handover (1 Sep 2026)

**Stage 1 · First Light is DONE** — projector done-test passed 31 Aug
(#94 closed; PLAN.md current). The globe has FLIR + CRT filter switches
(#74 ruling: all options stay live) and manual zoom controls (#107/#108).

**In flight (dispatched 1 Sep, briefs in the session transcript):**
- **#87 per-advisor pushback fan-out** — Sol-1, primary checkout, branch
  `feat/87-advisor-pushback-fanout`. Includes the `/ask` PM-voice bug and
  the carried-over test obligations (Mystery-leak, parity, DTDL
  extend-only).
- **#83 prompt-quality audit** — Sol-2, worktree `../false-flag-lane2`,
  branch `audit/83-prompt-quality-regression`. Read-only audit, deliverable
  under `audits/2026-09-01-prompt-quality/`; must not re-find #97's fixes
  or relitigate closed-#91; audits the pushback family last (against
  whatever main holds, recording the hash).
- Cards for both are in DOING (PM-reconciled — neither lane had board
  access at dispatch). **Reconcile on landing**: verify merge → gate card
  → sync → close issue manually → prune branch (verified-merged only).

**Queued:** #88 (advisor continuity, depends #87; resolve the #90 overlap
first — #90 item 3 duplicates #88's per-advisor deltas). #89 is a complete
evidence-backed work order (scope to one game type + Mystery, gate-don't-
delete, own branch, done tests in the issue) — solo dispatch, it crosses
~29 files; one engine-touching build at a time. Stage 2 build cites the
#72 ruling (SPLIT: scenario-truth geography with the scenario,
engine-derived with the tech, accounting across the seam in CI).

**Awaiting the owner:** ruleset creation + bypass call (§1); REVIEW cards
"PH-0 Prune stale/merged branches" and "Audit recent Claude threads"
(both no-PR, need explicit approve); decisions #73 (both cuts now
timeable; interacts with #89) and #75 (Quest yes/no); unknown branches
`free-gemini-flash` and `claude/coach-command-ehRXq` (unmerged, kept —
delete on owner's word).

**Backlog worth knowing:** ruff lint (config→cleanup→gate; 56 F821s may
hide real bugs); Sol's 12 Windows-only test failures (EOL/env class);
#92 dashboard remaining half (a11y/WCAG, reset contract, traceability).

## 4 · Known quirks and their workarounds

- **kanbanger MCP loses GitHub env after crash-restart** → sync via the
  CLI (`kanban-sync _kanban.md`) or have the owner reconnect the MCP.
- **`gh pr edit` fails on scope** with the session's `GITHUB_TOKEN` (PAT
  lacks `read:org`) → prefix `env -u GITHUB_TOKEN` so gh uses its keyring
  login. All other gh operations work with either.
- **`gh pr checks --watch` exits on stale rollups** (before a new run
  registers) → poll `gh pr view N --json state` for `MERGED`/settled
  instead.
- **ECC hooks spray "invalid JSON output" in some worker sessions.** The
  hooks themselves are verified healthy (all dispatchers return clean JSON
  from both checkouts). Suspect the worker session's environment — first
  check `node --version` in that terminal; fallback suspect is shared
  hook-state contention across concurrent sessions. Mute for worker lanes:
  launch with `ECC_DISABLED_HOOKS` set.
- **Windows CRLF warnings** on board/doc commits are cosmetic
  (.gitattributes normalises; the warnings are expected).
- **fogOfWar root** (one level above this repo) is not a git repo; its
  `CLAUDE.md`/`AGENTS.md`/`.mcp.json` are machine-local and already point
  at this repo's board.

## 5 · Ordered next actions

1. Land and reconcile #87 and #83 (procedure in §3).
2. Owner: create the main ruleset (`checks` + `review`; bypass per §1) —
   closes the instant-merge hole.
3. Resolve the #88/#90 boundary, then dispatch #88.
4. Schedule #89 (solo, own branch), then Stage 2 per PLAN.md.
5. Owner decisions when convenient: #73, #75; approve or return the two
   no-PR REVIEW cards.
