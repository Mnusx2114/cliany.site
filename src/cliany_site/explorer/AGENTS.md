# EXPLORER GUIDE

## OVERVIEW
`explorer/` converts AXTree snapshots + workflow text into `ExploreResult` objects that drive code generation.

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Env loading / provider selection | `engine.py` | supports Anthropic + OpenAI; normalizes OpenAI base URL |
| Exploration loop | `engine.py` | `WorkflowExplorer.explore()` iterates until done / max steps |
| Prompt contract | `prompts.py` | JSON-only reply schema; strict URL/value rules |
| Data model changes | `models.py` | `PageInfo`, `ActionStep`, `CommandSuggestion`, `ExploreResult` |

## CONVENTIONS
- Exploration output is structured JSON with `actions`, `next_url`, `commands`, `done`, `reasoning`.
- `ActionStep` carries both AXTree refs and descriptive metadata (`target_name`, `target_role`, `target_attributes`) for fuzzy replay.
- `MAX_STEPS` in `engine.py` bounds exploration; keep termination behavior explicit.
- `_sanitize_actions_data()` is part of the contract: normalize URLs, preserve actionable metadata, reject empty/invalid navigation.
- Prompt language is Chinese and examples are concrete; keep edits operational, not abstract.

## ANTI-PATTERNS
- Do not fabricate `next_url` or `actions[].url`; only emit real absolute URLs or approved relative forms.
- Do not emit `type` actions with empty `value` when the workflow requires actual input text.
- Do not mark `done=true` for an intermediate step; completion means the whole workflow goal is satisfied.
- Do not strip target metadata from actions unless replay logic is updated in lockstep.

## NOTES
- `engine.py` is the package hotspot: LLM setup, dotenv precedence, parsing, sanitization, and action/command extraction all meet there.
- If you change the prompt schema, update downstream parsing and code generation assumptions together.
