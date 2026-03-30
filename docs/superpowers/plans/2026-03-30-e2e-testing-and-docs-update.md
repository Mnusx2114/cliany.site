# v0.5.0 端到端测试 + GitHub/官网更新 实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 v0.1.1→v0.5.0 的全部新增功能编写端到端测试，确认项目稳定可用后，更新 GitHub README（中/英）和 cliany.site 官网以反映最新能力。

**Architecture:** 分四个独立 Chunk 推进：(1) L3 CLI 集成测试覆盖所有命令的注册/帮助/参数校验/错误降级；(2) L3.5 模块间集成测试验证跨模块协作路径；(3) 重写 README.md/README.en.md 以反映 v0.5.0 完整能力集；(4) 更新官网 HTML + i18n JS 新增 6 张特性卡片和新命令演示。每个 Chunk 可独立交付并产出可测试的工件。

**Tech Stack:** Python 3.11, Click (CliRunner), pytest, pytest-asyncio, HTML/CSS/JS (静态站), Vercel

---

## 文件结构总览

### 新建文件

| 文件 | 职责 |
|------|------|
| `tests/test_cli_integration.py` | L3 CLI 集成测试：所有命令的 --help、参数校验、JSON 输出 |
| `tests/test_cross_module.py` | L3.5 模块间集成测试：SDK/安全/市场/工作流跨模块交互 |

### 修改文件

| 文件 | 修改范围 |
|------|---------|
| `README.md` | 全面重写：新增徽章行、扩展特性列表、补充新命令参考、新增 SDK/API/工作流/安全/市场示例章节 |
| `README.en.md` | 与 README.md 同步的英文全面重写 |
| `site/index.html` | 新增 6 张特性卡片、更新 features subtitle、新增 SDK 代码示例区、更新快速开始 |
| `site/script.js` | 新增 6 张特性卡片的 i18n 条目、更新 subtitle 文案 |

---

## Chunk 1: L3 CLI 集成测试

### Task 1: CLI 版本与根命令测试

**Files:**
- Create: `tests/test_cli_integration.py`

- [ ] **Step 1: 编写根命令和版本号测试**

```python
"""L3 CLI 集成测试 — 验证所有命令注册、帮助文本、参数校验、错误降级。

使用 Click CliRunner，无需 Chrome/LLM 等外部依赖。
"""

import json

from click.testing import CliRunner

from cliany_site.cli import cli


class TestRootCommand:
    """根命令基础功能"""

    def test_version_output(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.5.0" in result.output

    def test_help_output(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "cliany-site" in result.output

    def test_help_lists_all_builtin_commands(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        expected_commands = [
            "doctor", "login", "explore", "list", "tui",
            "check", "market", "workflow", "serve", "report",
        ]
        for cmd in expected_commands:
            assert cmd in result.output, f"命令 '{cmd}' 未在 --help 输出中找到"

    def test_no_subcommand_shows_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "Commands:" in result.output

    def test_unknown_command_exits_nonzero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["nonexistent-command-xyz"])
        assert result.exit_code != 0

    def test_global_options_parsed(self):
        """全局选项 --verbose/--debug/--sandbox 不应导致崩溃"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "--help"])
        assert result.exit_code == 0
        result = runner.invoke(cli, ["--debug", "--help"])
        assert result.exit_code == 0
        result = runner.invoke(cli, ["--sandbox", "--help"])
        assert result.exit_code == 0
```

- [ ] **Step 2: 运行测试确认通过**

