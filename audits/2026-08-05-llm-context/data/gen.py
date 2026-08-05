#!/usr/bin/env python3
"""Generate the FALSE FLAG LLM schematic from the audit data.

Rendered from the structured audit rather than hand-written, so every input
row, source and bound survives verbatim instead of being summarised away.
"""
import json, html, os

SRC = '/tmp/claude-0/-home-user-false-flag/626a8206-8ea1-556d-9831-1103e7e56d4a/tasks/wgg1ffhaj.output'
OUT = '/tmp/claude-0/-home-user-false-flag/626a8206-8ea1-556d-9831-1103e7e56d4a/schematic.html'

data = json.load(open(SRC))['result']
groups = {g['group']: g['map']['calls'] for g in data['full']}
orphans = data['orphans']

# Reviewer corrections, keyed to the call they concern. The call maps below are
# first-pass output; these overturn or correct parts of them, and must travel
# with the map rather than sit in a separate file nobody opens.
CORR = {}
for g in data['full']:
    for r in (g.get('verdict') or {}).get('refutations', []):
        CORR.setdefault(g['group'], []).append(r)


def corrections_for(cid, name):
    """Refutations whose claim names this call."""
    keys = [cid.lower(), cid.split('.')[-1].lower()]
    out = []
    for grp, rs in CORR.items():
        for r in rs:
            c = r['claim'].lower()
            if any(k in c for k in keys if len(k) > 3):
                out.append(r)
    return out

def call(gid, cid):
    for c in groups[gid]:
        if c['call_id'] == cid:
            return c
    raise KeyError(f"{gid}/{cid}")

e = html.escape

# ---------------------------------------------------------------- tab layout
# The omissions scan is mapped twice; the 'omissions' group's version carries
# the fuller input trace, so the duplicate in 'decision' is dropped.
TABS = [
    ('turn',    'THE TURN',      None),
    ('dossier', 'SHARED DOSSIER', None),
    ('brief',   'BRIEFING',      [('inject', 'inject_generation'),
                                  ('discussion', 'narrator_bridge')]),
    ('disc',    'DISCUSSION',    [('discussion', 'advisor_qa')]),
    ('dec',     'DECISION',      [('decision', 'decision_interpretation'),
                                  ('decision', 'advisor_pushback'),
                                  ('omissions', 'critical_omissions.advisor_scan')]),
    ('adj',     'ADJUDICATION',  [('adjudication', 'ADJ-1'),
                                  ('adjudication', 'ADJ-2'),
                                  ('adjudication', 'ADJ-3')]),
    ('ext',     'EXTERNAL',      [('actors', 'state_actor_response'),
                                  ('actors', 'diplomacy_conversation_reply'),
                                  ('actors', 'diplomacy_outcome_assessment')]),
    ('win',     'WINDOWS',       None),
    ('dead',    'DEAD ENDS',     None),
    ('corr',    'CORRECTIONS',   None),
    ('issues',  'ISSUES',        None),
]


def render_corrections():
    total = sum(len(v) for v in CORR.values())
    out = ['<p class="lede">The call maps were traced once and reviewed a second time. '
           f'<b>{total} claims from the first pass were overturned or corrected</b> and the '
           'corrections are authoritative &mdash; where one contradicts a row in the phase tabs, '
           'the correction is what holds. Most are wrong line references; the ones marked '
           'REFUTED overturn a substantive claim. Corrections that name a specific call also '
           'appear beneath that call.</p>']
    for grp in sorted(CORR):
        rs = CORR[grp]
        out.append(f'<h3>{e(grp)} &mdash; {len(rs)}</h3>')
        out.append('<div class="ilist">')
        for r in rs:
            out.append('<div class="irow warnrow">'
                       f'<div class="idata">{e(r["verdict"])} &mdash; {e(r["claim"])}</div>'
                       + (f'<div class="isrc"><b>correction</b> {e(r["correction"])}</div>'
                          if r.get('correction') else '')
                       + f'<div class="iev"><b>evidence</b> {e(r.get("evidence",""))}</div>'
                       '</div>')
        out.append('</div>')
    return ''.join(out)


def meta_row(label, value):
    if not value:
        return ''
    return (f'<div class="mrow"><div class="mk">{e(label)}</div>'
            f'<div class="mv">{e(str(value))}</div></div>')


