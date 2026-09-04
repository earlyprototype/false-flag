<!-- kanbanger:start -->
## Kanbanger: task board for this project

This repository uses the Kanbanger board in the outer `fogOfWar` workspace
selected by `KANBANGER_WORKSPACE`, with `.kanban.json` beside it. The board is
not inside this repository or its worktrees. Use the MCP resource to locate it;
do not create a separate board here.

**For AI agents:**
- **Always use the Kanbanger MCP tools** (`list_tasks`, `add_task`, `move_task`,
  `delete_task`, `sync_to_github`, `get_sync_status`) to read or change the
  board. **Never hand-edit `_kanban.md`** -- direct edits bypass validation,
  locking, and atomic writes and will eventually corrupt the board or its
  GitHub sync.
- On first contact, read the `kanban://current-board` resource before acting.
- **REVIEW gates DONE.** AI-completed work goes to REVIEW via `propose_done`,
  never straight to DONE; a human approves REVIEW -> DONE via `approve_done`.
  Never move your own work directly to DONE.

**If the Kanbanger tools aren't available or the board is reported missing,**
stop and report a binding problem. Do not call `setup_project` or
`kanbanger init`: the outer workspace already has one canonical board.
<!-- kanbanger:end -->

## Recovery orchestration

- Read `PLAN.md` for the locked product streams and current dependency.
- Do not invoke the early-prototype `/worktime`, `/chosetime` or `/clocktime`
  lifecycle in this workspace. Its Stop/close behaviour is incompatible with
  the canonical board and human REVIEW gate.
- Use Kanbanger through its MCP-backed worker. AI work may move only to REVIEW;
  only the human owner approves DONE. Do not sync unless the owner asks.
- Use one isolated branch or worktree and one focused observable proof per
  implementation task. Broad test counts are not acceptance evidence.