Run: `uv run pytest tests/test_cli_integration.py::TestRootCommand -v`
Expected: 6 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli_integration.py
git commit -m "test: L3 CLI 集成测试 — 根命令、版本号、全局选项"
```

### Task 2: 各内置命令 --help 测试

**Files:**
- Modify: `tests/test_cli_integration.py`

- [ ] **Step 4: 编写所有内置命令的 --help 测试**

```python
class TestBuiltinCommandHelp:
    """每个内置命令的 --help 应正常返回"""

    def _run_help(self, args: list[str]):
        runner = CliRunner()
        result = runner.invoke(cli, args + ["--help"])
        assert result.exit_code == 0, f"'{' '.join(args)} --help' 退出码 {result.exit_code}: {result.output}"
        return result

    def test_doctor_help(self):
        result = self._run_help(["doctor"])
        assert "检查运行环境" in result.output or "CDP" in result.output

    def test_login_help(self):
        result = self._run_help(["login"])
        assert "Session" in result.output or "URL" in result.output.upper()

    def test_explore_help(self):
        result = self._run_help(["explore"])
        assert "探索" in result.output or "workflow" in result.output.lower()

    def test_list_help(self):
        result = self._run_help(["list"])
        assert "adapter" in result.output.lower() or "适配器" in result.output

    def test_check_help(self):
        result = self._run_help(["check"])
        assert "健康" in result.output or "AXTree" in result.output

    def test_tui_help(self):
        result = self._run_help(["tui"])
        assert "管理" in result.output or "界面" in result.output or "TUI" in result.output.upper()

    def test_serve_help(self):
        result = self._run_help(["serve"])
        assert "HTTP" in result.output or "API" in result.output or "port" in result.output

    def test_market_help(self):
        result = self._run_help(["market"])
        assert "适配器" in result.output or "market" in result.output.lower()

    def test_market_subcommands(self):
        """market 应包含 publish/install/uninstall/info/rollback/backups 子命令"""
        runner = CliRunner()
        result = runner.invoke(cli, ["market", "--help"])
        assert result.exit_code == 0
        for subcmd in ["publish", "install", "uninstall", "info", "rollback", "backups"]:
            assert subcmd in result.output, f"market 缺少子命令 '{subcmd}'"

    def test_workflow_help(self):
        result = self._run_help(["workflow"])
        assert "工作流" in result.output or "workflow" in result.output.lower()

    def test_workflow_subcommands(self):
        """workflow 应包含 run/validate/batch 子命令"""
        runner = CliRunner()
        result = runner.invoke(cli, ["workflow", "--help"])
        assert result.exit_code == 0
        for subcmd in ["run", "validate", "batch"]:
            assert subcmd in result.output, f"workflow 缺少子命令 '{subcmd}'"

    def test_report_help(self):
        result = self._run_help(["report"])
        assert "报告" in result.output or "report" in result.output.lower()

    def test_report_subcommands(self):
        """report 应包含 list/show 子命令"""
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "--help"])
        assert result.exit_code == 0
        for subcmd in ["list", "show"]:
            assert subcmd in result.output, f"report 缺少子命令 '{subcmd}'"
```

- [ ] **Step 5: 运行测试确认通过**

Run: `uv run pytest tests/test_cli_integration.py::TestBuiltinCommandHelp -v`
Expected: 14 passed

- [ ] **Step 6: Commit**

```bash
git add tests/test_cli_integration.py
git commit -m "test: L3 CLI 集成测试 — 全部内置命令 --help 和子命令完整性"
```

### Task 3: 参数校验与错误降级测试

**Files:**
- Modify: `tests/test_cli_integration.py`

- [ ] **Step 7: 编写缺参和错误参数测试**

```python
class TestParameterValidation:
    """命令缺少必要参数时应优雅报错"""

    def test_explore_missing_args(self):
        """explore 缺少 URL 和 workflow 参数"""
        runner = CliRunner()
        result = runner.invoke(cli, ["explore"])
        assert result.exit_code != 0

    def test_login_missing_url(self):
        """login 缺少 URL 参数"""
        runner = CliRunner()
        result = runner.invoke(cli, ["login"])
        assert result.exit_code != 0

    def test_check_missing_domain(self):
        """check 缺少 domain 参数"""
        runner = CliRunner()
        result = runner.invoke(cli, ["check"])
        assert result.exit_code != 0

    def test_market_publish_missing_domain(self):
        """market publish 缺少 domain"""
        runner = CliRunner()
        result = runner.invoke(cli, ["market", "publish"])
        assert result.exit_code != 0

    def test_market_install_missing_path(self):
        """market install 缺少 pack_path"""
        runner = CliRunner()
        result = runner.invoke(cli, ["market", "install"])
        assert result.exit_code != 0

    def test_workflow_run_missing_file(self):
        """workflow run 缺少 YAML 文件"""
        runner = CliRunner()
        result = runner.invoke(cli, ["workflow", "run"])
        assert result.exit_code != 0

    def test_workflow_batch_missing_args(self):
        """workflow batch 缺少 adapter/command/data_file"""
        runner = CliRunner()
        result = runner.invoke(cli, ["workflow", "batch"])
        assert result.exit_code != 0

    def test_report_show_missing_id(self):
        """report show 缺少 report_id"""
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "show"])
        assert result.exit_code != 0