def render_call(c):
    ins = c.get('inputs', [])
    got = [i for i in ins if i.get('reaches_prompt')]
    absent = [i for i in ins if not i.get('reaches_prompt')]

    def inrow(i, present):
        cls = 'irow' if present else 'irow gone'
        bound = i.get('bounded_by') or ''
        return (f'<div class="{cls}">'
                f'<div class="idata">{e(i["data"])}</div>'
                f'<div class="isrc"><b>source</b> {e(i["source"])}</div>'
                + (f'<div class="ibound"><b>bound</b> {e(str(bound))}</div>' if bound else '')
                + f'<div class="iev"><b>evidence</b> {e(i.get("evidence",""))}</div>'
                f'</div>')

    parts = [f'<section class="call" id="c-{e(c["call_id"])}">']
    parts.append(f'<h3>{e(c["name"])}</h3>')
    parts.append(f'<p class="cid">{e(c["call_id"])}</p>')

    parts.append('<div class="meta">')
    parts.append(meta_row('prompt built at', c.get('prompt_builder')))
    parts.append(meta_row('dispatched at', c.get('dispatch_site')))
    parts.append(meta_row('llm context', c.get('llm_context')))
    parts.append(meta_row('model tier', c.get('model_tier')))
    parts.append(meta_row('calls per turn', c.get('calls_per_turn')))
    parts.append(meta_row('concurrency', c.get('concurrency')))
    parts.append(meta_row('on failure', c.get('failure_behaviour')))
    parts.append('</div>')

    parts.append('<h4>Why this call exists</h4>')
    parts.append(f'<p class="why">{e(c["game_purpose"])}</p>')

    if c.get('output_shape'):
        parts.append('<h4>What it must return</h4>')
        parts.append(f'<p class="why">{e(c["output_shape"])}</p>')
    if c.get('consumed_by'):
        parts.append(f'<p class="ev">parsed at {e(c["consumed_by"])}</p>')

    parts.append(f'<h4>Data in &mdash; {len(got)} inputs reach the prompt</h4>')
    parts.append('<div class="ilist">' + ''.join(inrow(i, True) for i in got) + '</div>')

    if absent:
        parts.append(f'<h4 class="neg">Available but not sent &mdash; {len(absent)}</h4>')
        parts.append('<div class="ilist">' + ''.join(inrow(i, False) for i in absent) + '</div>')

    parts.append('<h4>What the output changes</h4>')
    parts.append('<ul class="aff">' + ''.join(f'<li>{e(a)}</li>' for a in c.get('affects', [])) + '</ul>')

    gaps = c.get('notable_gaps') or []
    if gaps:
        parts.append('<h4 class="neg">Observed gaps</h4>')
        parts.append('<ul class="aff gap">' + ''.join(f'<li>{e(g)}</li>' for g in gaps) + '</ul>')

    corr = corrections_for(c['call_id'], c['name'])
    if corr:
        parts.append(f'<h4 class="warn">Corrections against this block &mdash; {len(corr)}</h4>')
        parts.append('<div class="ilist">')
        for r in corr:
            parts.append('<div class="irow warnrow">'
                         f'<div class="idata">{e(r["verdict"])} &mdash; {e(r["claim"])}</div>'
                         + (f'<div class="isrc"><b>correction</b> {e(r["correction"])}</div>'
                            if r.get('correction') else '')
                         + f'<div class="iev"><b>evidence</b> {e(r.get("evidence",""))}</div>'
                         '</div>')
        parts.append('</div>')

    parts.append('</section>')
    return ''.join(parts)


