# PACKAGE GUIDE

## OVERVIEW
`src/cliany_site/` holds the runtime package: root CLI, built-in commands, browser/CDP integration, explorer, codegen, adapter loading, and session persistence.

## STRUCTURE
```text
src/cliany_site/
├── cli.py               # root Click group; global error rendering; adapter registration
├── commands/            # built-in user-facing commands
├── browser/             # CDP connection + AXTree capture
├── explorer/            # LLM planning loop and prompt/data contracts
├── codegen/             # generated adapter emitter
├── loader.py            # discovers and loads `~/.cliany-site/adapters/*/commands.py`
├── session.py           # cookies/session persistence in home dir
├── action_runtime.py    # replay engine for planned actions
└── response.py          # shared success/error envelope printing
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add/change root CLI behavior | `cli.py` | `SafeGroup`, root options, command registration |
| Add built-in command | `commands/` | follow existing Click + `asyncio.run` boundary |
| Change response envelope | `response.py`, `errors.py` | impacts all commands and generated adapters |
| Change adapter discovery/runtime mounting | `loader.py` | reads from home directory, not repo |
| Persist or inspect login state | `session.py` | safe-domain file naming |
| Change replay semantics | `action_runtime.py` | handles click/type/select/navigate/submit |

## CONVENTIONS
- Keep command entrypoints thin; push real work into helpers or async inner functions.
- Preserve root `json_mode` inheritance via `ctx.find_root().obj`.
- Use `Path.home() / ".cliany-site"` for runtime artifacts; do not introduce repo-local state.
- Prefer absolute imports from `cliany_site.*`.
- User-facing copy stays Chinese unless an existing file is clearly English-only.

## ANTI-PATTERNS
- Do not bypass `print_response` / shared error helpers for command output.
- Do not register generated adapters manually in source; `register_adapters()` owns that path.
- Do not hardcode runtime artifacts into the repo tree.
- Do not mix exploratory logic into command modules when a lower-level package already owns it.

## LOCAL CHILD GUIDES
- `explorer/AGENTS.md` — prompt contract, exploration loop, result models.
- `codegen/AGENTS.md` — generated adapter format and metadata rules.
