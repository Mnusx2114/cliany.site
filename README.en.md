# cliany-site

Turn any web interaction into callable CLI commands. Built on browser-use and LLM, using the CDP protocol to automate the entire workflow from web exploration to code generation and playback.

cliany-site is an automation tool that bridges the gap between web interaction and command-line interfaces. Built on the browser-use library, it leverages Large Language Models' (LLM) deep understanding of web Accessibility Trees (AXTree) to transform complex web workflows into structured Python/Click CLI tools.

**Core Workflow:**
1. **Explore Phase:** The LLM analyzes the current page structure in real-time, autonomously plans paths, and generates executable automation scripts.
2. **Run Phase:** Quickly replay recorded workflows through generated CLI commands. The system uses fuzzy attribute matching to precisely locate elements and run stably even when the web UI undergoes minor changes.

By combining the CDP protocol's底层 control capabilities with the LLM's reasoning ability, cliany-site enables developers to manipulate complex web applications as easily as calling local scripts, dramatically improving browser automation development efficiency and maintainability.

## Features

- **Zero-intrusion Exploration:** Captures page AXTree via Chrome CDP protocol, automatically analyzes workflows
- **LLM-driven Code Generation:** Calls Claude / GPT-4o to transform exploration results into executable Click commands
- **Standard JSON Output:** All commands support `--json` flag, outputting unified `{success, data, error}` envelopes
- **Persistent Sessions:** Maintains Cookie / LocalStorage login state across commands
- **Dynamic Adapter Loading:** Each website generates an independent adapter, dynamically registered as subcommands by domain

## Quick Start

### Installation

```bash
cd cliany-site
pip install -e .
```

### Chrome CDP Configuration

Start Chrome with remote debugging port enabled:

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug

# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

Verify Chrome CDP is available:

```bash
curl http://localhost:9222/json
```

### LLM API Key Configuration

cliany-site supports both Anthropic and OpenAI LLM providers.

```bash
# Option 1: Use Anthropic (default)
export CLIANY_LLM_PROVIDER=anthropic
export CLIANY_ANTHROPIC_API_KEY="sk-ant-..."
export CLIANY_ANTHROPIC_MODEL="claude-3-5-haiku-20241022"  # optional, default is claude-3-5-haiku-20241022
export CLIANY_ANTHROPIC_BASE_URL="https://api.anthropic.com"  # optional, supports proxy

# Option 2: Use OpenAI
export CLIANY_LLM_PROVIDER=openai
export CLIANY_OPENAI_API_KEY="sk-..."
export CLIANY_OPENAI_MODEL="gpt-4o-mini"  # optional, default is gpt-4o-mini
export CLIANY_OPENAI_BASE_URL="https://api.openai.com/v1"  # optional, supports proxy (recommended to include /v1 explicitly)
```

**Backward Compatibility:** The legacy environment variable `ANTHROPIC_API_KEY` still works (but not recommended).

#### Using .env File Configuration

In addition to environment variables, cliany-site also supports configuration via `.env` files. Configuration file lookup order (priority from low to high):

1. `~/.config/cliany-site/.env` (XDG user config)
2. `~/.cliany-site/.env` (legacy compatible path)
3. Project directory `.env` (project-level config)
4. System environment variables (highest priority, will override same-name variables in .env files)

> For OpenAI-compatible interfaces, it is recommended to set `CLIANY_OPENAI_BASE_URL` to an address that includes `/v1` (e.g., `https://your-proxy/v1`). If only the host is provided (e.g., `https://your-proxy`), the program will automatically append `/v1`.

Example `.env` file:

```bash
# Project directory or ~/.cliany-site/.env
CLIANY_LLM_PROVIDER=anthropic
CLIANY_ANTHROPIC_API_KEY=sk-ant-...
CLIANY_OPENAI_API_KEY=sk-...
```

## Usage Examples

### 1. Check Environment

```bash
cliany-site doctor --json
```

Example output:
```json
{
  "success": true,
  "data": {
    "cdp": true,
    "llm": true,
    "adapters_dir": "/Users/you/.cliany-site/adapters"
  },
  "error": null
}
```

### 2. Login to Website

```bash
cliany-site login "https://github.com" --json
```

After the browser completes login, the session is automatically saved to `~/.cliany-site/sessions/`.

### 3. Explore Workflow

```bash
cliany-site explore "https://github.com" "Search for cliany.site repository and view README" --json
```

After exploration completes, the adapter is automatically generated to `~/.cliany-site/adapters/github.com/`.

### 4. List Generated Commands

```bash
cliany-site list --json
```

Example output:
```json
{
  "success": true,
  "data": {
    "adapters": ["github.com", "example.com"]
  },
  "error": null
}
```

### 5. Execute Generated Commands

```bash
cliany-site github.com search --query "browser-use" --json
```

## Command Reference

| Command | Parameters | Description |
|---------|-------------|-------------|
| `doctor` | `[--json]` | Check environment prerequisites (CDP, LLM Key, directory structure) |
| `login <url>` | `[--json]` | Open URL and wait for manual login, save Session |
| `explore <url> <workflow>` | `[--json]` | Explore URL workflow, generate adapter CLI commands |
| `list` | `[--json]` | List all generated adapters |
| `<domain> <command>` | `[--json] [args...]` | Execute command from specified domain adapter |

All commands support the `--json` flag, exit 1 on failure, exit 0 on success.

## Architecture Overview

```
cliany-site
├── cli.py          Main entry, SafeGroup catches global exceptions
├── response.py     JSON envelope {success, data, error}
├── errors.py       Error code definitions (CDP_UNAVAILABLE, etc.)
├── session.py      Cookie/LocalStorage persistence
├── loader.py       Adapter dynamic loading and registration
├── browser/
│   ├── cdp.py      CDP WebSocket connection
│   └── axtree.py   Accessibility tree capture
├── commands/       doctor / login / explore / list
├── explorer        WorkflowExplorer + data models
└── codegen         AdapterGenerator, LLM code generation
```

Generated adapters are stored in `~/.cliany-site/adapters/<domain>/`, containing:
- `commands.py`: Click command groups
- `metadata.json`: Generation metadata

## Limitations

- Requires a running Chrome instance with `--remote-debugging-port=9222` enabled
- Requires a valid `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- Generated commands depend on page DOM structure; re-exploration may be needed after page updates
- Sessions are not shared across browser profiles
- Currently does not support automatic operations on elements inside iframes