# ------------------------------------------------------------ static panels
TURN = """
<p class="lede">A turn issues roughly fifteen dispatches across five phases. The order below is
the order the code runs them. Two structural facts govern everything after: eight of the twelve
call families open with the same shared dossier and are therefore mutually cacheable, and eight
of the twelve pass no context enum and therefore never consult the model configuration. These
are different eights.</p>

<figure>
<svg viewBox="0 0 880 740" role="img" aria-label="Sequence of LLM dispatches in one turn, grouped by phase, showing which run alone and which go out as a parallel group">
  <defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/></marker></defs>
  <text class="sh" x="0" y="30">BRIEFING</text><line class="lt" x1="0" y1="40" x2="150" y2="40"/>
  <text class="sh" x="0" y="200">DISCUSSION</text><line class="lt" x1="0" y1="210" x2="150" y2="210"/>
  <text class="sh" x="0" y="290">DECISION</text><line class="lt" x1="0" y1="300" x2="150" y2="300"/>
  <text class="sh" x="0" y="500">ADJUDICATION</text><line class="lt" x1="0" y1="510" x2="150" y2="510"/>

  <rect class="bf" x="190" y="14" width="300" height="40" rx="2"/><text class="sl" x="204" y="39">inject generation</text><text class="ss" x="470" y="39" text-anchor="end">0–1</text>
  <text class="ss" x="506" y="33">own context · ledger · no history</text>
  <line class="ln" x1="340" y1="54" x2="340" y2="76" marker-end="url(#ar)"/>
  <rect class="bf" x="190" y="78" width="300" height="40" rx="2"/><text class="sl" x="204" y="103">narrator bridge</text><text class="ss" x="470" y="103" text-anchor="end">0–1</text>
  <text class="ss" x="506" y="103">own context · last 20 lines, unbounded</text>
  <line class="ln" x1="340" y1="118" x2="340" y2="152" marker-end="url(#ar)"/>
  <rect class="bf" x="190" y="154" width="300" height="40" rx="2"/><text class="sl" x="204" y="179">diplomacy reply / outcome</text><text class="ss" x="470" y="179" text-anchor="end">0–2</text>
  <text class="ss" x="506" y="179">own context · no bound at all</text>
  <line class="ln" x1="340" y1="194" x2="340" y2="222" marker-end="url(#ar)"/>

  <g class="gd"><rect class="bf" x="190" y="224" width="300" height="40" rx="2"/><text class="sl" x="204" y="249">advisor Q&amp;A</text><text class="ss" x="470" y="249" text-anchor="end">≥1 per question</text></g>
  <text class="ss" x="506" y="249">shared dossier</text>
  <line class="ln" x1="340" y1="264" x2="340" y2="312" marker-end="url(#ar)"/>

  <g class="gd"><rect class="bf" x="190" y="314" width="300" height="40" rx="2"/><text class="sl" x="204" y="339">decision interpretation</text><text class="ss" x="470" y="339" text-anchor="end">1</text></g>
  <text class="ss" x="506" y="333">shared dossier · writes the cache</text>
  <text class="ss" x="506" y="347">output never parsed</text>
  <line class="ln" x1="340" y1="354" x2="340" y2="376" marker-end="url(#ar)"/>
  <g class="gd"><rect class="bf" x="190" y="378" width="300" height="40" rx="2"/><text class="sl" x="204" y="403">advisor pushback</text><text class="ss" x="470" y="403" text-anchor="end">1</text></g>
  <text class="ss" x="506" y="403">shared dossier · mutates nothing</text>
  <line class="ln" x1="340" y1="418" x2="340" y2="440" marker-end="url(#ar)"/>

  <g class="gd">
    <line class="ln" x1="190" y1="446" x2="490" y2="446"/>
    <line class="ln" x1="230" y1="446" x2="230" y2="458"/><line class="ln" x1="285" y1="446" x2="285" y2="458"/>
    <line class="ln" x1="340" y1="446" x2="340" y2="458"/><line class="ln" x1="395" y1="446" x2="395" y2="458"/>
    <line class="ln" x1="450" y1="446" x2="450" y2="458"/>
    <rect class="bf" x="206" y="458" width="48" height="28" rx="2"/><rect class="bf" x="261" y="458" width="48" height="28" rx="2"/>
    <rect class="bf" x="316" y="458" width="48" height="28" rx="2"/><rect class="bf" x="371" y="458" width="48" height="28" rx="2"/>
    <rect class="bf" x="426" y="458" width="48" height="28" rx="2"/>
    <text class="ss" x="506" y="463">critical omissions ×5 — one group</text>
    <text class="ss" x="506" y="477">can rewrite the decision and re-run all three</text>
  </g>
  <line class="ln" x1="340" y1="486" x2="340" y2="524" marker-end="url(#ar)"/>

  <g class="wn">
    <line class="ln" x1="245" y1="530" x2="435" y2="530"/>
    <line class="ln" x1="245" y1="530" x2="245" y2="542"/><line class="ln" x1="340" y1="530" x2="340" y2="542"/><line class="ln" x1="435" y1="530" x2="435" y2="542"/>
    <rect class="bf" x="206" y="542" width="78" height="28" rx="2"/><rect class="bf" x="301" y="542" width="78" height="28" rx="2"/><rect class="bf" x="396" y="542" width="78" height="28" rx="2"/>
    <text class="ss" x="506" y="560">state actors ×3 — moves metrics 40%</text>
  </g>
  <line class="ln" x1="340" y1="570" x2="340" y2="592" marker-end="url(#ar)"/>
  <g class="wn"><rect class="bf" x="190" y="594" width="300" height="40" rx="2"/><text class="sl" x="204" y="619">action quality assessment</text><text class="ss" x="470" y="619" text-anchor="end">1</text></g>
  <text class="ss" x="506" y="619">the call that moves the numbers</text>
  <line class="ln" x1="340" y1="634" x2="340" y2="652" marker-end="url(#ar)"/>
  <g class="wn">
    <line class="ln" x1="230" y1="658" x2="450" y2="658"/>
    <line class="ln" x1="230" y1="658" x2="230" y2="668"/><line class="ln" x1="303" y1="658" x2="303" y2="668"/>
    <line class="ln" x1="377" y1="658" x2="377" y2="668"/><line class="ln" x1="450" y1="658" x2="450" y2="668"/>
    <rect class="bf" x="206" y="668" width="48" height="26" rx="2"/><rect class="bf" x="279" y="668" width="48" height="26" rx="2"/>
    <rect class="bf" x="353" y="668" width="48" height="26" rx="2"/><rect class="bf" x="426" y="668" width="48" height="26" rx="2"/>
    <text class="ss" x="506" y="686">advisor reactions ×4 — mutates nothing</text>
  </g>
  <line class="ln" x1="340" y1="694" x2="340" y2="710" marker-end="url(#ar)"/>
  <g class="wn"><rect class="bf" x="190" y="712" width="300" height="26" rx="2"/><text class="sl" x="204" y="730">situation summary  ×1</text></g>
  <text class="ss" x="506" y="730">output reaches no prompt</text>
</svg>
<figcaption>Teal = opens with the shared dossier. Amber = builds its own context and passes no
context enum, so the model configuration does not apply. Fans are single parallel groups.</figcaption>
</figure>
"""

