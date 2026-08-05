export const meta = {
  name: 'llm-context-audit',
  description: 'Map every LLM call in FALSE FLAG: what data goes in, from where, for what game purpose, what it affects — then adversarially verify each claim',
  phases: [
    { title: 'Map', detail: 'six auditors, one per call group' },
    { title: 'Refute', detail: 'adversarial check of every claim against the code' },
    { title: 'Orphans', detail: 'game state that reaches no prompt at all' },
    { title: 'Synthesise', detail: 'merge into one verified map' },
  ],
}

const REPO = '/home/user/false-flag'

const COMMON = `
You are auditing the repo at ${REPO} (branch claude/false-flag-game-ux-2j8rea, HEAD d197c44).
It is an LLM-driven UK political-military crisis wargame.

Read the ACTUAL CODE. Do not infer from names, docstrings or comments — docstrings in this
repo have been wrong before. Every claim you make must be backed by a file:line you have read.

Key files: llm/prompts.py (prompt builders), llm/context_builder.py (shared context assembly
and windowing), llm/router.py (dispatch), llm/fanout.py (group dispatch), llm/model_config.py,
agents/conversation.py, engine/sim_loop.py, engine/narrative_adjudication.py,
engine/actor_simulation.py, engine/narrator.py, engine/diplomacy.py, llm/inject_generator.py,
models/world.py, models/narrative_state.py.

CRITICAL for this audit: for EVERY piece of data you claim reaches a prompt, trace it all the
way from the state object that holds it to the f-string that interpolates it. If a parameter
exists in a signature but no caller ever passes it, that data DOES NOT reach the prompt — say
so explicitly. This is the single most important thing the audit must get right.

Also record, for each input, whether it is TRUNCATED or WINDOWED on the way in, with the exact
constant and value.
`

