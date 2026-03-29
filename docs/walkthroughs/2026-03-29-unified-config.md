# Phase 1.3 — 统一配置中心

**日期**: 2026-03-29  
**状态**: 已完成

## 概述

将项目中所有硬编码的配置值（端口号、超时、路径常量、魔法数字）收归到
`src/cliany_site/config.py` 统一管理，通过环境变量实现可配置化。

## 核心变更

### 新增文件

| 文件 | 说明 |
|------|------|
| `src/cliany_site/config.py` | `ClanySiteConfig` 冻结数据类 + `get_config()` 单例访问器 |

### 修改文件（按模块分组）

**action_runtime.py** — 7 个魔法数字替换为 getter 函数  
**browser/cdp.py** — `port=9222` → `port: int | None = None` + config，`timeout=2` → `get_config().cdp_timeout`  
**browser/launcher.py** — 3 个函数的 `port=9222` → config  
**explorer/engine.py** — `MAX_STEPS=10` 删除 → `cfg.explore_max_steps`，`port=9222` → config  
**loader.py** — `ADAPTERS_DIR` 模块常量 → `get_config().adapters_dir`  
**session.py** — `SESSIONS_DIR` 模块常量 → `get_config().sessions_dir`  
**cli.py** — `_ensure_dirs()` 使用 `cfg.adapters_dir` / `cfg.sessions_dir`  
**commands/doctor.py** — 路径从 config 读取 + 输出 `checks["config"]`  
**commands/explore.py** — `adapter_dir` 从 config 读取  
**commands/report.py** — `REPORTS_DIR` 从 config 读取  
**codegen/generator.py** — `save_adapter()` 内路径从 config 读取  
**codegen/merger.py** — `AdapterMerger.__init__` 路径从 config 读取  
**activity_log.py** — `LOG_FILE` → `get_config().activity_log_path`  
**report.py** — `REPORTS_DIR` → `get_config().reports_dir`  
**atoms/storage.py** — `ADAPTERS_DIR` → `get_config().adapters_dir`  
**tui/screens/adapter_list.py** — 所有 `ADAPTERS_DIR` → config

## 配置项与环境变量映射

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| `cdp_port` | `CLIANY_CDP_PORT` | `9222` | Chrome CDP 端口 |
| `cdp_timeout` | `CLIANY_CDP_TIMEOUT` | `2.0` | CDP 连接超时（秒） |
| `post_navigate_delay` | `CLIANY_POST_NAVIGATE_DELAY` | `1.5` | 导航后等待延迟 |
| `post_click_nav_delay` | `CLIANY_POST_CLICK_NAV_DELAY` | `2.0` | 点击导航后延迟 |
| `new_tab_settle_delay` | `CLIANY_NEW_TAB_SETTLE_DELAY` | `2.5` | 新标签页稳定延迟 |
| `resolve_retry_delay` | `CLIANY_RESOLVE_RETRY_DELAY` | `1.0` | 元素解析重试延迟 |
| `resolve_max_retries` | `CLIANY_RESOLVE_MAX_RETRIES` | `2` | 元素解析最大重试次数 |
| `adaptive_repair_enabled` | `CLIANY_ADAPTIVE_REPAIR` | `False` | 启用自适应修复 |
| `adaptive_repair_max_attempts` | `CLIANY_ADAPTIVE_REPAIR_MAX_ATTEMPTS` | `3` | 自适应修复最大尝试次数 |
| `explore_max_steps` | `CLIANY_EXPLORE_MAX_STEPS` | `10` | 探索最大步数 |
| `home_dir` | — | `~/.cliany-site` | 运行时主目录 |

**派生属性**（只读，基于 `home_dir`）：

- `adapters_dir` → `{home_dir}/adapters`
- `sessions_dir` → `{home_dir}/sessions`
- `reports_dir` → `{home_dir}/reports`
- `activity_log_path` → `{home_dir}/activity.log`

## 设计决策

1. **冻结数据类** — `ClanySiteConfig` 使用 `frozen=True`，运行时不可变，避免状态泄漏
2. **单例 + reset** — `get_config()` 延迟初始化单例，`reset_config()` 用于测试
3. **`port: int | None = None` 签名** — 保持 API 向后兼容，调用方仍可显式传入 port，不传则读 config
4. **不动错误消息中的 9222** — 错误提示里的 `--remote-debugging-port=9222` 是引导用户的固定 Chrome 标志，不需要动态化

## 验证结果

- 全部 `.py` 文件 AST 语法检查通过
- `cliany-site --help` 正常输出
- `get_config()` 默认值正确
- 环境变量覆盖（`CLIANY_CDP_PORT=9333`）生效
- `reset_config()` 正确重置单例

## 消除的反模式

- ❌ 15 个文件中 `Path.home() / ".cliany-site"` 硬编码 → ✅ 仅 `config.py` 一处定义
- ❌ 模块级常量 `ADAPTERS_DIR` / `SESSIONS_DIR` / `REPORTS_DIR` / `LOG_FILE` → ✅ `get_config()` 属性
- ❌ `port=9222` 在 6 个函数签名中重复 → ✅ 从 config 读取默认值
- ❌ `MAX_STEPS = 10` 模块常量 → ✅ `cfg.explore_max_steps`
- ❌ `timeout=2` 内联常量 → ✅ `get_config().cdp_timeout`