DOSSIER = """
<p class="lede">One block, assembled per prompt by <code>build_shared_context_prefix</code>
(<code>llm/context_builder.py:285-355</code>), used by advisor Q&amp;A, decision interpretation,
advisor pushback and the five omissions checks. Ordered slowest-changing first so a prefix cache
can match through it. On the measured campaign it renders to <b>306,649 characters</b>, and the
eight prompts built on it are <b>99.4% identical</b> to one another by byte comparison.</p>

<figure>
<svg viewBox="0 0 880 330" role="img" aria-label="Composition of the shared briefing dossier in order of how often each block changes">
  <defs><marker id="ar2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/></marker></defs>
  <text class="sh" x="0" y="16">ORDERED BY RATE OF CHANGE — SLOWEST FIRST</text>
  <rect class="bf" x="0" y="28" width="160" height="46" rx="2"/><text class="ss" x="12" y="48">fixed framing</text><text class="ss" x="12" y="64">never changes</text>
  <rect class="bf" x="164" y="28" width="180" height="46" rx="2"/><text class="ss" x="176" y="48">secret narrative truth</text><text class="ss" x="176" y="64">drawn once at setup</text>
  <g class="gd"><rect class="bf" x="348" y="28" width="300" height="46" rx="2"/><text class="ss" x="360" y="48">GAME HISTORY — the transcript</text><text class="ss" x="360" y="64">append-only · windowed to 320,000 chars</text></g>
  <g class="acc"><rect class="bf" x="652" y="28" width="228" height="46" rx="2"/><text class="ss" x="664" y="48">metrics · metrics · flags</text><text class="ss" x="664" y="64">every turn</text></g>
  <line class="ln" x1="0" y1="90" x2="880" y2="90"/><line class="ln" x1="0" y1="84" x2="0" y2="96"/><line class="ln" x1="880" y1="84" x2="880" y2="96"/>
  <text class="ss" x="0" y="112">cache matches from here &rarr;</text>
  <g class="acc"><text class="ss" x="652" y="112">&larr; and stops here</text></g>

  <text class="sh" x="0" y="156">THE LAST BLOCK IS THE SAME THREE NUMBERS, THREE TIMES</text>
  <rect class="bf" x="0" y="168" width="270" height="40" rx="2"/><text class="ss" x="12" y="193">Escalation / Domestic / Alliance, raw /100</text>
  <line class="ln" x1="270" y1="188" x2="304" y2="188" marker-end="url(#ar2)"/>
  <rect class="bf" x="306" y="168" width="270" height="40" rx="2"/><text class="ss" x="318" y="193">the same three as prose bands</text>
  <line class="ln" x1="576" y1="188" x2="610" y2="188" marker-end="url(#ar2)"/>
  <g class="acc"><rect class="bf" x="612" y="168" width="268" height="40" rx="2"/><text class="ss" x="624" y="188">KEY INTELLIGENCE FLAGS —</text><text class="ss" x="624" y="202">five booleans thresholded from them</text></g>
  <text class="ss" x="0" y="234">engine/flags.py:38-40 replaces the flags dict each turn rather than accumulating, so it holds nothing the two renderings above do not.</text>

  <text class="sh" x="0" y="272">NOT IN THIS BLOCK</text>
  <text class="ss" x="0" y="294">per-country FactionStance — to_llm_context() is called with no country argument (llm/context_builder.py:323), skipping models/narrative.py:46-67</text>
  <text class="ss" x="0" y="312">the event ledger · the situation summary · world.posture · world.spatial_state · world.diplomatic_relationships</text>
</svg>
<figcaption>Nothing above the transcript may vary between calls in a turn: a line count in the
history header alone cut the matchable prefix from 75.9% to 60.2%, because the advisor question
is asked before the decision is interpreted and the two calls see different transcript lengths.</figcaption>
</figure>
"""

WINDOWS = """
<p class="lede">Every bound applied to data on its way into a prompt, and the measured effect of
the one that binds hardest.</p>

<figure>
<svg viewBox="0 0 880 300" role="img" aria-label="Turn strip showing which turns of a seventeen turn campaign survive the 320,000 character window">
  <defs><marker id="ar3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/></marker></defs>
  <text class="sh" x="0" y="18">AS PLAYED — 729,186 CHARACTERS · 1,853 LINES · 17 COMPLETED TURNS</text>
  <rect class="bf" x="0" y="30" width="46" height="32" rx="1"/><text class="ss" x="14" y="51">1</text>
  <rect class="bf" x="48" y="30" width="464" height="32" rx="1"/><text class="ss" x="60" y="51">turns 2 – 11   ·   1,099 lines</text>
  <rect class="bf" x="514" y="30" width="366" height="32" rx="1"/><text class="ss" x="526" y="51">turns 12 – 17   ·   272,819 chars</text>
  <line class="ln" x1="440" y1="70" x2="440" y2="102" marker-end="url(#ar3)"/>
  <text class="ss" x="452" y="90">MAX_ADVISOR_TRANSCRIPT_CHARS = 320,000 · head share 0.2 = 64,000</text>
  <text class="sh" x="0" y="128">RENDERED INTO EVERY DOSSIER-CARRYING PROMPT — 306,649 CHARACTERS</text>
  <g class="gd"><rect class="bf" x="0" y="140" width="46" height="32" rx="1"/><text class="ss" x="14" y="161">1</text>
  <rect class="bf" x="514" y="140" width="366" height="32" rx="1"/><text class="ss" x="526" y="161">turns 12 – 17</text></g>
  <g class="acc"><rect class="bx" x="48" y="140" width="464" height="32" rx="1" stroke-dasharray="5 4"/>
  <text class="ss" x="60" y="161">[... 1,099 lines of mid-campaign history elided for length ...]</text></g>
  <text class="ss" x="0" y="204">Head stops after turn 1: turn 2 alone spans 39,914 chars, and 33,517 + 39,914 exceeds the 64,000 head budget.</text>
  <text class="ss" x="0" y="222">Tail holds turns 12–17 at 272,819 against a 286,483 budget. 13,351 characters go unspent — both loops stop on whole-turn boundaries.</text>
  <text class="ss" x="0" y="254">The prompts built on this block instruct: "Reference past warnings or decisions from the conversation history if relevant</text>
  <text class="ss" x="0" y="272">(e.g. 'As I warned in Turn 2...')" — and turn 2 is inside the elision.</text>
</svg>
</figure>

<h3>Every bound in the pipeline</h3>
<div class="ilist">
<div class="irow"><div class="idata">Campaign transcript into all eight dossier-carrying prompts</div><div class="isrc"><b>bound</b> MAX_ADVISOR_TRANSCRIPT_CHARS = 320,000 characters; head share 0.2 = 64,000; cut on TURN boundaries, middle replaced by one marker line</div><div class="iev"><b>evidence</b> llm/context_builder.py:27, :54, :207, :280, :326</div></div>
<div class="irow"><div class="idata">Last-turn window into the inject generator</div><div class="isrc"><b>bound</b> MAX_INJECT_CONTINUITY_LINES = 400 lines, then char-bounded by the same 320,000; over-long turns keep head 2/3 and tail 1/3 around an elision marker</div><div class="iev"><b>evidence</b> llm/context_builder.py:61, :114, :156-163</div></div>
<div class="irow"><div class="idata">Story digest into the inject generator</div><div class="isrc"><b>bound</b> last 3 event-ish lines only, each truncated to 100 characters; emitted only when the transcript exceeds 10 lines</div><div class="iev"><b>evidence</b> llm/context_builder.py:595-596 · llm/prompts.py:388</div></div>
<div class="irow"><div class="idata">Event ledger titles and notes</div><div class="isrc"><b>bound</b> title 60 chars (_LEDGER_TITLE_MAX), note 90 chars; entry COUNT deliberately unbounded</div><div class="iev"><b>evidence</b> llm/context_builder.py:64, :87-88 · engine/narrative_adjudication.py:158</div></div>
<div class="irow"><div class="idata">RECENT EVENTS into the omissions checks</div><div class="isrc"><b>bound</b> double-windowed to 5 inject titles; falls back to 3 flag names, then to the literal "No recent major events"</div><div class="iev"><b>evidence</b> engine/sim_loop.py:392 · agents/conversation.py:353-356 · llm/prompts.py:494</div></div>
<div class="irow"><div class="idata">Recent events into reactions, summary and actors</div><div class="isrc"><b>bound</b> last 3 (NarrativeState.recent_events)</div><div class="iev"><b>evidence</b> models/narrative_state.py:256</div></div>
<div class="irow"><div class="idata">Number of state actors simulated</div><div class="isrc"><b>bound</b> 3 (max_actors)</div><div class="iev"><b>evidence</b> engine/narrative_adjudication.py:838</div></div>
<div class="irow"><div class="idata">Number of advisors reacting</div><div class="isrc"><b>bound</b> 4 (responders[:4])</div><div class="iev"><b>evidence</b> engine/narrative_adjudication.py:587</div></div>
<div class="irow gone"><div class="idata">Transcript tail into the narrator</div><div class="isrc"><b>bound</b> last 20 list elements — a bare literal, with NO character bound; one element can be a full unwrapped paragraph</div><div class="iev"><b>evidence</b> llm/prompts.py:587</div></div>
<div class="irow gone"><div class="idata">Filtered transcript into the diplomacy prompts</div><div class="isrc"><b>bound</b> none of any kind</div><div class="iev"><b>evidence</b> llm/context_builder.py:441-512</div></div>
<div class="irow gone"><div class="idata">Player decision text into interpretation, pushback, omissions, actors and the summary</div><div class="isrc"><b>bound</b> none — not truncated and not escaped</div><div class="iev"><b>evidence</b> llm/prompts.py:202, :277, :501 · engine/actor_simulation.py:32-85</div></div>
<div class="irow gone"><div class="idata">Scenario uk_forces, stockpiles, constraints, objectives, red_objectives</div><div class="isrc"><b>bound</b> none — str() of the whole sub-tree</div><div class="iev"><b>evidence</b> llm/prompts.py:113, :202, :277 · llm/prompts.py:362-363</div></div>
</div>
<p class="note">Rows in muted type carry no bound.</p>

<h3>Budget against the model</h3>
<p>The 320,000 figure is documented as leaving headroom inside a <b>128,000-token</b> context
window. Measured: the campaign is ~182,000 tokens whole; a full advisor prompt built from the
windowed block is 314,695 characters, ~78,700 tokens. A model whose window exceeds ~200,000
tokens would carry the campaign entire and the elision above would not occur.</p>
"""


