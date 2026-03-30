# cliany-site

[![PyPI version](https://img.shields.io/pypi/v/cliany-site)](https://pypi.org/project/cliany-site/)
[![Python](https://img.shields.io/pypi/pyversions/cliany-site)](https://pypi.org/project/cliany-site/)
[![CI](https://github.com/pearjelly/cliany.site/actions/workflows/ci.yml/badge.svg)](https://github.com/pearjelly/cliany.site/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/pearjelly/cliany.site)](LICENSE)

> Turn any web interaction into callable CLI commands

cliany-site uses browser-use and Large Language Models (LLM) to automate the full workflow from web exploration to code generation and replay via Chrome CDP protocol. One command to explore, one command to execute — turning complex web workflows into reusable CLI tools.

## Features

### Core

- **Zero-intrusion Exploration** — Captures page AXTree via Chrome CDP, no script injection needed
- **LLM-driven Code Generation** — Claude / GPT-4o understands page semantics, auto-generates Python CLI commands
- **Standard JSON Output** — All commands support `--json`, outputting unified `{success, data, error}` envelopes
- **Persistent Sessions** — Maintains Cookie / LocalStorage login state across commands
- **Dynamic Adapter Loading** — Auto-registers CLI subcommands by domain, extensible at any time
- **Chrome Auto-management** — Automatically detects and launches Chrome debugging instances

### Developer Experience

- **Incremental Adapter Merging** — Re-exploring the same site intelligently merges adapters, preserving existing commands
- **Atomic Command System** — Auto-extracts reusable atomic operations, shareable across adapters
- **Real-time Progress Feedback** — Rich progress bars and NDJSON streaming events during explore/execute
- **Smart Self-healing** — AXTree snapshot diffing, selector hot-fixing without re-exploration
- **Checkpoint Resume** — Records breakpoints on failure, `--resume` from last checkpoint

### Enterprise Features

- **Headless & Remote Browser** — Supports `--headless` and `--cdp-url ws://host:port`, runs on servers/Docker
- **YAML Workflow Orchestration** — Declarative multi-step workflows with inter-step data passing, conditionals, and retry policies
- **Data-driven Batch Execution** — CSV/JSON parameter lists, concurrency control, summary reports
- **Encrypted Session Storage** — Fernet symmetric encryption + system Keychain key management
- **Sandbox Execution Mode** — `--sandbox` restricts cross-domain navigation and dangerous operations
- **Generated Code Security Audit** — AST static analysis detects eval/exec/os.system and other dangerous patterns

### Ecosystem Integration

- **Python SDK** — `from cliany_site import explore, execute`, programmatic access
- **HTTP API** — `cliany-site serve --port 8080` launches a REST API server
- **Adapter Marketplace** — Package, install, uninstall, and rollback adapters for team sharing
- **TUI Management** — Textual-based terminal UI for visual adapter management
- **iframe/Shadow DOM** — Recursive AXTree capture with cross-origin iframe and Shadow DOM piercing

## Quick Start

### Installation

```bash
# From PyPI
pip install cliany-site

# Or from source
git clone https://github.com/pearjelly/cliany.site.git
cd cliany.site
pip install -e .
```

### Configuration

```bash
# LLM Provider (choose one)
export CLIANY_LLM_PROVIDER=anthropic
export CLIANY_ANTHROPIC_API_KEY="sk-ant-..."

# Or OpenAI
export CLIANY_LLM_PROVIDER=openai
export CLIANY_OPENAI_API_KEY="sk-..."
```

Also supports `.env` file configuration. Lookup order: `~/.config/cliany-site/.env` → `~/.cliany-site/.env` → project `.env` → environment variables.

### Verify Environment

```bash
cliany-site doctor --json
```

## Usage Examples

### Basic Flow

```bash
# 1. Explore a workflow
cliany-site explore "https://github.com" "Search repositories and view README" --json

# 2. List generated commands
cliany-site list --json

# 3. Execute a generated command
cliany-site github.com search --query "browser-use" --json
```

### Python SDK

```python
from cliany_site.sdk import ClanySite

async with ClanySite() as cs:
    result = await cs.explore("https://github.com", "Search repositories")
    adapters = await cs.list_adapters()
```

### HTTP API

```bash
# Start server
cliany-site serve --port 8080

# Call API
curl http://localhost:8080/doctor
curl http://localhost:8080/adapters
curl -X POST http://localhost:8080/explore \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com", "workflow": "Search repositories"}'
```

### YAML Workflow Orchestration

```yaml
# workflow.yaml
name: GitHub Search Flow
steps:
  - name: Search repositories
    adapter: github.com
    command: search
    params:
      query: "cliany-site"
  - name: View details
    adapter: github.com
    command: view
    params:
      repo: "$prev.data.results[0].name"
```

```bash
cliany-site workflow run workflow.yaml --json
cliany-site workflow validate workflow.yaml --json
```

### Batch Execution

```bash
# Batch execute from CSV
cliany-site workflow batch github.com search data.csv --concurrency 3 --json
```

### Adapter Marketplace

```bash
# Package adapter
cliany-site market publish github.com --version 1.0.0

# Install adapter
cliany-site market install ./github.com.cliany-adapter.tar.gz

# Rollback
cliany-site market rollback github.com
```

## Command Reference

| Command | Parameters | Description |
|---------|------------|-------------|
| `doctor` | `[--json]` | Check environment (CDP, LLM Key, directories) |
| `login <url>` | `[--json]` | Open URL for login, save session |
| `explore <url> <workflow>` | `[--json]` | Explore workflow, generate adapter |
| `list` | `[--json]` | List generated adapters |
| `check <domain>` | `[--json] [--fix]` | Check adapter health |
| `tui` | | Launch TUI management interface |
| `serve` | `[--host] [--port]` | Start HTTP API server |
| `market publish <domain>` | `[--version] [--json]` | Package and export adapter |
| `market install <path>` | `[--force] [--json]` | Install adapter package |
| `market uninstall <domain>` | `[--json]` | Uninstall adapter |
| `market rollback <domain>` | `[--index] [--json]` | Rollback to backup version |
| `workflow run <file>` | `[--json] [--dry-run]` | Execute YAML workflow |
| `workflow validate <file>` | `[--json]` | Validate workflow file |
| `workflow batch <adapter> <cmd> <data>` | `[--concurrency] [--json]` | Batch execution |
| `report list` | `[--domain] [--json]` | List execution reports |
| `report show <id>` | `[--json]` | View report details |
| `<domain> <command>` | `[--json] [args...]` | Execute adapter command |

**Global options:** `--json` `--verbose` `--debug` `--cdp-url <ws://host:port>` `--headless` `--sandbox`

## Architecture

```
cliany-site/src/cliany_site/
├── cli.py              # Entry point, SafeGroup global exception handling
├── config.py           # Unified config (env vars + .env)
├── errors.py           # Exception hierarchy + error codes
├── response.py         # JSON envelope {success, data, error}
├── logging_config.py   # Structured logging (JSON format + sanitization)
├── sdk.py              # Python SDK (sync + async)
├── server.py           # HTTP API server (aiohttp)
├── security.py         # Session encryption (Fernet + Keychain)
├── sandbox.py          # Sandbox policy enforcement
├── audit.py            # Code security audit (AST analysis)
├── marketplace.py      # Adapter marketplace (pack/install/rollback)
├── browser/            # CDP connection + AXTree + Chrome launcher + iframe
├── explorer/           # LLM workflow exploration + atom extraction + validation
├── codegen/            # Code generation (templates/param inference/dedup/merge)
├── workflow/           # YAML orchestration + batch execution
├── commands/           # Built-in CLI commands
└── tui/                # Textual terminal UI
```

## Security

- **Session Encryption**: Fernet symmetric encryption with keys stored in system Keychain (macOS Keychain / Linux Secret Service), falling back to file-based keys
- **Sandbox Mode**: `--sandbox` restricts navigation to same domain, blocks `javascript:` / `file://` / `data:` URLs and file downloads
- **Code Audit**: Generated code is automatically AST-scanned for `eval` / `exec` / `os.system` / `subprocess` and other dangerous calls

## Contributing

```bash
# Development setup
git clone https://github.com/pearjelly/cliany.site.git
cd cliany.site
pip install -e ".[dev,test]"

# Quality checks
ruff check src/
mypy src/cliany_site/
pytest tests/ -v
```

## Limitations

- Requires Chrome/Chromium (auto-launched or manual `--remote-debugging-port=9222`)
- Requires a valid LLM API Key (Anthropic or OpenAI)
- Generated commands depend on page DOM structure; major page redesigns may require re-exploration (minor changes are handled by fuzzy matching and self-healing)
- Sessions are not shared across browser profiles
- Cross-origin iframes enabled by default for recursive capture (configurable via `CLIANY_CROSS_ORIGIN_IFRAMES`)