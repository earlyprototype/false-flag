<!-- kanbanger:start -->
## Kanbanger: task board for this project

This project tracks work on a Kanban board managed by the **Kanbanger MCP
server**. The board lives at `_kanban.md` in the project root and is
**project-scoped** -- configured here via `.mcp.json`, not globally.
The board belongs to this project.

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

**If the Kanbanger tools aren't available** in this session, kanbanger may not
be installed globally, or this project may not be provisioned yet (no
`_kanban.md` / `.mcp.json`). Install once
(`pipx install git+https://github.com/earlyprototype/kanbanger-partymix.git`),
then provision this project by calling the MCP `setup_project` tool (or, for
CLI parity, run `kanbanger init` in the project root), and restart the session.
<!-- kanbanger:end -->