def render_dead():
    rows = orphans['orphaned_state']
    unreached = [r for r in rows if not r.get('reaches_any_prompt')]
    reached = [r for r in rows if r.get('reaches_any_prompt')]
    out = ['<p class="lede">State the game maintains, and whether any prompt ever sees it. '
           f'<b>{len(unreached)} of {len(rows)}</b> audited fields reach no prompt at all.</p>']

    out.append(f'<h3 class="neg">Reaches no prompt &mdash; {len(unreached)}</h3>')
    out.append('<div class="ilist">')
    for r in unreached:
        out.append('<div class="irow gone">'
                   f'<div class="idata">{e(r["owner"])} &middot; <b>{e(r["field"])}</b></div>'
                   + (f'<div class="isrc"><b>consequence</b> {e(r["consequence"])}</div>' if r.get('consequence') else '')
                   + f'<div class="iev"><b>evidence</b> {e(r.get("evidence",""))}</div>'
                   '</div>')
    out.append('</div>')

    out.append(f'<h3>Reaches at least one prompt &mdash; {len(reached)}</h3>')
    out.append('<div class="ilist">')
    for r in reached:
        out.append('<div class="irow">'
                   f'<div class="idata">{e(r["owner"])} &middot; <b>{e(r["field"])}</b></div>'
                   + (f'<div class="isrc"><b>reaches</b> {e(r["which_prompts"])}</div>' if r.get('which_prompts') else '')
                   + (f'<div class="ibound"><b>note</b> {e(r["consequence"])}</div>' if r.get('consequence') else '')
                   + f'<div class="iev"><b>evidence</b> {e(r.get("evidence",""))}</div>'
                   '</div>')
    out.append('</div>')

    lr = orphans['ledger_reach']
    out.append('<h3>The event ledger, traced</h3>')
    out.append('<h4>Receives it</h4><ul class="aff">'
               + ''.join(f'<li>{e(x)}</li>' for x in lr['prompts_that_receive_it']) + '</ul>')
    out.append('<h4 class="neg">Does not receive it</h4><ul class="aff gap">'
               + ''.join(f'<li>{e(x)}</li>' for x in lr['prompts_that_do_not']) + '</ul>')
    out.append('<h4>Consequence</h4>')
    for para in lr['consequence'].split('\n\n'):
        if para.strip():
            out.append(f'<p class="why">{e(para.strip())}</p>')
    return ''.join(out)


