#!/usr/bin/env python3
"""Export the LLM context audit into the repo as a lookup folder."""
import json, os, shutil, re

SESSION = '/tmp/claude-0/-home-user-false-flag/626a8206-8ea1-556d-9831-1103e7e56d4a'
WF = '/root/.claude/projects/-home-user-false-flag/626a8206-8ea1-556d-9831-1103e7e56d4a/subagents/workflows/wf_73e42dc7-bfe'
SCRIPTS = '/root/.claude/projects/-home-user-false-flag/626a8206-8ea1-556d-9831-1103e7e56d4a/workflows/scripts'
DEST = '/home/user/false-flag/audits/2026-08-05-llm-context'

os.makedirs(f'{DEST}/data/maps', exist_ok=True)
os.makedirs(f'{DEST}/data/verification', exist_ok=True)
os.makedirs(f'{DEST}/html', exist_ok=True)

result = json.load(open(f'{SESSION}/tasks/wgg1ffhaj.output'))['result']

# ---- structured data -------------------------------------------------------
json.dump(result, open(f'{DEST}/data/audit.json', 'w'), indent=2)

for g in result['full']:
    key = g['group']
    json.dump(g['map'], open(f'{DEST}/data/maps/{key}.json', 'w'), indent=2)
    if g.get('verdict'):
        json.dump(g['verdict'], open(f'{DEST}/data/verification/{key}.json', 'w'), indent=2)

json.dump(result['orphans'], open(f'{DEST}/data/orphans.json', 'w'), indent=2)

# ---- reproducibility -------------------------------------------------------
for f in os.listdir(SCRIPTS):
    if 'llm-context-audit' in f:
        shutil.copy(f'{SCRIPTS}/{f}', f'{DEST}/data/workflow.js')

# ---- rendered documents ----------------------------------------------------
for src, dst in [('schematic.html', 'schematic.html')]:
    p = f'{SESSION}/{src}'
    if not os.path.exists(p):
        p = f'{SESSION}/scratchpad/{src}'
    if os.path.exists(p):
        shutil.copy(p, f'{DEST}/html/{dst}')

# ---- SCHEMATIC.md : the traceable map, in markdown -------------------------
groups = {g['group']: g['map']['calls'] for g in result['full']}
ORDER = [
    ('Briefing', [('inject', 'inject_generation'), ('discussion', 'narrator_bridge')]),
    ('Discussion', [('discussion', 'advisor_qa')]),
    ('Decision', [('decision', 'decision_interpretation'),
                  ('decision', 'advisor_pushback'),
                  ('omissions', 'critical_omissions.advisor_scan')]),
    ('Adjudication', [('adjudication', 'ADJ-1'), ('adjudication', 'ADJ-2'),
                      ('adjudication', 'ADJ-3')]),
    ('External', [('actors', 'state_actor_response'),
                  ('actors', 'diplomacy_conversation_reply'),
                  ('actors', 'diplomacy_outcome_assessment')]),
]

def find(gid, cid):
    for c in groups[gid]:
        if c['call_id'] == cid:
            return c
    raise KeyError(cid)


CORR = {}
for g in result['full']:
    for r in (g.get('verdict') or {}).get('refutations', []):
        CORR.setdefault(g['group'], []).append(r)


def corrections_for(cid):
    keys = [k for k in (cid.lower(), cid.split('.')[-1].lower()) if len(k) > 3]
    return [r for rs in CORR.values() for r in rs
            if any(k in r['claim'].lower() for k in keys)]

L = ['# FALSE FLAG — LLM call schematic',
     '',
     'Every prompt the game issues: what enters it, where that data comes from, how it is',
     'bounded, why the call exists, and what its output changes. State of the source at',
     '`d197c44`; measurements against `saves/parked_campaign4_borrowed_faces.json`.',
     '',
     'Each input row is marked `IN` (reaches the prompt) or `OUT` (available to the call site',
     'and not sent).',
     '',
     'Where a row conflicts with `VERIFIED-NOTES.md`, the note holds.',
     '']

