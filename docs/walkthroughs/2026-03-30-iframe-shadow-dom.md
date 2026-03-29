# Phase 4.4 iframe / Shadow DOM 支持

**日期:** 2026-03-30
**Phase:** 4.4 (v0.5.0 生态建设)
**状态:** 已完成

## 概述

解除 cliany-site 之前"不支持 iframe 内元素操作"的限制。通过利用 browser-use DomService 已有的递归 iframe 采集和 Shadow DOM 穿透能力，在我们的包装层（axtree.py / action_runtime.py）中正确传播 frame_id、target_id、shadow_root_type 等上下文信息，实现对嵌套页面结构的感知和精确匹配。

## 关键发现

browser-use 的 `DomService` 已内建完整的 iframe/Shadow DOM 支持：
- `DOM.getDocument(depth=-1, pierce=True)` 穿透 Shadow DOM
- `_get_ax_tree_for_all_frames()` 递归采集所有 frame 的 AX Tree
- `EnhancedDOMTreeNode` 包含 `frame_id`、`target_id`、`shadow_root_type` 等字段
- `BrowserSession.get_element_by_index()` 自动处理跨 frame 的事件分发

问题在于我们的包装层 `capture_axtree()` 构建的简化 selector_map 丢弃了这些信息。

## 变更清单

### 4.4.1 配置参数

**文件:** `src/cliany_site/config.py`

- 新增 `cross_origin_iframes: bool`（默认 True）— 是否采集跨域 iframe
- 新增 `max_iframes: int`（默认 100）— 最大 iframe 处理数量
- 新增 `max_iframe_depth: int`（默认 5）— iframe 最大嵌套深度
- 对应环境变量：`CLIANY_CROSS_ORIGIN_IFRAMES`、`CLIANY_MAX_IFRAMES`、`CLIANY_MAX_IFRAME_DEPTH`

### 4.4.2 AXTree 采集富化

**文件:** `src/cliany_site/browser/axtree.py`

- `capture_axtree()` 将 `cross_origin_iframes`/`max_iframes`/`max_iframe_depth` 传递给 `DomService` 构造函数
- selector_map 每个条目增加可选字段：`frame_id`、`target_id`、`shadow_root_type`
- 返回结果增加 `iframe_count` 和 `shadow_root_count` 统计
- 新增 `_count_nested_contexts()` 统计唯一 frame ID 和 shadow root 数量
- `extract_interactive_elements()` 传播 `frame_id` 和 `shadow_root_type`
- `axtree_to_markdown()` 在有嵌套上下文时显示统计行

### 4.4.3 动作匹配增强

**文件:** `src/cliany_site/action_runtime.py`

- `_score_candidate()` 新增 frame_id 匹配评分（+10 分）
- `_score_candidate()` 新增 shadow_root_type 匹配评分（+5 分）
- 动作数据通过 `target_frame_id` 和 `target_shadow_root_type` 字段携带上下文

### 4.4.4 README 更新

**文件:** `README.md`、`README.en.md`

- 移除"目前不支持 iframe 内元素的自动操作"限制说明
- 替换为 iframe/Shadow DOM 支持说明及配置环境变量引用

### 4.4.5 测试覆盖

**文件:** `tests/test_axtree.py`、`tests/test_action_runtime.py`、`tests/test_config.py`

新增 24 个测试：
- `TestExtractInteractiveElementsWithContext` — 验证 frame_id/shadow_root_type 在有/无时的正确传播
- `TestCountNestedContexts` — 验证 iframe/shadow DOM 计数逻辑（单 frame、多 frame、混合场景）
- `TestAxtreeToMarkdownWithContext` — 验证 markdown 输出包含/不包含嵌套上下文信息
- `TestScoreCandidate` 扩展 — 验证 frame_id 匹配加分、不匹配无加分、shadow_root_type 匹配加分、组合评分

## 设计决策

1. **不实现自定义 frame 切换** — browser-use 的 `get_element_by_index()` 通过 `EnhancedDOMTreeNode` 上的 `target_id`/`session_id` 已自动处理跨 frame 事件分发
2. **frame_id 等字段仅在非空时写入** — 避免大量 null 值污染普通页面的 selector_map
3. **iframe_count 使用 unique_frame_ids - 1** — 主 frame 不算 iframe，只计额外嵌套的 frame
4. **跨域 iframe 默认启用** — 许多现代 Web 应用（支付、OAuth、嵌入式内容）依赖跨域 iframe

## 验证

- ruff check：通过
- mypy：通过
- pytest：583 个测试全部通过
