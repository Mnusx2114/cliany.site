---
name: cliany-site
description: 通过 Chrome CDP 探索网页工作流并生成可调用 CLI 命令的智能 harness 工具
version: 0.1.0
---

# cliany-site Skill

## 概述

`cliany-site` 将任意网页工作流自动化为可执行的 CLI 命令。它通过 Chrome CDP 协议捕获页面结构，借助 LLM 生成对应的 Click 命令，并以标准 JSON 格式输出结果。

## 前置条件

- Python 3.9+，已安装 `cliany-site`（`pip install -e .`）
- Chrome 以 `--remote-debugging-port=9222` 启动
- `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY` 环境变量已设置

## 使用方法

### doctor — 环境检查

```bash
cliany-site doctor [--json]
```

检查所有前置条件：CDP 连接、LLM Key、`~/.cliany-site/` 目录结构。

**输出字段：**
- `cdp` (bool)：Chrome CDP 是否可用
- `llm` (bool)：LLM API Key 是否已配置
- `adapters_dir` (str)：adapter 存储路径

### login — 网站登录

```bash
cliany-site login <url> [--json]
```

打开指定 URL，等待用户手动完成登录，自动保存 Session 至 `~/.cliany-site/sessions/`。

### explore — 探索工作流

```bash
cliany-site explore <url> <workflow_description> [--json]
```

通过 CDP 捕获页面 AXTree，调用 LLM 分析工作流，生成 adapter 命令至 `~/.cliany-site/adapters/<domain>/`。

**参数：**
- `url`：目标网页 URL
- `workflow_description`：工作流描述（自然语言）

### list — 列出 adapter

```bash
cliany-site list [--json]
```

列出所有已生成的 adapter 域名。

### `<domain> <command>` — 执行 adapter 命令

```bash
cliany-site <domain> <command> [args...] [--json]
```

执行指定域名 adapter 中的命令。

## 示例

### 示例 1：检查环境是否就绪

```bash
cliany-site doctor --json
# 成功时输出:
# {"success": true, "data": {"cdp": true, "llm": true, ...}, "error": null}
```

### 示例 2：探索 GitHub 搜索工作流

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
cliany-site login "https://github.com" --json
cliany-site explore "https://github.com" "搜索仓库并查看 README" --json
```

explore 成功后，`github.com` adapter 自动注册，可直接调用：

```bash
cliany-site github.com search --query "browser-use" --json
```

### 示例 3：批量自动化（Shell 脚本）

```bash
#!/bin/bash
set -e

cliany-site doctor --json | python3 -c "
import sys, json
d = json.loads(sys.stdin.read())
if not d['success']:
    print('环境检查失败:', d['error']['message'])
    exit(1)
print('环境就绪')
"

cliany-site explore "https://example.com" "提交表单" --json
cliany-site example.com submit --name "test" --json
```

## 输出格式

所有命令均输出标准 JSON 信封：

```json
{
  "success": true | false,
  "data": { ... },
  "error": null | {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

**常见错误码：**

| 错误码 | 含义 |
|--------|------|
| `CDP_UNAVAILABLE` | Chrome 未启动或未开启 9222 端口 |
| `LLM_KEY_MISSING` | 未设置 LLM API Key |
| `COMMAND_NOT_FOUND` | 未知命令或 adapter 不存在 |
| `EXPLORE_FAILED` | 工作流探索失败 |

**退出码：**
- `0`：命令成功
- `1`：命令失败（错误详情见 JSON `error` 字段）

## QA 验证

使用内置 QA 脚本验证安装：

```bash
bash qa/doctor_check.sh
bash qa/run_all.sh
```
