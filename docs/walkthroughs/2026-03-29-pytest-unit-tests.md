# Phase 1.4 — pytest 单元测试体系

**日期**: 2026-03-29
**范围**: Phase 1.4 (v0.2.0 迭代计划)
**状态**: 已完成

## 目标

为项目建立 pytest 单元测试基础设施，覆盖核心纯函数，确保重构安全网。

## 变更清单

### 基础设施

| 文件 | 变更 |
|------|------|
| `pyproject.toml` | 新增 `[project.optional-dependencies.test]`（pytest>=8.0, pytest-asyncio>=0.23）和 `[tool.pytest.ini_options]`（asyncio_mode=auto） |
| `tests/conftest.py` | `_reset_config_singleton` autouse fixture、`clean_env`、`tmp_adapters_dir`、`mock_cdp`、`sample_metadata`、`sample_adapter_dir` |

### 测试文件

| 文件 | 测试数 | 覆盖模块 |
|------|--------|----------|
| `tests/test_config.py` | 20 | `config.py` — 环境变量解析器、ClanySiteConfig 数据类、get_config 单例 |
| `tests/test_axtree.py` | 13 | `browser/axtree.py` — serialize_axtree、extract_interactive_elements、axtree_to_markdown |
| `tests/test_action_runtime.py` | 53 | `action_runtime.py` — _normalize_text、_parse_ref_to_index、normalize_navigation_url、substitute_parameters、_score_candidate、_action_has_href、_action_opens_new_tab、_extract_repair_selector_refs |
| `tests/test_codegen.py` | 61 | `codegen/generator.py` — _to_command_name、_to_function_name、_to_parameter_name、_unique_parameter_name、_sanitize_inline_text、_sanitize_docstring_text、_safe_domain、_extract_header_value、_extract_commands_from_code、_render_click_type、_action_detail、_render_args_payload |
| `tests/test_engine.py` | 60 | `explorer/engine.py` — _to_snake_case、_infer_name_from_description、_infer_command_name_from_description、_normalize_openai_base_url、_parse_llm_response、_to_text、_sanitize_actions_data |
| `tests/test_smoke.py` | 1 | 包导入冒烟测试 |
| **合计** | **208** | |

## 测试策略

- **只测纯函数**：本阶段聚焦无副作用的纯逻辑函数，不涉及 CDP 连接、LLM 调用、文件系统写入等 I/O 操作。
- **边界覆盖**：每个函数包含正常输入、空值、None、非法类型等边界用例。
- **Config 隔离**：通过 autouse fixture 在每个测试前后重置 config 单例，避免测试间环境污染。
- **安装方式**：`uv pip install -e ".[test]"` 安装测试依赖，`uv run pytest` 执行。

## 运行方式

```bash
uv run pytest tests/ -v
```

## 修复记录

| 问题 | 修复 |
|------|------|
| `test_axtree.py::test_missing_title` 断言 `"# " not in md` 过于宽泛 | 改为 `not any(line.startswith("# ") for line in md.splitlines())`，只检查一级标题 |

## 后续计划

- Phase 2+ 可逐步增加集成测试（mock CDP/LLM）
- 可引入 pytest-cov 追踪覆盖率
- CI/CD 管线中集成 `uv run pytest`
