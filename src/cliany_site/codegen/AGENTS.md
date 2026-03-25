# CODEGEN GUIDE

## OVERVIEW
`codegen/` turns `ExploreResult` into executable Click adapter modules plus sidecar metadata in the user's home directory.

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Main generator | `generator.py` | `AdapterGenerator.generate()` builds the full module string |
| Command rendering | `generator.py` | `_render_command_block()`, `_render_argument_decorators()` |
| Metadata persistence | `generator.py` | `save_adapter()` writes `commands.py` + `metadata.json` |
| Naming / sanitization | `generator.py` | `_to_command_name()`, `_to_function_name()`, text sanitizers |

## CONVENTIONS
- Generated modules always start with `# 自动生成 — DO NOT EDIT` and embed source URL / workflow headers.
- Every generated command mirrors root CLI behavior: `--json`, `click.pass_context`, shared response helpers, `asyncio.run(...)` wrapper.
- Generated code depends on runtime modules in `cliany_site.*`; keep imports stable when refactoring core APIs.
- `save_adapter()` stores artifacts under `~/.cliany-site/adapters/<domain>/` and derives metadata from code headers/decorators.
- Command and parameter names are normalized into Click-safe identifiers; preserve this sanitization path.

## ANTI-PATTERNS
- Do not hand-edit generated adapters; fix the generator or regenerate.
- Do not change header/decorator formats casually; metadata extraction depends on them.
- Do not introduce repo-local output paths for adapters.
- Do not drop JSON-mode propagation from generated commands.

## NOTES
- `generator.py` is large because it owns both module templating and metadata extraction; keep helper additions close to the rendering code they support.