ISSUES = """
<p class="lede">Issues observed while tracing the above. Ordered by consequence.</p>
<ul class="issues">
<li><b>An empty ledger removes the do-not-restage rule as well as the data.</b> Continuity rule 8
is appended only under <code>if event_ledger:</code>, and an empty list is falsy. Reachable on a
fresh campaign before the first event is recorded, and on any save written before the field
existed — persistence rebuilds the state with the empty default. The failure mode is unguarded
rather than degraded. <span class="ev">llm/prompts.py:422 · models/narrative_state.py:88 · engine/persistence.py:134</span></li>

<li><b>The decision interpretation is passed to the omissions check and never reaches the prompt.</b>
Five advisors judging whether a decision omitted something catastrophic work from the raw typed
text rather than the structured reading produced moments earlier for that purpose. Advisor
<code>personality</code> is read from config on the same path and likewise never interpolated.
<span class="ev">engine/sim_loop.py:569 · agents/conversation.py:376-381 · llm/prompts.py:462-553, :491</span></li>

<li><b>No prompt in the game holds both the campaign history and the event ledger.</b> The eight
prompts that lose ten turns to elision do not receive the ledger; the one prompt that receives it
carries no history block at all. The ledger would cost ~1,600 characters against 13,351 unspent.
<span class="ev">llm/context_builder.py:285-355 vs :391-439</span></li>

<li><b>Eight of twelve call families bypass the model configuration.</b> The narrator, quality
assessment, advisor reactions, situation summary and state actors pass no <code>context=</code>,
so the router leaves <code>model_name</code> None and the driver default applies.
<code>LLMContext.CHARACTER_RESPONSE</code> is defined and mapped to FLASH but has zero live call
sites — <code>generate_group</code> is invoked positionally at the reactions call site. There is
no <code>STATE_ACTOR</code> member at all. The per-context tier table and the <code>/llm</code>
menu therefore govern the discussion, decision, inject and diplomacy families only.
<span class="ev">llm/router.py:231-234, :331-335 · llm/model_config.py:10-38 · engine/narrative_adjudication.py:545 · engine/actor_simulation.py:131</span></li>

<li><b>The effects parser can absorb prose from the reasoning paragraph.</b> The branch fires on
any line containing a colon and the substring escalation, alliance or stability, so a continuation
line of REASONING matching that shape is read as a metric effect. A multiplier that parses to
exactly 1.0, or is absent, is overridden by the quality-to-multiplier table.
<span class="ev">engine/narrative_adjudication.py:374-381, :383-399</span></li>

<li><b>Advisor trust updates on one adjudication path only.</b>
<code>_update_character_attitudes</code> is called on the narrative path and never on the
actor-simulation path, so trust responds to decision quality in one mode and not the other. The
two paths also derive base effects differently — LLM-suggested effects on one, a keyword
heuristic merged 60/40 with actor effects on the other.
<span class="ev">engine/narrative_adjudication.py:788, :928-943, :865-876</span></li>

<li><b>Two context builders apply no size limit.</b> The diplomacy context bounds its filtered
transcript not at all; the narrator takes the last 20 elements with no character cap, where one
element can be an unwrapped paragraph. Both share the shape of the overrun already corrected in
the advisor window, where 400 long lines reached 792,572 characters against a 320,000 budget.
<span class="ev">llm/context_builder.py:441-512 · llm/prompts.py:587</span></li>

<li><b>The three metrics appear three times in every dossier-carrying prompt.</b> Raw values,
prose bands, and KEY INTELLIGENCE FLAGS — five booleans thresholded from those same metrics, in a
dict replaced rather than accumulated each turn.
<span class="ev">llm/context_builder.py:335-341, :351-352 · engine/flags.py:15-40</span></li>

<li><b>The situation summary costs a call per turn and reaches no prompt.</b> It overwrites a
field read only by emergent-mode display and three CLI render sites, is absent from
<code>to_llm_context()</code>, and is not written to the save transcript. It also does not
receive the previous summary it replaces.
<span class="ev">engine/narrative_adjudication.py:675-689 · models/narrative_state.py:233-234</span></li>

<li><b>Requested output constraints are dropped on some drivers.</b> The narrator passes
<code>system_instruction</code>, <code>temperature</code> and <code>max_tokens=150</code>; none is
honoured on the gemini, mock or offline drivers, so the length cap is not enforced.
<span class="ev">engine/narrator.py:39-41</span></li>

<li><b>Inject generation can fire twice in one turn on a resumed save.</b> The generation branch
in <code>run_turn_briefing</code> has no <code>replay</code> guard — <code>replay</code> is
consulted only for effects and the diplomatic encounter. Loading a save taken mid-turn re-runs
the briefing with <code>replay=True</code>, so a second event is generated and a second ledger
entry written for the same turn.
<span class="ev">engine/sim_loop.py:311-324, :384, :396 · cli/main.py:729, :859</span></li>

<li><b>The secret narrative truth is absent from every prompt outside Mystery Mode.</b>
<code>world.narrative</code> is <code>None</code> on the default game type, so the SECRET
NARRATIVE CONTEXT block is skipped in the shared dossier, the inject prompt and the state-actor
prompt alike. Where it is present it is interpolated with no length bound.
<span class="ev">engine/game_manager.py:91-92 · cli/main.py:497 · llm/context_builder.py:322-323, :415</span></li>

<li><b>Scripted faction stances and the state-actor roster barely intersect.</b> Stances are
defined for RUS, USA, CHN and IRL; the state actors are USA, FRA, DEU, POL and RUS. Only USA and
RUS appear in both, so CHN and IRL have stances no actor can voice, and FRA, DEU and POL respond
with no scripted stance behind them — on top of stances reaching no prompt at all.
<span class="ev">data/scenarios/war_game_2025/narratives.yaml · data/state_actors.yaml:5, 36, 69, 99</span></li>

<li><b>Per-country faction stances never reach any prompt.</b>
<code>NarrativeConfig.to_llm_context()</code> is always called without a country argument, so
secret motive, public posture, economic leverage and intelligence-sharing level are skipped
everywhere — including in the state-actor prompt, where the actor's own hidden agendas are sent
but its scripted stance is not.
<span class="ev">llm/context_builder.py:323 · models/narrative.py:46-67</span></li>

<li><b>Advisor pushback mutates nothing.</b> No metric, flag, trust value or ledger entry is
written from it anywhere in the codebase; it drives the confirm gate and the transcript only. In
the API path every entry is given the canned recommendation "Consider revising your approach."
<span class="ev">engine/game_manager.py:213-219</span></li>

<li><b>The state-actor prompt carries UK internal advisor trust.</b> Every UK advisor's name,
relationship label and trust score is interpolated into the prompt sent as a foreign government's
private view. <span class="ev">engine/actor_simulation.py:32-85</span></li>
</ul>
"""

