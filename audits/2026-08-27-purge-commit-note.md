# Note on commit 09a03ae ("purge commit")

Disposition ruled by the owner, 27 Aug 2026: **accepted as-is, documented here.**

Commit `09a03ae1c93703a1f8868092885912567c551135` (7 Jul 2026) is titled
`fix: enforce conversation-log cap in both append paths` and its message
describes only that 10-line fix. The same commit also deleted **21,231 lines
across 177 files** of legacy planning material: `@filing/` collaboration
specs and day-plans (73 files), `Graphics/Animations` research (36),
`cli/demos/No_Good/` demos, `unused_systems/` inventories, and assorted
root-level temp files.

The deletions were cleanup, not loss — but they were bundled under an
unrelated fix message, so this note exists to stop the message misleading
anyone reading history.

Everything deleted remains recoverable:

```
git show 09a03ae --stat            # full list of what was removed
git checkout 09a03ae^ -- <path>    # restore any of it
```

Public history is not rewritten.
