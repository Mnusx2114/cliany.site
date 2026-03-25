# cliany-site OpenAI provider `model_dump` 异常修复记录

## 背景

用户在执行以下命令时失败：

```bash
cliany-site explore https://github.com "搜索 browser-use 仓库"
```

报错：

```text
EXECUTION_FAILED: 探索失败: 'str' object has no attribute 'model_dump'
```

## 根因

当前环境使用 `CLIANY_LLM_PROVIDER=openai`，并配置了代理 base URL。

在 `langchain_openai.ChatOpenAI` 调用链中，代理返回了不符合 OpenAI SDK 预期的数据形态（字符串而非对象/字典），最终在 `response.model_dump()` 处触发 `AttributeError`。

该问题和 `CLIANY_OPENAI_BASE_URL` 配置格式相关（缺少或不规范的 `/v1` 路径时更容易触发兼容问题）。

## 修复内容

### 1) OpenAI base URL 规范化

文件：`src/cliany_site/explorer/engine.py`

- 新增 `_normalize_openai_base_url()`：
  - 校验 URL 必须是 `http(s)://host[:port][/v1]`
  - 若仅配置到 host（无 path），自动补齐 `/v1`

### 2) provider 白名单校验

文件：`src/cliany_site/explorer/engine.py`、`src/cliany_site/commands/explore.py`

- `CLIANY_LLM_PROVIDER` 仅允许 `anthropic` / `openai`
- 在 `explore` 命令入口提前拦截非法 provider

### 3) OpenAI 调用异常可读化

文件：`src/cliany_site/explorer/engine.py`

- 对 `model_dump` 相关 `AttributeError` 转换为清晰错误提示：
  - 指导将 `CLIANY_OPENAI_BASE_URL` 配置为含 `/v1` 的地址

### 4) doctor 增强配置检查

文件：`src/cliany_site/commands/doctor.py`

- 新增检查项：
  - `llm_provider`
  - `openai_base_url`（仅 provider=openai 时）

## 验证结果

### 静态验证

- `lsp_diagnostics`（修改文件）: 无 error
- `python3 -m compileall -q src/cliany_site/`: 通过

### 功能回归

1. `cliany-site doctor --json`：`success: true`，包含 `llm_provider=openai_base_url=ok`
2. `cliany-site explore https://github.com "搜索 browser-use 仓库" --json`：成功生成 adapter
3. `cliany-site github.com run-workflow --json`：执行成功
4. 交互式覆盖流程（输入 `y`）同样成功

## 建议配置

```env
CLIANY_LLM_PROVIDER=openai
CLIANY_OPENAI_API_KEY=<your_key>
CLIANY_OPENAI_BASE_URL=https://your-proxy-host/v1
CLIANY_OPENAI_MODEL=<model_id>
```