total_in = total_out = 0
for phase, calls in ORDER:
    L += [f'## {phase}', '']
    for gid, cid in calls:
        c = find(gid, cid)
        ins = c.get('inputs', [])
        got = [i for i in ins if i.get('reaches_prompt')]
        absent = [i for i in ins if not i.get('reaches_prompt')]
        total_in += len(got); total_out += len(absent)

        L += [f'### {c["name"]}', '', f'`{c["call_id"]}`', '']
        for k, v in [('Prompt built at', c.get('prompt_builder')),
                     ('Dispatched at', c.get('dispatch_site')),
                     ('LLM context', c.get('llm_context')),
                     ('Model tier', c.get('model_tier')),
                     ('Calls per turn', c.get('calls_per_turn')),
                     ('Concurrency', c.get('concurrency')),
                     ('On failure', c.get('failure_behaviour'))]:
            if v:
                L.append(f'- **{k}** — {v}')
        L += ['', '**Why this call exists.** ' + c['game_purpose'], '']
        if c.get('output_shape'):
            L += ['**What it must return.** ' + c['output_shape'], '']
        if c.get('consumed_by'):
            L += [f'**Parsed at** {c["consumed_by"]}', '']

        L += [f'#### Data in — {len(got)} reach the prompt', '']
        for i in got:
            L.append(f'- `IN ` **{i["data"]}**')
            L.append(f'    - source: {i["source"]}')
            if i.get('bounded_by'):
                L.append(f'    - bound: {i["bounded_by"]}')
            if i.get('evidence'):
                L.append(f'    - evidence: {i["evidence"]}')
        L.append('')
        if absent:
            L += [f'#### Available but not sent — {len(absent)}', '']
            for i in absent:
                L.append(f'- `OUT` **{i["data"]}**')
                L.append(f'    - source: {i["source"]}')
                if i.get('evidence'):
                    L.append(f'    - evidence: {i["evidence"]}')
            L.append('')
        L += ['#### What the output changes', '']
        for a in c.get('affects', []):
            L.append(f'- {a}')
        L.append('')
        if c.get('notable_gaps'):
            L += ['#### Observed gaps', '']
            for g_ in c['notable_gaps']:
                L.append(f'- {g_}')
            L.append('')
        corr = corrections_for(c['call_id'])
        if corr:
            L += [f'#### Verified notes — {len(corr)}', '',
                  '_Supersedes any row above that conflicts with it._', '']
            for r in corr:
                L.append(f'- {r.get("correction") or r["claim"]}')
                if r.get('evidence'):
                    L.append(f'    - `{r["evidence"]}`')
            L.append('')

# ---- state reachability ----------------------------------------------------
o = result['orphans']
rows = o['orphaned_state']
un = [r for r in rows if not r.get('reaches_any_prompt')]
re_ = [r for r in rows if r.get('reaches_any_prompt')]
L += ['## State reachability', '',
      f'{len(un)} of {len(rows)} audited state fields reach no prompt at all.', '',
      f'### Reaches no prompt — {len(un)}', '']
for r in un:
    L.append(f'- **{r["owner"]} · {r["field"]}**')
    if r.get('consequence'):
        L.append(f'    - consequence: {r["consequence"]}')
    if r.get('evidence'):
        L.append(f'    - evidence: {r["evidence"]}')
L += ['', f'### Reaches at least one prompt — {len(re_)}', '']
for r in re_:
    L.append(f'- **{r["owner"]} · {r["field"]}**')
    if r.get('which_prompts'):
        L.append(f'    - reaches: {r["which_prompts"]}')
    if r.get('consequence'):
        L.append(f'    - note: {r["consequence"]}')

lr = o['ledger_reach']
L += ['', '## The event ledger, traced', '', '### Receives it', '']
L += [f'- {x}' for x in lr['prompts_that_receive_it']]
L += ['', '### Does not receive it', '']
L += [f'- {x}' for x in lr['prompts_that_do_not']]
L += ['', '### Consequence', '', lr['consequence'], '']

w = o['windowing']
L += ['## Windowing', '']
for k in ('budget_chars', 'real_transcript_size', 'turns_elided', 'what_is_lost'):
    L += [f'### {k.replace("_", " ")}', '', w[k], '']

open(f'{DEST}/SCHEMATIC.md', 'w').write('\n'.join(L))


print(f'schematic.md  {len(chr(10).join(L)):,} bytes  ({total_in} IN / {total_out} OUT rows)')
print(f'maps: {len(os.listdir(DEST + "/data/maps"))}  verification: {len(os.listdir(DEST + "/data/verification"))}')
