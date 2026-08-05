#!/usr/bin/env python3
"""Rebuild the audit folder: neutral documents, raw agent reports, register."""
import json, os, glob

SESSION = '/tmp/claude-0/-home-user-false-flag/626a8206-8ea1-556d-9831-1103e7e56d4a'
WF = ('/root/.claude/projects/-home-user-false-flag/'
      '626a8206-8ea1-556d-9831-1103e7e56d4a/subagents/workflows/wf_73e42dc7-bfe')
DEST = '/home/user/false-flag/audits/2026-08-05-llm-context'

task = json.load(open(f'{SESSION}/tasks/wgg1ffhaj.output'))
result = task['result']

# ---------------------------------------------------------------------------
# 1. Raw agent reports, verbatim, one file per agent
# ---------------------------------------------------------------------------
labels = {p['agentId']: p['label'] for p in task.get('workflowProgress', []) if p.get('agentId')}
os.makedirs(f'{DEST}/data/agent-reports', exist_ok=True)

rows = [json.loads(l) for l in open(f'{WF}/journal.jsonl') if l.strip()]
results = [r for r in rows if r.get('type') == 'result']
written = 0
for r in results:
    aid = r.get('agentId') or ''
    label = labels.get(aid, aid)
    value = r.get('value', r.get('result'))
    name = label.replace(':', '-')
    if isinstance(value, (dict, list)):
        with open(f'{DEST}/data/agent-reports/{name}.json', 'w') as fh:
            json.dump(value, fh, indent=2)
    else:
        with open(f'{DEST}/data/agent-reports/{name}.md', 'w') as fh:
            fh.write(str(value))
    written += 1

# ---------------------------------------------------------------------------
# 2. Verified notes — the second-pass findings, stated as facts
# ---------------------------------------------------------------------------
NOTES = {}
for g in result['full']:
    for r in (g.get('verdict') or {}).get('refutations', []):
        NOTES.setdefault(g['group'], []).append(r)

total_notes = sum(len(v) for v in NOTES.values())

N = ['# Verified notes',
     '',
     'Statements below were checked directly against the source and supersede any conflicting',
     'row in `SCHEMATIC.md` or `data/maps/*.json`. Each carries the file:line that establishes',
     'it.',
     '']
for grp in sorted(NOTES):
    N += [f'## {grp}', '']
    for r in NOTES[grp]:
        stated = r.get('correction') or r['claim']
        N.append(f'- {stated}')
        if r.get('evidence'):
            N.append(f'    - `{r["evidence"]}`')
    N.append('')
open(f'{DEST}/VERIFIED-NOTES.md', 'w').write('\n'.join(N))

for f in ('CORRECTIONS.md',):
    p = f'{DEST}/{f}'
    if os.path.exists(p):
        os.remove(p)

print(f'agent reports: {written}   verified notes: {total_notes}')