# ------------------------------------------------------------------- assemble
panels = []
navs = []
for i, (tid, label, calls) in enumerate(TABS):
    navs.append(f'<button class="tab{" on" if i == 0 else ""}" data-t="{tid}" '
                f'role="tab" aria-selected="{"true" if i==0 else "false"}" '
                f'aria-controls="p-{tid}" id="t-{tid}">{e(label)}</button>')
    if tid == 'turn':
        body = TURN
    elif tid == 'dossier':
        body = DOSSIER
    elif tid == 'win':
        body = WINDOWS
    elif tid == 'dead':
        body = render_dead()
    elif tid == 'corr':
        body = render_corrections()
    elif tid == 'issues':
        body = ISSUES
    else:
        body = ''.join(render_call(call(g, c)) for g, c in calls)
    panels.append(f'<div class="panel{" on" if i == 0 else ""}" id="p-{tid}" '
                  f'role="tabpanel" aria-labelledby="t-{tid}">{body}</div>')

CSS = """
:root{--ground:#F1FAEE;--panel:#E7F1E6;--ink:#10171C;--muted:#5C6E7A;--rule:#C4D3CE;
--accent:#D8481B;--good:#00785C;--warn:#9A6B00;--steel:#1A659E;
--mono:ui-monospace,"SF Mono","JetBrains Mono",Menlo,Consolas,monospace;
--serif:Charter,Georgia,"Iowan Old Style","Times New Roman",serif}
@media (prefers-color-scheme:dark){:root{--ground:#0B0F14;--panel:#131A21;--ink:#E8EFF2;
--muted:#8598A5;--rule:#26333D;--accent:#FF6B35;--good:#00D9A3;--warn:#FFB627;--steel:#4E9FD4}}
:root[data-theme="light"]{--ground:#F1FAEE;--panel:#E7F1E6;--ink:#10171C;--muted:#5C6E7A;
--rule:#C4D3CE;--accent:#D8481B;--good:#00785C;--warn:#9A6B00;--steel:#1A659E}
:root[data-theme="dark"]{--ground:#0B0F14;--panel:#131A21;--ink:#E8EFF2;--muted:#8598A5;
--rule:#26333D;--accent:#FF6B35;--good:#00D9A3;--warn:#FFB627;--steel:#4E9FD4}

body{background:var(--ground);color:var(--ink);font-family:var(--serif);font-size:16px;
line-height:1.58;margin:0;padding:0 1.4rem 6rem}
.wrap{max-width:66rem;margin:0 auto}
header.mast{padding:3rem 0 1rem;border-bottom:2px solid var(--ink)}
.desig{font-family:var(--mono);font-size:.68rem;letter-spacing:.18em;text-transform:uppercase;
color:var(--accent);margin:0 0 .8rem}
h1{font-family:var(--mono);font-size:clamp(1.3rem,3.4vw,1.8rem);line-height:1.2;font-weight:600;
margin:0 0 .6rem;text-wrap:balance}
.sub{font-family:var(--mono);font-size:.74rem;color:var(--muted);margin:0}

nav.tabs{display:flex;flex-wrap:wrap;gap:0;margin:0 0 2rem;border-bottom:1px solid var(--rule);
position:sticky;top:0;background:var(--ground);z-index:5;padding-top:.6rem}
.tab{font-family:var(--mono);font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;
background:none;border:none;border-bottom:2px solid transparent;color:var(--muted);
padding:.7rem .85rem;cursor:pointer;margin-bottom:-1px}
.tab:hover{color:var(--ink)}
.tab.on{color:var(--ink);border-bottom-color:var(--accent)}
.tab:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.panel{display:none}
.panel.on{display:block}

.lede{color:var(--muted);max-width:40rem;margin:0 0 2rem}
p{margin:0 0 .9rem;max-width:44rem}
h3{font-family:var(--mono);font-size:1rem;font-weight:600;margin:3rem 0 .2rem;text-wrap:balance}
h4{font-family:var(--mono);font-size:.7rem;font-weight:600;letter-spacing:.11em;
text-transform:uppercase;color:var(--muted);margin:1.8rem 0 .5rem}
h4.neg{color:var(--accent)}
h3.neg{color:var(--accent)}
code{font-family:var(--mono);font-size:.85em;background:var(--panel);padding:.06em .3em;border-radius:2px}

.call{border-top:1px solid var(--rule);padding-top:.4rem;margin-bottom:4rem}
.cid{font-family:var(--mono);font-size:.68rem;color:var(--muted);margin:0 0 1rem}
.why{max-width:44rem}
.meta{margin:0 0 1.4rem;border-left:2px solid var(--rule);padding-left:1rem}
.mrow{display:grid;grid-template-columns:9.5rem 1fr;gap:.4rem 1rem;font-family:var(--mono);
font-size:.72rem;line-height:1.55;margin-bottom:.4rem;align-items:start}
.mk{color:var(--muted);letter-spacing:.06em;text-transform:uppercase;font-size:.64rem;padding-top:.12rem}
.mv{color:var(--ink)}

.ilist{display:flex;flex-direction:column;gap:.1rem;margin-bottom:.6rem}
.irow{border-left:2px solid var(--good);padding:.5rem 0 .55rem .85rem;font-size:.86rem}
.irow.gone{border-left-color:var(--accent);opacity:.82}
.irow.warnrow{border-left-color:var(--warn)}
h4.warn{color:var(--warn)}
.idata{font-weight:600;margin-bottom:.15rem}
.isrc,.ibound,.iev{font-family:var(--mono);font-size:.68rem;line-height:1.5;color:var(--muted)}
.isrc b,.ibound b,.iev b{color:var(--ink);font-weight:600;letter-spacing:.05em;
text-transform:uppercase;font-size:.62rem;margin-right:.35rem}
.iev{opacity:.8}
.ev{font-family:var(--mono);font-size:.68rem;color:var(--muted);display:block;margin-top:.4rem}
.note{font-family:var(--mono);font-size:.7rem;color:var(--muted)}

ul.aff{padding-left:1.1rem;margin:0 0 1rem;max-width:46rem}
ul.aff li{margin-bottom:.42rem;font-size:.9rem}
ul.aff.gap li{color:var(--muted)}
ul.issues{padding-left:1.1rem;max-width:46rem}
ul.issues li{margin-bottom:1.3rem}

figure{margin:2rem 0 2.4rem;padding:0;overflow-x:auto}
figure svg{display:block;width:100%;max-width:100%;height:auto;min-width:33rem;color:var(--ink)}
figcaption{font-family:var(--mono);font-size:.72rem;line-height:1.55;color:var(--muted);
margin-top:.8rem;max-width:40rem}
.sl{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;fill:currentColor}
.ss{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:10.5px;fill:currentColor;opacity:.66}
.sh{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;letter-spacing:.1em;
fill:currentColor;opacity:.55}
.bx{fill:none;stroke:currentColor;stroke-width:1.4}
.bf{fill:var(--panel);stroke:currentColor;stroke-width:1.4}
.ln{stroke:currentColor;stroke-width:1.4;fill:none}
.lt{stroke:currentColor;stroke-width:1;fill:none;opacity:.3}
.acc{color:var(--accent)}.gd{color:var(--good)}.wn{color:var(--warn)}.st{color:var(--steel)}
footer{margin-top:4rem;padding-top:1rem;border-top:1px solid var(--rule);
font-family:var(--mono);font-size:.7rem;color:var(--muted)}
"""

