# Windows Python 3.12 test-suite audit - 2026-09-01

Current `main` does not reproduce the historical count of twelve Windows
failures. On the repository's documented Windows UTF-8 setup, the full suite
collected 1,239 tests: **1,235 passed and four failed**. All four failures share
one test-harness encoding defect in `tests/test_cli_modes.py`; the child CLI
processes themselves exited successfully and produced the expected output.

No failure was line-ending-sensitive. No production defect was found. This
audit changes no production or test file.

## Tested revision and environment

| Setting | Value |
|---|---|
| Base revision | `eb0ea96280e8ca97150fe5ce3b174d280ddee0f1` (`origin/main`) |
| OS | Microsoft Windows 11 Home, version `10.0.26200`, build `26200`, 64-bit |
| Shell | Windows PowerShell `5.1.26100.9168` (`Desktop`) |
| Console code page | `850` |
| Python | CPython `3.12.10`, 64-bit |
| Python executable | `<worktree>\.venv\Scripts\python.exe` |
| `config.py` | absent |
| `WARGAME_LLM` | unset |
| `PYTHONIOENCODING` | `utf-8`, as documented in `README.md` and `GEMINI.md` |
| `PYTHONUTF8` | unset |
| Python UTF-8 mode | off (`sys.flags.utf8_mode == 0`) |
| Locale-preferred encoding | `cp1252` |
| Python stdin/stdout/stderr | `utf-8` after setting `PYTHONIOENCODING` |
| Filesystem/default encoding | `utf-8` |