const CALL_SCHEMA = {
  type: 'object',
  required: ['group', 'calls'],
  properties: {
    group: { type: 'string' },
    calls: {
      type: 'array',
      items: {
        type: 'object',
        required: ['call_id', 'name', 'prompt_builder', 'dispatch_site', 'game_purpose',
                   'inputs', 'output_shape', 'consumed_by', 'affects', 'concurrency',
                   'failure_behaviour'],
        properties: {
          call_id: { type: 'string' },
          name: { type: 'string', description: 'plain-language name a player would recognise' },
          prompt_builder: { type: 'string', description: 'file:line of the function building the prompt' },
          dispatch_site: { type: 'string', description: 'file:line where the LLM is actually called' },
          llm_context: { type: 'string', description: 'LLMContext enum value, or "none" if not passed' },
          model_tier: { type: 'string' },
          calls_per_turn: { type: 'string' },
          game_purpose: { type: 'string', description: 'what this call is FOR, in player terms, one sentence' },
          inputs: {
            type: 'array',
            items: {
              type: 'object',
              required: ['data', 'source', 'reaches_prompt', 'evidence'],
              properties: {
                data: { type: 'string', description: 'what information this is' },
                source: { type: 'string', description: 'the state object and field it comes from' },
                bounded_by: { type: 'string', description: 'truncation/window constant and value, or "unbounded"' },
                reaches_prompt: { type: 'boolean' },
                evidence: { type: 'string', description: 'file:line proving it does or does not' },
              },
            },
          },
          output_shape: { type: 'string' },
          consumed_by: { type: 'string', description: 'file:line of the parser' },
          affects: {
            type: 'array',
            description: 'what changes in the game as a result — metrics, narrative state, on-screen text',
            items: { type: 'string' },
          },
          concurrency: { type: 'string', description: 'alone, or the group it goes out with' },
          failure_behaviour: { type: 'string' },
          notable_gaps: {
            type: 'array',
            description: 'data this call arguably SHOULD see but does not, with evidence',
            items: { type: 'string' },
          },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['refutations', 'confirmed_count'],
  properties: {
    confirmed_count: { type: 'number' },
    refutations: {
      type: 'array',
      items: {
        type: 'object',
        required: ['claim', 'verdict', 'evidence'],
        properties: {
          claim: { type: 'string' },
          verdict: { type: 'string', description: 'REFUTED or CORRECTED' },
          correction: { type: 'string' },
          evidence: { type: 'string', description: 'file:line' },
        },
      },
    },
  },
}

const GROUPS = [
  { key: 'discussion', what: 'The DISCUSSION phase: advisor Q&A (player asks an advisor a question) and the narrator bridge text between turns. Start at agents/conversation.py ask_advisor and engine/narrator.py.' },
  { key: 'decision', what: 'The DECISION phase: decision interpretation (parsing the player free-form order) and advisor pushback. Start at agents/conversation.py interpret_player_action and generate_advisor_pushback.' },
  { key: 'omissions', what: 'The CRITICAL OMISSIONS scan: five advisors checking what the player failed to do. Start at agents/conversation.py check_critical_omissions and llm/prompts.py build_critical_omissions_prompt. Pay special attention to the recent_events argument — trace exactly what it contains and where it comes from.' },
  { key: 'inject', what: 'INJECT GENERATION: the stochastic event that opens a turn. Start at llm/inject_generator.py and llm/prompts.py build_inject_generation_prompt. Trace the event_ledger argument in full — where it originates, what it contains, and what it changes in the prompt.' },
  { key: 'adjudication', what: 'ADJUDICATION: action quality assessment, advisor character responses to the adjudicated decision, and the situation summary refresh. Start at engine/narrative_adjudication.py.' },
  { key: 'actors', what: 'STATE ACTORS and DIPLOMACY: simulating foreign powers responses, and any diplomacy conversation calls. Start at engine/actor_simulation.py and engine/diplomacy.py.' },
]

phase('Map')

const mapped = await pipeline(
  GROUPS,
  g => agent(
    `${COMMON}\n\nMap this group of LLM calls exhaustively.\n\nGROUP: ${g.what}\n\n` +
    `For each distinct LLM call in the group, fill the schema. Be exhaustive about "inputs": ` +
    `list EVERY distinct piece of information in the built prompt, including the shared ` +
    `context prefix's contents broken out individually (framing, secret narrative truth, ` +
    `transcript, metrics, world state summary — each as its own input row with its own ` +
    `bounding). For "affects", trace what the parsed output actually mutates.`,
    { label: `map:${g.key}`, phase: 'Map', schema: CALL_SCHEMA }
  ),
  (result, g) => {
    if (!result) return null
    return agent(
      `${COMMON}\n\nYou are an adversarial reviewer. Below is another auditor's map of the ` +
      `"${g.key}" LLM calls. Your job is to REFUTE it, not to agree with it.\n\n` +
      `For every claim that a piece of data "reaches_prompt: true", verify by reading the code ` +
      `that it genuinely is interpolated into the final prompt string. For every ` +
      `"reaches_prompt: false", verify it really is absent. Check the file:line references ` +
      `actually say what is claimed. Check the "affects" claims against the parser and the ` +
      `state mutation. Check bounding constants and their values.\n\n` +
      `Default to REFUTED when you cannot confirm something from the code. Report only claims ` +
      `you found wrong, plus a count of those you confirmed.\n\n` +
      `THE MAP:\n${JSON.stringify(result, null, 2)}`,
      { label: `refute:${g.key}`, phase: 'Refute', schema: VERDICT_SCHEMA }
    ).then(v => ({ group: g.key, map: result, verdict: v }))
  }
)

phase('Orphans')

const orphans = await agent(
  `${COMMON}\n\nThis is the question the repo owner actually cares about: WHAT GAME STATE ` +
  `EXISTS BUT NEVER REACHES ANY PROMPT?\n\n` +
  `Enumerate every field on WorldState (models/world.py), NarrativeState ` +
  `(models/narrative_state.py), StateActorSystem (engine/actor_simulation.py) and the parsed ` +
  `initial_conditions. For each, determine whether its contents reach ANY LLM prompt, and if ` +
  `so which. Grep for each field name across llm/, agents/ and engine/ and follow the call ` +
  `chain to an f-string.\n\n` +
  `Pay particular attention to NarrativeState.event_ledger: establish exactly which prompts ` +
  `receive it and which do not, and what the consequence is when the transcript is windowed ` +
  `and middle turns are elided.\n\n` +
  `Also report: what is the transcript character budget, what is the actual size of a real ` +
  `long campaign transcript (check saves/parked_campaign4_borrowed_faces.json), and how many ` +
  `turns get elided as a result.`,
  {
    label: 'orphan-state',
    phase: 'Orphans',
    schema: {
      type: 'object',
      required: ['orphaned_state', 'ledger_reach', 'windowing'],
      properties: {
        orphaned_state: {
          type: 'array',
          items: {
            type: 'object',
            required: ['field', 'owner', 'reaches_any_prompt', 'evidence'],
            properties: {
              field: { type: 'string' },
              owner: { type: 'string' },
              reaches_any_prompt: { type: 'boolean' },
              which_prompts: { type: 'string' },
              consequence: { type: 'string', description: 'what the game loses by this being absent' },
              evidence: { type: 'string' },
            },
          },
        },
        ledger_reach: {
          type: 'object',
          required: ['prompts_that_receive_it', 'prompts_that_do_not', 'consequence'],
          properties: {
            prompts_that_receive_it: { type: 'array', items: { type: 'string' } },
            prompts_that_do_not: { type: 'array', items: { type: 'string' } },
            consequence: { type: 'string' },
          },
        },
        windowing: {
          type: 'object',
          required: ['budget_chars', 'real_transcript_size', 'turns_elided', 'what_is_lost'],
          properties: {
            budget_chars: { type: 'string' },
            real_transcript_size: { type: 'string' },
            turns_elided: { type: 'string' },
            what_is_lost: { type: 'string' },
          },
        },
      },
    },
  }
)

phase('Synthesise')

const good = mapped.filter(Boolean)

const synthesis = await agent(
  `${COMMON}\n\nYou are merging a verified audit of every LLM call in the game into one map.\n\n` +
  `Below are six group maps, each paired with an adversarial reviewer's refutations, plus an ` +
  `audit of game state that never reaches a prompt.\n\n` +
  `APPLY THE REFUTATIONS. Where a reviewer refuted or corrected a claim, use the reviewer's ` +
  `version, not the original. Where a claim was confirmed, keep it.\n\n` +
  `Produce a single coherent account, organised as the turn actually runs, that answers three ` +
  `questions for every call: WHAT DATA goes in (and from where, and how bounded), WHAT GAME ` +
  `PURPOSE it serves, and WHAT IT AFFECTS. Then a section on what state is orphaned and what ` +
  `the game loses by it.\n\n` +
  `Be concrete and quantitative. Flag every place where a call is working from less ` +
  `information than the game already has available.\n\n` +
  `AUDIT DATA:\n${JSON.stringify({ groups: good, orphans }, null, 2)}`,
  { label: 'synthesis', phase: 'Synthesise' }
)

return {
  synthesis,
  orphans,
  refutation_counts: good.map(g => ({
    group: g.group,
    confirmed: g.verdict ? g.verdict.confirmed_count : null,
    refuted: g.verdict ? g.verdict.refutations.length : null,
  })),
  full: good,
}