JS = """
(function(){
  var tabs=[].slice.call(document.querySelectorAll('.tab'));
  function show(id){
    tabs.forEach(function(t){
      var on=t.dataset.t===id;
      t.classList.toggle('on',on);
      t.setAttribute('aria-selected',on?'true':'false');
    });
    [].forEach.call(document.querySelectorAll('.panel'),function(p){
      p.classList.toggle('on',p.id==='p-'+id);
    });
    if(history.replaceState)history.replaceState(null,'','#'+id);
    window.scrollTo(0,0);
  }
  tabs.forEach(function(t){
    t.addEventListener('click',function(){show(t.dataset.t)});
    t.addEventListener('keydown',function(ev){
      var i=tabs.indexOf(t),n=null;
      if(ev.key==='ArrowRight')n=tabs[(i+1)%tabs.length];
      if(ev.key==='ArrowLeft')n=tabs[(i-1+tabs.length)%tabs.length];
      if(n){ev.preventDefault();n.focus();show(n.dataset.t)}
    });
  });
  var h=(location.hash||'').replace('#','');
  if(h&&document.getElementById('p-'+h))show(h);
})();
"""

doc = f"""<title>FALSE FLAG — LLM schematic</title>
<style>{CSS}</style>
<div class="wrap">
<header class="mast">
  <p class="desig">System schematic &middot; LLM context and routing</p>
  <h1>FALSE FLAG — every prompt, what enters it, and what it changes</h1>
  <p class="sub">repo at d197c44 &middot; branch claude/false-flag-game-ux-2j8rea &middot;
  measured against saves/parked_campaign4_borrowed_faces.json</p>
</header>
<nav class="tabs" role="tablist">{''.join(navs)}</nav>
{''.join(panels)}
<footer>Rendered from the traced call graph. <b>Green</b> rules mark data that reaches the
prompt, <b>orange</b> marks data that does not, <b>amber</b> marks a correction filed against the
block above it &mdash; the trace was reviewed a second time and a correction supersedes the row
it sits under. Line references inside corrections are the verified ones.</footer>
</div>
<script>{JS}</script>
"""

open(OUT, 'w').write(doc)
print(f"wrote {OUT}  ({len(doc):,} bytes)")
ncalls = sum(len(v) for v in groups.values())
print(f"call blocks rendered: {sum(len(c) for _,_,c in TABS if c)} of {ncalls} mapped")
print(f"orphan rows: {len(orphans['orphaned_state'])}")