```

- [ ] **Step 8: 运行测试确认通过**

Run: `uv run pytest tests/test_cli_integration.py::TestParameterValidation -v`
Expected: 8 passed

- [ ] **Step 9: Commit**

```bash
git add tests/test_cli_integration.py
git commit -m "test: L3 CLI 集成测试 — 参数校验和错误降级"
```

### Task 4: JSON 输出格式测试

**Files:**
- Modify: `tests/test_cli_integration.py`

- [ ] **Step 10: 编写 JSON 输出格式验证测试**

```python
class TestJsonOutput:
    """--json 模式下的输出格式验证"""

    def test_list_json_output(self):
        """list --json 应返回有效 JSON 信封"""
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "success" in data
        assert "data" in data
        assert "error" in data
        assert data["success"] is True

    def test_report_list_json_output(self):
        """report list --json 应返回有效 JSON 信封"""
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True
        assert "reports" in data["data"]

    def test_json_error_envelope(self):
        """JSON 模式下错误输出应包含 error.code 和 error.message"""
        runner = CliRunner()
        # report show 传入不存在的 ID
        result = runner.invoke(cli, ["report", "show", "nonexistent-report-id-xyz", "--json"])
        # 即使报错，输出也应该是有效 JSON
        try:
            data = json.loads(result.output)
            if not data.get("success"):
                assert "code" in data["error"]
                assert "message" in data["error"]
        except json.JSONDecodeError:
            pass  # 某些错误可能不输出 JSON，这是可接受的

    def test_global_json_flag_propagates(self):
        """根级 --json 应传递到子命令"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] is True
```

- [ ] **Step 11: 运行测试确认通过**

Run: `uv run pytest tests/test_cli_integration.py::TestJsonOutput -v`
Expected: 4 passed

- [ ] **Step 12: 运行全部 L3 测试确认通过**

Run: `uv run pytest tests/test_cli_integration.py -v`
Expected: 32 passed

- [ ] **Step 13: Commit**

```bash
git add tests/test_cli_integration.py
git commit -m "test: L3 CLI 集成测试 — JSON 输出格式验证（32 用例完成）"
```

---

## Chunk 2: L3.5 模块间集成测试

### Task 5: SDK + 安全 + 市场 + 工作流跨模块测试

**Files:**
- Create: `tests/test_cross_module.py`

- [ ] **Step 14: 编写 SDK 同步接口测试**

```python
"""L3.5 模块间集成测试 — 验证跨模块协作路径。

