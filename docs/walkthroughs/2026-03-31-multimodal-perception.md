# v0.7.0 多模态感知 — 变更说明

**日期:** 2026-03-31
**分支:** master

## 变更摘要

为 cliany-site 探索引擎和动作执行引擎引入截图 + Vision LLM 双通道感知能力。当 AXTree 文本描述不足以理解页面时，通过截图 + SoM 标注 + 多模态 LLM 调用进行视觉辅助，提升探索成功率。

## 架构

```
capture_axtree() ──┬── AXTree 文本（原有）
                   └── 截图 bytes（新增，vision_enabled 时）
                         │
                         ▼
              enrich_selector_map_with_bounds()
                         │
                         ▼
              annotate_screenshot_with_som()
                         │
                         ▼
              build_multimodal_message()  →  LLM.ainvoke([HumanMessage])
```

### 元素定位分层策略

```
L0 精确匹配（@ref 直接命中）
  └─ L1 模糊匹配（_score_candidate 评分）
       └─ L2 自适应修复（LLM 文本修复，adaptive_repair）
            └─ L3 Vision 定位（截图 + Vision LLM 视觉匹配）← 新增
```

## 新增文件

| 文件 | 职责 |
|------|------|
| `src/cliany_site/browser/screenshot.py` | 截图采集、base64 编码、SoM 标注引擎、CDP 坐标采集 |
| `src/cliany_site/explorer/vision.py` | 多模态 LLM 消息构建、Vision 元素定位、响应解析 |
| `tests/test_screenshot.py` | 截图和标注模块测试（9 用例） |
| `tests/test_vision.py` | 多模态消息和定位模块测试（8 用例） |

## 修改文件

| 文件 | 变更 |
|------|------|
| `src/cliany_site/config.py` | 新增 5 个 Vision 配置字段 |
| `src/cliany_site/browser/axtree.py` | `capture_axtree()` 在 `vision_enabled` 时同步采集截图 |
| `src/cliany_site/explorer/engine.py` | `_invoke_llm_with_retry()` 支持 Message 对象；探索循环集成多模态调用 |
| `src/cliany_site/explorer/prompts.py` | 新增 `VISION_SUPPLEMENT_PROMPT` 和 `VISION_ELEMENT_LOCATE_PROMPT` |
| `src/cliany_site/action_runtime.py` | 新增 `_attempt_vision_locate()`；`_resolve_action_node()` 集成 L3 Vision 层 |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `CLIANY_VISION_ENABLED` | `false` | 是否启用 Vision 多模态感知 |
| `CLIANY_SCREENSHOT_FORMAT` | `jpeg` | 截图格式 (jpeg/png/webp) |
| `CLIANY_SCREENSHOT_QUALITY` | `75` | JPEG/WebP 压缩质量 |
| `CLIANY_VISION_MIN_CONFIDENCE` | `0.6` | Vision 定位最低置信度阈值 |
| `CLIANY_VISION_SOM_MAX_LABELS` | `50` | SoM 标注最大元素数 |

## 使用方式

```bash
export CLIANY_VISION_ENABLED=true
cliany-site explore "https://example.com" "执行某个工作流" --json
```

`vision_enabled` 默认关闭，不影响现有流程。开启后每步探索增加截图采集 + 可选 SoM 标注 + 多模态消息发送。

## 成本与性能

- 每步探索增加约 $0.005-0.01 Vision API 费用（仅 `vision_enabled=true` 时）
- 每步增加约 1-2 秒延迟（截图 + Vision API 调用）
- SoM 标注依赖 Pillow（可选），无 Pillow 时跳过标注，发送原始截图

## 已知限制

- Pillow 为可选依赖，未安装时 SoM 标注降级为无标注
- Vision API 增加网络延迟
- SoM 标注仅覆盖有 bounding box 坐标的元素
- `_attempt_vision_locate()` 会额外调用一次 `capture_axtree()`，增加定位延迟
