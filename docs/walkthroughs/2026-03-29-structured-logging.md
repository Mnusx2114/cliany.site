# Phase 1.2 结构化日志系统

**日期：** 2026-03-29
**状态：** 已完成
**关联计划：** [迭代计划 1.2](../iteration-plan-v02-v05.md)

## 变更概要

为 cliany-site 引入基于标准库 `logging` 的结构化日志系统，支持 CLI 级别控制和敏感信息自动脱敏。

## 新增文件

### `src/cliany_site/logging_config.py`

| 组件 | 说明 |
|------|------|
| `SensitiveFilter` | 日志过滤器，自动脱敏 API key / Bearer token / password / cookie / secret |
| `JSONFormatter` | 单行 JSON 输出，包含 ts / level / logger / msg 及 extra 字段 (duration_ms, action, domain) |
| `HumanFormatter` | 彩色终端输出，按级别着色，附加耗时标注 |
| `setup_logging()` | 配置入口：设置级别 + formatter + 脱敏过滤器，幂等（重复调用仅更新级别） |
| `log_duration()` | 装饰器，自动记录函数执行入口/完成/失败及耗时（支持 sync 和 async 函数） |
| `LEVEL_QUIET / LEVEL_VERBOSE / LEVEL_DEBUG` | 级别常量 |

## 修改文件

### `cli.py`
- 新增 `--verbose` (`-v`) 和 `--debug` 全局选项
- 在 `cli()` 回调中调用 `setup_logging()`，根据选项设定日志级别
- `--json` 模式下使用 JSON formatter

### `explorer/engine.py`
- 添加 `logger = logging.getLogger(__name__)`
- explore 入口记录 URL / workflow / LLM provider
- 每步记录 LLM 调用和动作数量 + 耗时
- 完成时记录总动作数 / 命令数 / 总耗时

### `action_runtime.py`
- 添加 `import time`
- execute 入口记录动作数量 / domain / command_name
- 每步记录动作类型 / 描述 / 耗时
- 完成时记录成功 / 失败 / 总计汇总

### `codegen/generator.py`
- 添加 `logger = logging.getLogger(__name__)`
- generate 入口记录 domain / 动作数 / 命令数
- 完成时记录命令块数量 + 耗时
- save_adapter 记录保存路径

### `loader.py`
- 用 `logger.warning` 替换 `warnings.warn`（不再依赖 `warnings` 模块）
- 添加 adapter 注册成功的 debug 日志

### `session.py`
- 添加 `logger = logging.getLogger(__name__)`
- save_session 记录 domain / cookie 数量 / 路径
- load_session 记录 session 不存在的情况

## 脱敏规则

| 模式 | 示例 | 脱敏结果 |
|------|------|----------|
| `sk-ant-*` | `sk-ant-abcdef123456` | `sk-ant-abcdef***` |
| `sk-*` | `sk-proj-abc123` | `sk-p***` |
| key/token/password/secret/cookie | `api_key=mysecretkey12345` | `api_key=mysecret***` |
| Bearer token | `Bearer eyJhbGci...` | `Bearer eyJhbG***` |

## 使用方式

```bash
cliany-site --verbose doctor      # INFO 级别
cliany-site --debug explore ...   # DEBUG 级别（含 LLM 调用详情）
cliany-site --json --debug list   # JSON 格式日志输出到 stderr
```

## 验证结果

- 所有 40 个 `.py` 文件通过 AST 语法检查
- LSP 诊断 0 个新增错误（14 个预存 textual 导入问题不变）
- `cliany-site --help` 正确显示 `--verbose` 和 `--debug` 选项
- 脱敏功能经验证可正确处理 sk-ant / sk- / password / Bearer token
- HumanFormatter 和 JSONFormatter 均正常工作
