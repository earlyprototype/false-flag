# interop — False Flag's twin model, in DTDL

A DTDL v3 model set (`models/`, namespace `dtmi:falseflag:...`) describing
False Flag's exercise domain in the open standard SEDL also builds on, plus
an exporter that writes False Flag scenarios and runs into it. Not claimed
SEDL-conformant — that spec is unpublished. The model set is rendered live
on the dataflow page's ◇ DTDL mode (see the repo README), where each engine
node badges with its interface and the unmapped gaps state their reasons.

## Use (from the false-flag repo root)
    python interop/validate_dtdl.py       # validate the model set
    python interop/export_run.py capture  # record a 4-turn deterministic mock campaign
    python interop/export_run.py export   # write exercise + run-telemetry documents
    python interop/test_interop.py        # self-check models + sample_export

Sample output is in `sample_export/` (exercise document, run telemetry, raw
run record, engine call/state logs).

## Validation status
Two layers, both clean as of 27 Aug 2026:
- `validate_dtdl.py` (stdlib structural checks: DTMI grammar, @context,
  @type rules, content types, schema whitelist, enum shape, relationship
  target resolution): 13 interfaces, zero errors.
- **Microsoft's official DTDLParser** (NuGet `DTDLParser`, .NET 8): PARSE OK —
  278 entities, 13 interfaces, zero errors. To re-run: a ~20-line console app
  calling `new ModelParser().Parse(files)` over `models/*.json`.
