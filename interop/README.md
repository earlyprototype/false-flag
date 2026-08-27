# interop — False Flag ↔ SEDL correspondence profile

A DTDL v3 model set (`models/`, namespace `dtmi:falseflag:...`) approximating
the published shape of Nuwa's SEDL, plus an exporter that writes False Flag
scenarios and runs into it. Not claimed SEDL-conformant — the spec is
unpublished; `CORRESPONDENCE.md` has the mapping, divergences, open questions.

## Use (from the false-flag repo root)
    python interop/validate_dtdl.py       # validate the model set
    python interop/export_run.py capture  # record a 4-turn deterministic mock campaign
    python interop/export_run.py export   # write exercise + run-telemetry documents
    python interop/test_interop.py        # self-check models + sample_export

Sample output is in `sample_export/` (exercise document, run telemetry, raw
run record, engine call/state logs).

## Validation status
Structural validation by `validate_dtdl.py` (stdlib: DTMI grammar, @context,
@type rules, content types, schema whitelist, enum shape, relationship target
resolution): 13 interfaces, zero errors. Pending: official DTDLParser (NuGet) — no .NET SDK here.