不依赖 Chrome/LLM 外部服务，通过 Mock 或纯逻辑验证。
"""

import json
import tempfile
from pathlib import Path

import pytest


class TestSDKIntegration:
    """SDK 模块集成测试"""

    def test_sdk_class_instantiation(self):
        """ClanySite 类可正常实例化"""
        from cliany_site.sdk import ClanySite

        sdk = ClanySite()
        assert sdk is not None

    def test_sdk_sync_list_adapters(self):
        """同步 list_adapters 返回结构化结果"""
        from cliany_site.sdk import list_adapters

        result = list_adapters()
        assert isinstance(result, dict)
        assert "success" in result

    def test_sdk_sync_doctor(self):
        """同步 doctor 返回结构化结果"""
        from cliany_site.sdk import doctor

        result = doctor()
        assert isinstance(result, dict)
        assert "success" in result
```

- [ ] **Step 15: 编写安全模块集成测试**

```python
class TestSecurityIntegration:
    """安全模块跨组件集成测试"""

    def test_session_encrypt_decrypt_roundtrip(self):
        """加密 → 解密往返一致性"""
        from cliany_site.security import decrypt_data, encrypt_data

        original = {"cookies": [{"name": "token", "value": "abc123"}]}
        plaintext = json.dumps(original, ensure_ascii=False)
        encrypted = encrypt_data(plaintext)
        assert encrypted != plaintext.encode()

        decrypted_str = decrypt_data(encrypted)
        decrypted = json.loads(decrypted_str)
        assert decrypted == original

    def test_audit_detects_dangerous_patterns(self):
        """代码审计检测 eval/exec 等危险模式"""
        from cliany_site.audit import audit_source

        dangerous_code = '''
import os
result = eval(user_input)
os.system("rm -rf /")
'''
        findings = audit_source(dangerous_code)
        assert len(findings) > 0
        categories = [f.category for f in findings]
        assert any("dangerous_call" in c for c in categories)

    def test_audit_passes_clean_code(self):
        """安全代码应通过审计"""
        from cliany_site.audit import audit_source

        clean_code = '''
import click

@click.command()
def hello():
    click.echo("Hello World")
'''
        findings = audit_source(clean_code)
        assert len(findings) == 0

    def test_sandbox_blocks_cross_domain(self):
        """沙箱策略阻止跨域导航"""
        from cliany_site.sandbox import SandboxPolicy

        policy = SandboxPolicy.from_domain("github.com")
        assert policy.enabled is True
        assert "github.com" in policy.allowed_domains
```

- [ ] **Step 16: 编写市场模块集成测试**

```python
class TestMarketplaceIntegration:
    """适配器市场打包 → 安装往返测试"""

    def test_pack_and_install_roundtrip(self, tmp_path):
        """打包 → 安装 → 验证文件完整"""
        from cliany_site.marketplace import install_adapter, pack_adapter

        # 准备一个模拟 adapter
        adapter_dir = tmp_path / "adapters" / "test-roundtrip.com"
        adapter_dir.mkdir(parents=True)
        (adapter_dir / "commands.py").write_text(
            "import click\n\n@click.group()\ndef cli():\n    pass\n"
        )
        (adapter_dir / "metadata.json").write_text(
            json.dumps({"domain": "test-roundtrip.com", "commands": []})
        )

        # 打包
        import os
        os.environ["CLIANY_HOME"] = str(tmp_path)
        from cliany_site.config import reset_config
        reset_config()

        pack_path = pack_adapter("test-roundtrip.com", version="1.0.0")
        assert pack_path.exists()
        assert pack_path.suffix == ".gz"

        # 安装到另一个位置
        install_dir = tmp_path / "install_target"
        install_dir.mkdir(parents=True)
        manifest = install_adapter(str(pack_path), force=True)
        assert manifest.domain == "test-roundtrip.com"
        assert manifest.version == "1.0.0"
```

- [ ] **Step 17: 编写工作流模块集成测试**

```python
class TestWorkflowIntegration:
    """工作流解析 + 引擎集成测试"""

    def test_yaml_parse_valid_workflow(self, tmp_path):
        """有效 YAML → WorkflowDef 解析成功"""
        from cliany_site.workflow.parser import load_workflow_file

        yaml_content = """
name: 测试工作流
description: 集成测试用
steps:
  - name: 第一步
    adapter: example.com
    command: search
    params:
      query: test
  - name: 第二步
    adapter: example.com
    command: view
    params:
      id: "123"
"""
        yaml_file = tmp_path / "test_workflow.yaml"
        yaml_file.write_text(yaml_content)

        workflow = load_workflow_file(str(yaml_file))
        assert workflow.name == "测试工作流"
        assert len(workflow.steps) == 2
        assert workflow.steps[0].adapter == "example.com"
        assert workflow.steps[0].params == {"query": "test"}

    def test_yaml_parse_invalid_workflow(self, tmp_path):
        """缺少必填字段的 YAML 应抛出 WorkflowParseError"""
        from cliany_site.workflow.parser import WorkflowParseError, load_workflow_file

        yaml_content = """
steps:
  - adapter: example.com