The API requirements were installed as well as the core requirements so the
API modules were exercised rather than skipped.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r api/requirements.txt pytest httpx
$env:PYTHONIOENCODING = "utf-8"
Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m pytest tests/
```

Installed packages:

```text
annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.14.2
certifi==2026.7.22
charset-normalizer==3.5.1
click==8.1.7
colorama==0.4.6
fastapi==0.135.1
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.19
iniconfig==2.3.0
markdown-it-py==4.2.0
mdurl==0.1.2
packaging==26.3
pluggy==1.6.0
pydantic==2.7.3
pydantic_core==2.18.4
Pygments==2.21.0
pytest==9.1.1
python-multipart==0.0.32
PyYAML==6.0.2
requests==2.32.3
rich==13.7.1
shellingham==1.5.4
sse-starlette==3.4.8
starlette==1.6.0
typer==0.12.4
typing-inspection==0.4.4
typing_extensions==4.16.0
urllib3==2.7.0
uvicorn==0.52.4
```

## Full-suite result

```text
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
collected 1239 items
first complete run:  4 failed, 1235 passed, 976 warnings in 93.70s
verification repeat: 4 failed, 1235 passed, 976 warnings in 100.83s
```

| Failure | Classification | Evidence-backed cause |
|---|---|---|
| `tests/test_cli_modes.py::test_original_cli_works` | Product/test defect - test harness | The CLI exited `0`. Its valid UTF-8 help output was decoded as cp1252 by `subprocess.run(text=True)`, the reader thread raised `UnicodeDecodeError` on byte `0x90`, and `result.stdout` remained `None`. |
| `tests/test_cli_modes.py::test_dashboard_cli_works` | Product/test defect - test harness | Same UTF-8-child/cp1252-reader mismatch; the dashboard CLI exited `0`, then the assertion received `stdout=None`. |
| `tests/test_cli_modes.py::test_both_commands_available` | Product/test defect - test harness | Both help subprocesses use `text=True` without `encoding`; both reader threads failed before the command-parity assertions could inspect their successful output. |
| `tests/test_cli_modes.py::test_play_intro_smoke_non_tty` | Product/test defect - test harness | The intro CLI exited `0` and emitted the expected masthead and all three scene cards as UTF-8. The cp1252 reader failed on bytes `0x8f`/`0x90`, leaving `stdout=None`. |

Classification totals for the required run:

- line-ending-sensitive: **0**;
- environment/configuration: **0**;
- product/test defect: **4**, all test-harness defects with one root cause;
- confirmed production defects: **0**.

The Windows locale is the trigger, but not the root defect. The documented
setup deliberately makes the child write UTF-8. Python's `subprocess` text
mode still uses the locale encoding when the caller omits `encoding`, so these
tests ask a cp1252 reader to decode UTF-8 bytes. The working subprocess
convention already present in `tests/test_turn_loop_integration.py` sets the
child environment and also passes `encoding="utf-8"` to `subprocess.run`.

## Root-cause controls

The following diagnostics did not alter repository files.

### Successful child output, failed implicit decoding

With the documented `PYTHONIOENCODING=utf-8` environment, a byte-mode run of
`python -m cli.main --help` recorded:

```text
parent_locale_encoding=cp1252
child_returncode=0
stdout_bytes=2465
stderr_bytes=0
cp1252_replacement_count=3
cp1252_undefined_bytes=[144]
utf8_decode_contains_FALSE_FLAG=True
explicit_utf8_returncode=0
explicit_utf8_contains_FALSE_FLAG=True
```

The corresponding intro-only run recorded:

```text
child_returncode=0
stdout_bytes=14434
stderr_bytes=0
cp1252_replacement_count=8
cp1252_undefined_bytes=[143, 144]
utf8_has_masthead=True
utf8_has_three_scenes=True
```

As a diagnostic control, enabling Python UTF-8 mode makes the test process's
implicit subprocess decoder UTF-8 too:

```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe -m pytest tests/test_cli_modes.py -q
```

```text
8 passed, 1 warning in 7.90s
```

This control isolates the decoding mismatch; it is not a recommendation to
replace the documented setup with another global environment switch.

### Existing explicit-UTF-8 subprocess convention

The four real CLI runs behind the integration module explicitly configure both
ends of the text transport. They pass on the same machine with only the
documented environment enabled:

```powershell
$env:PYTHONIOENCODING = "utf-8"
Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m pytest tests/test_turn_loop_integration.py -q -s
```

```text
cancel-run: 0.9s
full-turn-run: 0.9s
load-autosave-run: 1.0s
reload-turn2-run: 0.8s
5 passed in 3.76s
```

### Historical cp1252 child failure

The [issue comment from PR #145](https://github.com/earlyprototype/false-flag/issues/135#issuecomment-5501573548)
reported that `test_play_intro_smoke_non_tty` failed when the child used its
default cp1252 stdio, while the four integration subprocesses passed with an
explicit UTF-8 environment. Both observations still reproduce.

Removing the documented UTF-8 environment and running only the intro smoke
test produced one failure in 3.17 seconds: the child exited `1` with
`UnicodeEncodeError` when cp1252 tried to encode the box-drawing string
`"\u2500\u2500"`. This is an environment/configuration failure in the unsupported
negative control, not a production failure in the required run.

## Line-ending check

The relevant files are stored and checked out as LF, as required by
`.gitattributes`:

```text
i/lf  w/lf  attr/text=auto eol=lf  README.md
i/lf  w/lf  attr/text=auto eol=lf  GEMINI.md
i/lf  w/lf  attr/text=auto eol=lf  tests/test_cli_modes.py
i/lf  w/lf  attr/text=auto eol=lf  tests/test_turn_loop_integration.py
```

No failed assertion compared line endings, and the failure traces end in
encoding exceptions before output assertions can run. The earlier broad
"EOL/environment" label is therefore not supported for the four current
failures.

## Historical result and follow-up

The issue's historical count of twelve failures is **not reproduced** on the
tested revision. The issue does not preserve the twelve test node IDs, so no
claim can be made about which historical nodes disappeared; the current,
enumerated result is four failures with one root cause.

Smallest independent follow-up: [issue #155](https://github.com/earlyprototype/false-flag/issues/155),
**"Make Windows CLI subprocess captures explicitly UTF-8"**. Apply the
established convention to the subprocess calls in `tests/test_cli_modes.py`:
give the child a UTF-8 environment and give `subprocess.run`
`encoding="utf-8"`. Do not change production rendering to satisfy a test pipe.

Documentation drift: `GEMINI.md` currently presents
`PYTHONIOENCODING=utf-8` as sufficient for the Windows pytest command. It is
not sufficient until the affected test subprocess readers also use explicit
UTF-8. `README.md`'s use of the variable for launching the game itself remains
valid.

## Residual risks

- GitHub CI runs on Ubuntu only, so it does not gate this Windows locale path.
- `pytest` and `httpx` are unpinned install arguments; their exact audited
  versions are recorded above, but a future fresh install may resolve newer
  versions.
- This run covers one Windows 11/cp1252 locale and CPython 3.12.10. It does not
  establish behavior for every Windows locale or older Python release.
- The 976 warnings were recorded but not triaged because issue #135 concerns
  test failures; most are existing Pydantic deprecations.
