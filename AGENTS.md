# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-25T12:39:50Z
**Commit:** ee9bbf6
**Branch:** master

## OVERVIEW
Python 3.11 CLI package that turns browser workflows into generated site-specific commands.
Core flow: inspect Chrome via CDP + AXTree, ask an LLM to plan actions, emit Click adapter code into `~/.cliany-site/adapters/`, then replay actions with JSON envelopes.

## STRUCTURE
```text
./
├── src/cliany_site/        # runtime package; CLI, browser, explorer, codegen, adapter loader
├── qa/                     # shell-based integration checks; no pytest suite
├── docs/walkthroughs/      # change notes / troubleshooting writeups
├── pyproject.toml          # package metadata; `cliany-site` console entry point
├── uv.lock                 # locked Python dependency graph
└── README.md               # user workflow, env setup, operational examples
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| CLI entry / command wiring | `src/cliany_site/cli.py` | `SafeGroup`, root `--json`, adapter registration |
| Built-in commands | `src/cliany_site/commands/` | `doctor`, `login`, `explore`, `list` |
| Browser / CDP connectivity | `src/cliany_site/browser/cdp.py` | assumes Chrome on `localhost:9222` |
| AXTree capture / selector map | `src/cliany_site/browser/axtree.py` | truncates long trees; emits `@ref`-style selector map |
| Workflow planning | `src/cliany_site/explorer/engine.py` | env loading, LLM setup, exploration loop |
| Prompt contract | `src/cliany_site/explorer/prompts.py` | strict JSON shape and URL rules |
| Generated adapter emission | `src/cliany_site/codegen/generator.py` | renders Click code + metadata.json |
| Dynamic adapter loading | `src/cliany_site/loader.py` | loads generated `commands.py` from home dir |
| Session persistence | `src/cliany_site/session.py` | stores cookies under `~/.cliany-site/sessions/` |
| Action replay / fuzzy element resolution | `src/cliany_site/action_runtime.py` | executes click/type/select/navigate/submit |
| QA coverage | `qa/*.sh` | shell suites; integration-oriented |

## CODE MAP
| Symbol | Type | Location | Refs | Role |
|--------|------|----------|------|------|
| `CDPConnection` | class | `src/cliany_site/browser/cdp.py` | 10 | shared Chrome/CDP entrypoint for doctor, login, explore |
| `WorkflowExplorer` | class | `src/cliany_site/explorer/engine.py` | 5 | LLM-guided workflow discovery loop |
| `AdapterGenerator` | class | `src/cliany_site/codegen/generator.py` | 6 | turns `ExploreResult` into generated Click adapters |
| `execute_action_steps` | function | `src/cliany_site/action_runtime.py` | 3 | replays recorded actions against live pages |
| `register_adapters` | function | `src/cliany_site/loader.py` | 3 | mounts generated domain commands on root CLI |
| `save_session` | async function | `src/cliany_site/session.py` | 3 | persists cookies from browser session |

## CONVENTIONS
- src-layout package only: import from `cliany_site.*`; no local path hacks or aliases.
- CLI commands are synchronous Click functions that call internal async helpers via `asyncio.run(...)`.
- Root `--json` flag propagates through `ctx.find_root().obj`; user-facing commands should respect it.
- Responses use the shared envelope from `response.py`; success/error payloads stay machine-readable.
- User-facing help, docstrings, and status text are predominantly Chinese; keep tone consistent.
- Environment resolution is layered: XDG config `.env` → legacy `~/.cliany-site/.env` → project `.env` → real environment.
- OpenAI-compatible base URLs are normalized to include `/v1`; do not duplicate normalization logic elsewhere.

## ANTI-PATTERNS (THIS PROJECT)
- Do not edit generated adapter code marked `# 自动生成 — DO NOT EDIT`.
- Do not assume generated adapters or session files live in this repo; runtime state lives under `~/.cliany-site/`.
- Do not fabricate navigation URLs during exploration; prompt contract explicitly forbids guessed URLs.
- Do not add pytest/CI assumptions to contributor docs; current validation path is shell scripts in `qa/`.
- Do not commit cache/build artifacts; repo already treats generated and transient files as out-of-scope.

## UNIQUE STYLES
- Built-in CLI plus runtime-loaded per-domain subcommands.
- AXTree-driven selector metadata enables fuzzy action replay after minor page changes.
- `doctor` reports environment health as structured JSON rather than plain logs.
- Generated adapters mirror root CLI conventions: root-aware `--json`, shared error codes, CDP/session preflight.

## COMMANDS
```bash
pip install -e .
cliany-site --version
cliany-site doctor --json
cliany-site login "https://github.com" --json
cliany-site explore "https://github.com" "搜索 cliany.site 仓库并查看 README" --json
cliany-site list --json
bash qa/run_all.sh
python -m cliany_site
```

## NOTES
- No in-repo CI workflows detected.
- QA scripts are integration checks, not isolated unit tests.
- `qa/test_commands.sh` creates a `test.com` adapter under `~/.cliany-site/adapters/` if absent.
- Runtime assumes a user-managed Chrome instance with `--remote-debugging-port=9222`.

## VERCEL 部署（重要）

**官网目录**: `site/` 目录包含静态网站文件

**正确部署步骤**:
```bash
cd site
# 确保链接到正确的 cliany.site 项目
vercel link --yes --project cliany.site
# 部署到生产环境
vercel --prod --yes
```

**关键点**: 必须使用 `--project cliany.site` 参数指定项目名称，否则会部署到错误的 `site` 项目。

**官网地址**: https://www.cliany.site
