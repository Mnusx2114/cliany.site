# QA GUIDE

## OVERVIEW
`qa/` is the project's test surface: shell-based integration checks for install health, CLI JSON output, error handling, and generated adapter behavior.

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Run everything | `run_all.sh` | serial suite runner with aggregate PASS/FAIL |
| Install / env smoke checks | `doctor_check.sh` | version, `doctor --json`, home-dir layout |
| Error-path validation | `test_errors.sh` | unknown commands, JSON error shape, exit codes |
| Generated adapter behavior | `test_commands.sh` | creates `test.com` adapter if needed |
| Explore command validation | `test_explore.sh` | missing CDP / missing LLM key paths |

## CONVENTIONS
- Tests are shell scripts, not pytest modules.
- Assertions rely on exit codes plus JSON validation through `python3 -m json.tool` or short Python snippets.
- Each script keeps local `PASS` / `FAIL` counters and exits non-zero on any failure.
- Tests assume `cliany-site` is installed on PATH and runtime state lives under `~/.cliany-site/`.

## ANTI-PATTERNS
- Do not document or add pytest-only workflows here unless the repo actually adopts pytest.
- Do not assume CI will run these; there is no in-repo CI pipeline today.
- Do not forget that `test_commands.sh` may create persistent home-dir adapter state (`test.com`).

## NOTES
- Best fit for regression checks after CLI-facing changes.
- These suites validate real command surfaces, so they are slower and more stateful than unit tests would be.