"""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text(yaml_content)

        with pytest.raises(WorkflowParseError):
            load_workflow_file(str(yaml_file))

    def test_batch_data_csv_parse(self, tmp_path):
        """CSV 批量数据解析"""
        from cliany_site.workflow.batch import load_batch_data

        csv_content = "query,limit\ntest1,10\ntest2,20\n"
        csv_file = tmp_path / "batch.csv"
        csv_file.write_text(csv_content)

        data = load_batch_data(str(csv_file))
        assert len(data) == 2
        assert data[0]["query"] == "test1"
        assert data[1]["limit"] == "20"

    def test_batch_data_json_parse(self, tmp_path):
        """JSON 批量数据解析"""
        from cliany_site.workflow.batch import load_batch_data

        json_content = json.dumps([
            {"query": "test1", "limit": 10},
            {"query": "test2", "limit": 20},
        ])
        json_file = tmp_path / "batch.json"
        json_file.write_text(json_content)

        data = load_batch_data(str(json_file))
        assert len(data) == 2
```

- [ ] **Step 18: 编写 AXTree iframe 标注测试**

```python
class TestAxtreeIframeIntegration:
    """AXTree iframe/Shadow DOM 增强测试"""

    def test_serialize_axtree_handles_iframe_annotations(self):
        """serialize_axtree 能处理带 frameId 标注的节点"""
        from cliany_site.browser.axtree import serialize_axtree

        # 模拟带 iframe 标注的树
        mock_tree = {
            "role": {"value": "RootWebArea"},
            "name": {"value": "Test Page"},
            "children": [
                {
                    "role": {"value": "Iframe"},
                    "name": {"value": "embedded"},
                    "frameId": "frame-123",
                    "children": [],
                }
            ],
        }
        result = serialize_axtree(mock_tree)
        assert isinstance(result, str)
        assert len(result) > 0
```

- [ ] **Step 19: 运行全部 L3.5 测试**

Run: `uv run pytest tests/test_cross_module.py -v`
Expected: ~15 passed

- [ ] **Step 20: 运行完整测试套件确认无回归**

Run: `uv run pytest tests/ -v --tb=short -q`
Expected: 583 + ~47 = ~630 passed, 0 failed

- [ ] **Step 21: Commit**

```bash
git add tests/test_cross_module.py
git commit -m "test: L3.5 模块间集成测试 — SDK/安全/市场/工作流/AXTree 跨模块验证"
```

---

## Chunk 3: GitHub README 更新

### Task 6: 重写 README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 22: 重写 README.md**

完整替换 README.md 内容，新结构如下：

```markdown
# cliany-site

[![PyPI version](https://img.shields.io/pypi/v/cliany-site)](https://pypi.org/project/cliany-site/)
[![Python](https://img.shields.io/pypi/pyversions/cliany-site)](https://pypi.org/project/cliany-site/)
[![CI](https://github.com/pearjelly/cliany.site/actions/workflows/ci.yml/badge.svg)](https://github.com/pearjelly/cliany.site/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/pearjelly/cliany.site)](LICENSE)

> 将任意网页操作自动化为可调用的 CLI 命令

cliany-site 基于 browser-use 和大语言模型（LLM），通过 Chrome CDP 协议实现从网页探索到代码生成、回放的全流程自动化。一条命令探索、一条命令执行，把复杂的网页工作流变成可重复调用的 CLI 工具。

## 特性

### 核心能力

- **零侵入探索** — Chrome CDP 捕获页面 AXTree，无需注入脚本
- **LLM 驱动代码生成** — Claude / GPT-4o 理解页面语义，自动生成 Python CLI 命令
- **标准 JSON 输出** — 所有命令支持 `--json`，输出统一 `{success, data, error}` 信封
- **持久化 Session** — 跨命令保持 Cookie / LocalStorage 登录状态
- **动态适配器加载** — 按域名自动注册 CLI 子命令，随时扩展
- **Chrome 自动管理** — 自动检测并启动 Chrome 调试实例

### 开发体验

- **适配器增量合并** — 重复 explore 同一网站时智能合并，保留已有命令
- **原子命令系统** — 自动提取可复用的原子操作，跨适配器共享
- **实时进度反馈** — explore/execute 过程中展示 Rich 进度条和 NDJSON 流式事件
- **智能自愈** — AXTree 快照对比，selector 热修复，无需重新 explore
- **断点续执行** — 失败后记录断点，`--resume` 从断点恢复

### 企业级特性

- **Headless & 远程浏览器** — 支持 `--headless` 和 `--cdp-url ws://host:port`，可在服务器/Docker 中运行
- **YAML 工作流编排** — 声明式多步骤工作流，步骤间数据传递 + 条件判断 + 重试策略
- **数据驱动批量执行** — CSV/JSON 批量参数，并发控制，汇总报告
- **Session 加密存储** — Fernet 对称加密 + 系统 Keychain 密钥管理
- **沙箱执行模式** — `--sandbox` 限制跨域导航和危险操作
- **生成代码安全审计** — AST 静态分析检测 eval/exec/os.system 等危险模式

### 生态集成

- **Python SDK** — `from cliany_site import explore, execute`，程序化调用
- **HTTP API** — `cliany-site serve --port 8080` 启动 REST API 服务
- **适配器市场** — 打包、安装、卸载、回滚适配器，团队共享自动化能力
- **TUI 管理界面** — 基于 Textual 的终端 UI，可视化管理适配器
- **iframe/Shadow DOM** — 递归 AXTree 采集，跨域 iframe 和 Shadow DOM 穿透

## 快速开始

### 安装

```bash
# PyPI 安装
pip install cliany-site

# 或源码安装
git clone https://github.com/pearjelly/cliany.site.git
cd cliany.site
pip install -e .
```

### 配置

```bash
# LLM Provider（二选一）
export CLIANY_LLM_PROVIDER=anthropic
export CLIANY_ANTHROPIC_API_KEY="sk-ant-..."

# 或 OpenAI
export CLIANY_LLM_PROVIDER=openai
export CLIANY_OPENAI_API_KEY="sk-..."
```

也支持 `.env` 文件配置，查找顺序：`~/.config/cliany-site/.env` → `~/.cliany-site/.env` → 项目目录 `.env` → 环境变量。

### 验证环境

```bash
cliany-site doctor --json
```

## 使用示例

### 基础流程

```bash
# 1. 探索工作流
cliany-site explore "https://github.com" "搜索仓库并查看 README" --json

# 2. 查看已生成命令
cliany-site list --json

# 3. 执行生成的命令
cliany-site github.com search --query "browser-use" --json
```

### Python SDK

```python
from cliany_site.sdk import ClanySite

async with ClanySite() as cs:
    result = await cs.explore("https://github.com", "搜索仓库")
    adapters = await cs.list_adapters()
```

### HTTP API

```bash
# 启动服务
cliany-site serve --port 8080

# 调用 API
curl http://localhost:8080/doctor
curl http://localhost:8080/adapters
curl -X POST http://localhost:8080/explore \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com", "workflow": "搜索仓库"}'
```

### YAML 工作流编排

```yaml
# workflow.yaml
name: GitHub 搜索流程
steps:
  - name: 搜索仓库
    adapter: github.com
    command: search
    params:
      query: "cliany-site"
  - name: 查看详情
    adapter: github.com
    command: view
    params:
      repo: "$prev.data.results[0].name"
```

```bash
cliany-site workflow run workflow.yaml --json
cliany-site workflow validate workflow.yaml --json
```

### 批量执行

```bash
# 从 CSV 批量执行
cliany-site workflow batch github.com search data.csv --concurrency 3 --json
```

### 适配器市场

```bash
# 打包适配器
cliany-site market publish github.com --version 1.0.0

# 安装适配器
cliany-site market install ./github.com.cliany-adapter.tar.gz

# 回滚
cliany-site market rollback github.com
```

## 命令参考

| 命令 | 参数 | 说明 |
|------|------|------|
| `doctor` | `[--json]` | 检查环境（CDP、LLM Key、目录结构） |
| `login <url>` | `[--json]` | 打开 URL 等待登录，保存 Session |
| `explore <url> <workflow>` | `[--json]` | 探索工作流，生成 adapter |
| `list` | `[--json]` | 列出已生成的 adapter |
| `check <domain>` | `[--json] [--fix]` | 检查适配器健康状态 |
| `tui` | | 启动 TUI 管理界面 |
| `serve` | `[--host] [--port]` | 启动 HTTP API 服务 |
| `market publish <domain>` | `[--version] [--json]` | 打包导出适配器 |
| `market install <path>` | `[--force] [--json]` | 安装适配器包 |
| `market uninstall <domain>` | `[--json]` | 卸载适配器 |
| `market rollback <domain>` | `[--index] [--json]` | 回滚到备份版本 |
| `workflow run <file>` | `[--json] [--dry-run]` | 执行 YAML 工作流 |
| `workflow validate <file>` | `[--json]` | 验证工作流文件 |
| `workflow batch <adapter> <cmd> <data>` | `[--concurrency] [--json]` | 批量执行 |
| `report list` | `[--domain] [--json]` | 列出执行报告 |
| `report show <id>` | `[--json]` | 查看报告详情 |
| `<domain> <command>` | `[--json] [args...]` | 执行适配器中的命令 |

**全局选项：** `--json` `--verbose` `--debug` `--cdp-url <ws://host:port>` `--headless` `--sandbox`

## 架构概览

```
cliany-site/src/cliany_site/
├── cli.py              # 主入口，SafeGroup 全局异常捕获
├── config.py           # 统一配置中心（环境变量 + .env）
├── errors.py           # 异常层级体系 + 错误码
├── response.py         # JSON 信封 {success, data, error}
├── logging_config.py   # 结构化日志（JSON format + 脱敏）
├── sdk.py              # Python SDK（同步 + 异步）
├── server.py           # HTTP API 服务（aiohttp）
├── security.py         # Session 加密（Fernet + Keychain）
├── sandbox.py          # 沙箱策略执行
├── audit.py            # 代码安全审计（AST 分析）
├── marketplace.py      # 适配器市场（打包/安装/回滚）
├── browser/            # CDP 连接 + AXTree + Chrome 启动 + iframe
├── explorer/           # LLM 工作流探索 + 原子提取 + 验证
├── codegen/            # 代码生成（模板/参数推导/去重/合并）
├── workflow/           # YAML 编排 + 批量执行
├── commands/           # 内置 CLI 命令
└── tui/                # Textual 终端 UI
```

## 安全特性

- **Session 加密**：Fernet 对称加密，密钥存入系统 Keychain（macOS Keychain / Linux Secret Service），无 Keychain 时降级为文件密钥
- **沙箱模式**：`--sandbox` 限制 navigate 同域、禁止 `javascript:` / `file://` / `data:` URL、禁止文件下载
- **代码审计**：codegen 输出自动 AST 扫描，检测 `eval` / `exec` / `os.system` / `subprocess` 等危险调用

## 贡献指南

```bash
# 开发环境
git clone https://github.com/pearjelly/cliany.site.git
cd cliany.site
pip install -e ".[dev,test]"

# 质量检查
ruff check src/           # lint
mypy src/cliany_site/     # type check
pytest tests/ -v          # 单元测试

# PR 流程
# 1. Fork → 2. 创建分支 → 3. 修改 → 4. 通过 lint/test → 5. 提交 PR
```

## 限制说明

- 需要 Chrome/Chromium（自动启动或手动 `--remote-debugging-port=9222`）
- 需要有效的 LLM API Key（Anthropic 或 OpenAI）
- 生成的命令依赖页面 DOM 结构，大幅页面改版后可能需要重新 explore（小幅变化由模糊匹配和自愈机制处理）
- Session 不跨浏览器 Profile 共享
- 跨域 iframe 默认启用递归采集（可通过 `CLIANY_CROSS_ORIGIN_IFRAMES` 配置）
```

- [ ] **Step 23: 运行 lint 确认 README 无语法问题**

验证 README.md 中的代码块语法正确。

- [ ] **Step 24: Commit**

```bash
git add README.md
git commit -m "docs: 全面重写 README.md — 反映 v0.5.0 完整能力集（特性/命令/SDK/API/安全/工作流）"
```

### Task 7: 重写 README.en.md

**Files:**
- Modify: `README.en.md`

- [ ] **Step 25: 重写 README.en.md**

与 README.md 结构完全一致的英文版本。关键翻译要点：
- 标题/简介对应翻译
- 代码示例保持一致（注释和工作流描述翻译为英文）
- 命令参考表「说明」列翻译
- 修正 v0.1.1 遗留的翻译问题（如 `CDP protocol's底层` → `CDP protocol's low-level`）

- [ ] **Step 26: Commit**

```bash
git add README.en.md
git commit -m "docs: 全面重写 README.en.md — 英文版同步 v0.5.0 完整能力集"
```

---

## Chunk 4: 官网更新

### Task 8: 新增特性卡片 HTML

**Files:**
- Modify: `site/index.html:87-156` (features section)

- [ ] **Step 27: 在 features-grid 末尾新增 6 张特性卡片**

在 `</div> <!-- .features-grid -->` 关闭标签之前，追加 6 个 `feature-card` div：

1. **Headless & 远程浏览器** (headless) — cloud/server 图标
2. **YAML 工作流编排** (workflow) — git-branch 图标
3. **数据驱动批量执行** (batch) — table/spreadsheet 图标
4. **Python SDK & HTTP API** (sdk) — code/globe 图标
5. **安全加固** (security) — shield 图标
6. **适配器市场** (marketplace) — package 图标

同时更新 features subtitle 从"十大核心能力"改为"十六大核心能力"。

- [ ] **Step 28: 更新快速开始区域**

在 Step 1 安装卡片中，`pip install -e .` 前面新增 `pip install cliany-site`（PyPI 安装）。

- [ ] **Step 29: 验证 HTML 语法正确**

用浏览器打开 `site/index.html` 确认新卡片正常渲染。

- [ ] **Step 30: Commit**

```bash
git add site/index.html
git commit -m "feat(site): 新增 6 张 v0.2-v0.5 特性卡片 + 更新快速开始"
```

### Task 9: 新增 i18n 翻译条目

**Files:**
- Modify: `site/script.js:1-141` (I18N object)

- [ ] **Step 31: 在 I18N 对象中新增 6 张卡片的翻译条目**

在 `features.tui.desc` 之后追加：

```javascript
  'features.headless.title': { zh: 'Headless & 远程浏览器', en: 'Headless & Remote Browser' },
  'features.headless.desc': {
    zh: '支持 Headless Chrome 和远程 CDP 连接，可在服务器和 Docker 容器中运行，突破本地 GUI 限制。',
    en: 'Support Headless Chrome and remote CDP connections. Run on servers and Docker containers, beyond local GUI limitations.'
  },
  'features.workflow.title': { zh: 'YAML 工作流编排', en: 'YAML Workflow Orchestration' },
  'features.workflow.desc': {
    zh: '通过 YAML 声明式编排多步骤工作流，支持步骤间数据传递、条件判断和重试策略。',
    en: 'Declaratively orchestrate multi-step workflows via YAML, with inter-step data passing, conditional logic, and retry policies.'
  },
  'features.batch.title': { zh: '数据驱动批量执行', en: 'Data-Driven Batch Execution' },
  'features.batch.desc': {
    zh: '从 CSV/JSON 读取参数列表批量执行，支持并发控制，自动生成汇总报告。',
    en: 'Batch execute from CSV/JSON parameter lists with concurrency control and automatic summary reports.'
  },
  'features.sdk.title': { zh: 'Python SDK & HTTP API', en: 'Python SDK & HTTP API' },
  'features.sdk.desc': {
    zh: '程序化调用 from cliany_site import explore，或启动 REST API 服务，集成到任意系统。',
    en: 'Programmatic calls via from cliany_site import explore, or launch a REST API server for integration into any system.'
  },
  'features.security.title': { zh: '安全加固', en: 'Security Hardening' },
  'features.security.desc': {
    zh: 'Session 加密存储、沙箱执行模式、生成代码自动 AST 安全审计，全方位安全保障。',
    en: 'Encrypted session storage, sandbox execution mode, and automatic AST security auditing of generated code.'
  },
  'features.marketplace.title': { zh: '适配器市场', en: 'Adapter Marketplace' },
  'features.marketplace.desc': {
    zh: '打包、发布、安装、回滚适配器，团队间共享自动化能力，版本化管理。',
    en: 'Package, publish, install, and rollback adapters. Share automation capabilities across teams with version management.'
  },
```

同时更新 subtitle：

```javascript
  'features.subtitle': { zh: '十六大核心能力，从探索到生态', en: 'Sixteen core capabilities, from exploration to ecosystem' },
```

- [ ] **Step 32: 验证双语切换正常**

用浏览器打开 `site/index.html`，切换中/英文验证新增卡片文案正确。

- [ ] **Step 33: Commit**

```bash
git add site/script.js
git commit -m "feat(site): 新增 6 张特性卡片 i18n 翻译（中/英）"
```

### Task 10: 最终验证与汇总提交

**Files:**
- All modified files

- [ ] **Step 34: 运行完整测试套件**

Run: `uv run pytest tests/ -v --tb=short -q`
Expected: ~630+ passed, 0 failed

- [ ] **Step 35: 运行 lint + type check**

Run: `uv run ruff check src/ && uv run mypy src/cliany_site/`
Expected: 0 error

- [ ] **Step 36: 验证 CLI 所有命令可用**

Run: `uv run cliany-site --version && uv run cliany-site --help`
Expected: version 0.5.0, 所有命令列出

- [ ] **Step 37: 验证官网本地预览**

用浏览器打开 `site/index.html`，检查：
- 16 张特性卡片正确显示
- 中英文切换正常
- terminal 动画正常
- 响应式布局正常

- [ ] **Step 38: 记录完成文档**

更新 `docs/brainstorm-e2e-testing-and-docs-update.md` 的完成状态。
