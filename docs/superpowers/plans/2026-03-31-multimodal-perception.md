# v0.7.0 多模态感知 — 详细实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 cliany-site 探索引擎和动作执行引擎引入截图 + Vision LLM 双通道感知能力，在 AXTree 不足时用视觉理解兜底，将探索成功率从约 70% 提升到 90%+。

**Architecture:** 分五个独立 Chunk 递进推进：
1. **截图基础设施** — 在 AXTree 采集同时截取页面截图，构建截图管道
2. **SoM 标注引擎** — 在截图上叠加编号标记（Set-of-Mark），让 LLM 可通过编号指示元素
3. **多模态探索提示词** — 改造 LLM 调用链路支持图文混合输入，增强页面理解
4. **视觉兜底元素定位** — 当 AXTree 模糊匹配失败时，用 Vision LLM + 截图定位元素
5. **配置、测试与文档** — 配置项、单元测试、walkthrough 文档

**Tech Stack:** Python 3.11, browser-use (BrowserSession.take_screenshot/add_highlights), LangChain (ChatAnthropic/ChatOpenAI with vision), Pillow (截图标注), base64

**前置约束：**
- browser-use 已内置 `BrowserSession.take_screenshot(format, quality, full_page, clip) -> bytes` 和 `BrowserSession.add_highlights(selector_map)` 方法，直接复用
- LangChain 的 `ChatAnthropic` 和 `ChatOpenAI` 均支持 `HumanMessage(content=[{"type": "image_url", ...}, {"type": "text", ...}])` 多模态消息格式
- 当前 LLM 调用入口为 `engine.py:331` 的 `llm.ainvoke(prompt)`，需改为传入 `HumanMessage` 对象

---

## 文件结构总览

### 新建文件

| 文件 | 职责 |
|------|------|
| `src/cliany_site/browser/screenshot.py` | 截图采集 + SoM 标注引擎 |
| `src/cliany_site/explorer/vision.py` | 多模态 LLM 消息构建 + Vision 元素定位 |
| `tests/test_screenshot.py` | 截图和标注模块单元测试 |
| `tests/test_vision.py` | 多模态消息构建和 Vision 定位测试 |
| `docs/walkthroughs/2026-03-31-multimodal-perception.md` | 变更说明文档 |

### 修改文件

| 文件 | 修改范围 |
|------|---------|
| `src/cliany_site/config.py` | 新增 Vision 相关配置项 |
| `src/cliany_site/browser/axtree.py` | `capture_axtree()` 同步采集截图 |
| `src/cliany_site/explorer/engine.py` | 探索循环集成多模态调用 |
| `src/cliany_site/explorer/prompts.py` | 新增 Vision 辅助提示词模板 |
| `src/cliany_site/action_runtime.py` | `_resolve_action_node()` 新增 Vision 兜底层 |

---

## Chunk 1: 截图基础设施

### Task 1: 新建截图模块

**Files:**
- Create: `src/cliany_site/browser/screenshot.py`

- [ ] **Step 1: 实现截图采集核心函数**

```python
"""
截图采集与 SoM 标注引擎

利用 browser-use BrowserSession.take_screenshot() 采集页面截图，
可选叠加编号标记（Set-of-Mark）用于 Vision LLM 元素指示。
"""

from __future__ import annotations

import base64
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def capture_screenshot(
    browser_session: Any,
    *,
    format: str = "jpeg",
    quality: int = 75,
    full_page: bool = False,
) -> bytes:
    """采集当前页面截图。

    Args:
        browser_session: browser-use BrowserSession 实例
        format: 图片格式 (jpeg/png/webp)
        quality: JPEG/WebP 压缩质量 (0-100)
        full_page: 是否采集整页（超出视口部分）

    Returns:
        截图二进制数据
    """
    try:
        data: bytes = await browser_session.take_screenshot(
            format=format,
            quality=quality,
            full_page=full_page,
        )
        logger.debug("截图完成: format=%s size=%d bytes", format, len(data))
        return data
    except (RuntimeError, OSError, AttributeError) as exc:
        logger.warning("截图失败: %s", exc)
        return b""


def screenshot_to_base64(data: bytes, format: str = "jpeg") -> str:
    """将截图二进制数据编码为 base64 data URL。"""
    if not data:
        return ""
    media_type = f"image/{format}"
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def screenshot_to_raw_base64(data: bytes) -> str:
    """将截图二进制数据编码为原始 base64 字符串（无 data URL 前缀）。"""
    if not data:
        return ""
    return base64.b64encode(data).decode("ascii")
```

- [ ] **Step 2: 运行 lint 确认无错误**

Run: `uv run ruff check src/cliany_site/browser/screenshot.py`

- [ ] **Step 3: Commit**

```bash
git add src/cliany_site/browser/screenshot.py
git commit -m "feat(browser): 新增截图采集模块 — capture_screenshot + base64 编码"
```

### Task 2: 在 AXTree 采集时同步截图

**Files:**
- Modify: `src/cliany_site/browser/axtree.py`

- [ ] **Step 4: 修改 capture_axtree() 返回截图数据**

在 `capture_axtree()` 函数中，AXTree 采集完成后（`serialize_axtree` 之前的位置），新增截图采集逻辑：

```python
# 在 axtree.py 顶部新增 import
from cliany_site.browser.screenshot import capture_screenshot

# 在 capture_axtree() 中，url/title 获取之后、return 之前：
    # --- 可选截图采集 ---
    screenshot_data = b""
    if cfg.vision_enabled:
        screenshot_data = await capture_screenshot(
            browser_session,
            format=cfg.screenshot_format,
            quality=cfg.screenshot_quality,
        )

# 在返回的 dict 中新增字段：
    return {
        "element_tree": element_tree_text,
        "selector_map": selector_map,
        "url": url,
        "title": title,
        "iframe_count": nested_stats["iframe_count"],
        "shadow_root_count": nested_stats["shadow_root_count"],
        "screenshot": screenshot_data,  # 新增
    }
```

**注意：** `cfg.vision_enabled` 默认为 `False`，截图不影响现有流程。

- [ ] **Step 5: 运行现有测试确认无回归**

Run: `uv run pytest tests/test_axtree.py -v`

- [ ] **Step 6: Commit**

```bash
git add src/cliany_site/browser/axtree.py
git commit -m "feat(axtree): capture_axtree 支持同步采集截图（vision_enabled 控制）"
```

---

## Chunk 2: SoM 标注引擎

### Task 3: 实现 Set-of-Mark 截图标注

**Files:**
- Modify: `src/cliany_site/browser/screenshot.py`

- [ ] **Step 7: 实现 SoM 标注函数**

在 `screenshot.py` 末尾追加 SoM 标注实现。利用 Pillow 在截图上绘制编号标记：

```python
from io import BytesIO
from typing import Any

def annotate_screenshot_with_som(
    screenshot_data: bytes,
    selector_map: dict[str, dict],
    *,
    format: str = "jpeg",
    quality: int = 75,
    max_labels: int = 50,
) -> tuple[bytes, dict[str, str]]:
    """在截图上叠加 Set-of-Mark 编号标记。

    利用 selector_map 中元素的坐标信息，在截图对应位置绘制编号标签。
    
    Args:
        screenshot_data: 原始截图二进制
        selector_map: AXTree selector_map（含元素位置信息）
        format: 输出图片格式
        quality: 输出压缩质量
        max_labels: 最多标注的元素数量

    Returns:
        (标注后截图 bytes, ref→标签号映射 dict)
    """
    if not screenshot_data:
        return b"", {}

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("Pillow 未安装，跳过 SoM 标注 (pip install Pillow)")
        return screenshot_data, {}

    img = Image.open(BytesIO(screenshot_data))
    draw = ImageDraw.Draw(img, "RGBA")

    # 尝试加载等宽字体，失败则用默认
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 12)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("DejaVuSansMono.ttf", 12)
        except (OSError, IOError):
            font = ImageFont.load_default()

    ref_to_label: dict[str, str] = {}
    label_idx = 0

    # 按 ref 数值排序，优先标注交互元素
    sorted_refs = sorted(
        selector_map.keys(),
        key=lambda r: int(r) if r.isdigit() else 999999,
    )

    for ref in sorted_refs:
        if label_idx >= max_labels:
            break

        element = selector_map[ref]
        if not isinstance(element, dict):
            continue

        # 从 attributes 中提取坐标（如果有 bounding box 信息）
        attrs = element.get("attributes", {})
        # 尝试从 _bounds 字段获取位置（需要在 enrich_selector_map 中填充）
        bounds = element.get("_bounds")
        if not bounds:
            continue

        x = bounds.get("x", 0)
        y = bounds.get("y", 0)
        w = bounds.get("width", 0)
        h = bounds.get("height", 0)
        if w <= 0 or h <= 0:
            continue

        label = str(label_idx)
        ref_to_label[ref] = label
        label_idx += 1

        # 绘制半透明背景 + 编号文字
        text_bbox = draw.textbbox((0, 0), label, font=font)
        tw = text_bbox[2] - text_bbox[0] + 6
        th = text_bbox[3] - text_bbox[1] + 4

        # 标签位置：元素左上角
        lx = max(0, int(x) - 2)
        ly = max(0, int(y) - th - 2)

        draw.rectangle(
            [lx, ly, lx + tw, ly + th],
            fill=(255, 0, 0, 180),
        )
        draw.text(
            (lx + 3, ly + 2),
            label,
            fill=(255, 255, 255, 255),
            font=font,
        )

        # 元素边框高亮
        draw.rectangle(
            [int(x), int(y), int(x + w), int(y + h)],
            outline=(255, 0, 0, 120),
            width=2,
        )

    # 编码输出
    output = BytesIO()
    if format == "png":
        img.save(output, format="PNG")
    else:
        img = img.convert("RGB")  # JPEG 不支持 RGBA
        img.save(output, format="JPEG", quality=quality)

    annotated_data = output.getvalue()
    logger.debug("SoM 标注完成: %d 个元素, 输出 %d bytes", label_idx, len(annotated_data))
    return annotated_data, ref_to_label
```

- [ ] **Step 8: 新增 CDP 获取元素坐标的辅助函数**

在 `screenshot.py` 中新增通过 CDP 获取元素 bounding box 的函数，用于填充 selector_map 的坐标：

```python
async def enrich_selector_map_with_bounds(
    browser_session: Any,
    selector_map: dict[str, dict],
) -> dict[str, dict]:
    """为 selector_map 中的元素补充 bounding box 坐标信息。

    通过 browser-use 的 get_element_coordinates CDP 调用获取每个元素的位置。
    结果写入 element["_bounds"] = {"x", "y", "width", "height"}。
    """
    if not selector_map:
        return selector_map

    enriched = dict(selector_map)

    for ref, element in enriched.items():
        if not isinstance(element, dict):
            continue
        # 跳过已有坐标的
        if "_bounds" in element:
            continue

        try:
            ref_idx = int(ref)
            node = await browser_session.get_dom_element_by_index(ref_idx)
            if node and hasattr(node, "absolute_position") and node.absolute_position:
                pos = node.absolute_position
                element["_bounds"] = {
                    "x": pos.x,
                    "y": pos.y,
                    "width": pos.width,
                    "height": pos.height,
                }
        except (ValueError, IndexError, KeyError, RuntimeError, OSError, AttributeError):
            continue

    return enriched
```

- [ ] **Step 9: 运行 lint**

Run: `uv run ruff check src/cliany_site/browser/screenshot.py`

- [ ] **Step 10: Commit**

```bash
git add src/cliany_site/browser/screenshot.py
git commit -m "feat(screenshot): SoM 标注引擎 — Pillow 绘制编号标记 + CDP 坐标采集"
```

---

## Chunk 3: 多模态探索提示词 + LLM 调用改造

### Task 4: 新增 Vision 辅助提示词

**Files:**
- Modify: `src/cliany_site/explorer/prompts.py`

- [ ] **Step 11: 在 prompts.py 末尾新增 Vision 提示词**

```python
VISION_SUPPLEMENT_PROMPT = """## 页面截图分析

你同时收到了页面的截图（带编号标记）。截图中红色编号标签标注了可交互元素的位置。

当 AXTree 文本描述不够清晰时（例如元素没有 name、role 不明确），请参考截图中的视觉信息：
- 编号标签旁边的元素就是对应的交互目标
- 截图可帮助你理解页面布局、视觉层级和元素分组关系
- 如果 AXTree 中看不到某个元素但截图中可见，说明它可能是自定义组件或 canvas 元素

**重要：** 你在 actions 中引用的 ref 编号仍然是 AXTree 中的 @ref 编号，不是截图标签编号。截图标签仅供辅助理解。"""


VISION_ELEMENT_LOCATE_PROMPT = """你是一个页面元素定位专家。

你会收到：
1. 页面截图（带编号标记）
2. 要定位的目标元素描述
3. 当前页面的 AXTree 可交互元素列表

你的任务是找到与目标描述最匹配的元素，返回其 @ref 编号。

目标元素：
- 动作类型: {action_type}
- 元素描述: {description}
- 原始名称: {target_name}
- 原始角色: {target_role}

请返回 JSON：
```json
{{
  "ref": "匹配的 @ref 编号",
  "confidence": 0.0-1.0 之间的置信度,
  "reasoning": "你的判断依据（中文）"
}}
```

如果找不到匹配的元素，ref 返回空字符串，confidence 返回 0。"""
```

- [ ] **Step 12: Commit**

```bash
git add src/cliany_site/explorer/prompts.py
git commit -m "feat(prompts): 新增 Vision 辅助提示词和元素定位提示词"
```

### Task 5: 新建 Vision LLM 消息构建模块

**Files:**
- Create: `src/cliany_site/explorer/vision.py`

- [ ] **Step 13: 实现多模态消息构建**

```python
"""
多模态 Vision LLM 集成

构建图文混合的 LangChain HumanMessage，支持将截图嵌入 LLM 调用。
提供 Vision 兜底元素定位能力。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from cliany_site.browser.screenshot import screenshot_to_raw_base64

logger = logging.getLogger(__name__)


def build_multimodal_message(
    text_prompt: str,
    screenshot_data: bytes,
    *,
    screenshot_format: str = "jpeg",
) -> Any:
    """构建包含截图的多模态 LangChain HumanMessage。

    Args:
        text_prompt: 文本提示词
        screenshot_data: 截图二进制数据
        screenshot_format: 截图格式 (jpeg/png)

    Returns:
        LangChain HumanMessage 对象（图文混合）
    """
    from langchain_core.messages import HumanMessage

    if not screenshot_data:
        # 无截图时降级为纯文本
        return HumanMessage(content=text_prompt)

    b64 = screenshot_to_raw_base64(screenshot_data)
    media_type = f"image/{screenshot_format}"

    return HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{b64}",
                },
            },
            {
                "type": "text",
                "text": text_prompt,
            },
        ]
    )


def build_vision_locate_message(
    action_data: dict[str, Any],
    screenshot_data: bytes,
    element_tree_text: str,
    *,
    screenshot_format: str = "jpeg",
) -> Any:
    """构建 Vision 元素定位的多模态消息。

    用于 AXTree 模糊匹配失败后的 Vision 兜底定位。
    """
    from cliany_site.explorer.prompts import VISION_ELEMENT_LOCATE_PROMPT

    prompt_text = VISION_ELEMENT_LOCATE_PROMPT.format(
        action_type=action_data.get("type", "click"),
        description=action_data.get("description", ""),
        target_name=action_data.get("target_name", ""),
        target_role=action_data.get("target_role", ""),
    )
    prompt_text += f"\n\n## 页面可交互元素\n{element_tree_text}"

    return build_multimodal_message(
        prompt_text,
        screenshot_data,
        screenshot_format=screenshot_format,
    )


def parse_vision_locate_response(text: str) -> dict[str, Any]:
    """解析 Vision 元素定位响应。

    Returns:
        {"ref": str, "confidence": float, "reasoning": str}
    """
    # 尝试提取 JSON
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(0))
            return {
                "ref": str(result.get("ref", "")),
                "confidence": float(result.get("confidence", 0)),
                "reasoning": str(result.get("reasoning", "")),
            }
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    return {"ref": "", "confidence": 0, "reasoning": "响应解析失败"}
```

- [ ] **Step 14: Commit**

```bash
git add src/cliany_site/explorer/vision.py
git commit -m "feat(vision): 多模态 LLM 消息构建 + Vision 元素定位能力"
```

### Task 6: 改造探索循环集成多模态调用

**Files:**
- Modify: `src/cliany_site/explorer/engine.py`

- [ ] **Step 15: 修改 _invoke_llm_with_retry 支持 Message 对象输入**

当前 `_invoke_llm_with_retry()` 的 `prompt` 参数是 `str`。改为 `str | Any`，当传入 `HumanMessage` 时直接透传：

在 `engine.py:320-344` 修改 `_invoke_llm_with_retry`：

```python
async def _invoke_llm_with_retry(
    llm: Any,
    prompt: Any,  # str 或 LangChain Message 对象
    *,
    max_attempts: int = 3,
    base_delay: float = 2.0,
    backoff_factor: float = 2.0,
) -> Any:
    """带指数退避重试的 LLM 调用。支持纯文本和多模态消息。"""
    for attempt in range(max_attempts):
        try:
            # LangChain ainvoke 统一支持 str 和 Message 列表
            if isinstance(prompt, str):
                return await llm.ainvoke(prompt)
            else:
                # 多模态 Message 对象，包装为列表传入
                from langchain_core.messages import SystemMessage
                messages = [prompt] if not isinstance(prompt, list) else prompt
                return await llm.ainvoke(messages)
        except Exception as exc:
            if not _is_retryable_error(exc) or attempt >= max_attempts - 1:
                raise
            delay = base_delay * (backoff_factor ** attempt)
            logger.warning(
                "LLM 调用失败 (第 %d/%d 次): %s — %.1f 秒后重试",
                attempt + 1, max_attempts, exc, delay,
            )
            await asyncio.sleep(delay)
    raise RuntimeError("LLM 重试逻辑异常")
```

- [ ] **Step 16: 修改探索循环在 vision_enabled 时发送多模态消息**

在 `engine.py` 的 `WorkflowExplorer.explore()` 方法中（约 L450-498），修改 LLM 调用逻辑：

```python
# 在 explore() 方法内，构建 prompt_text 之后（约 L466-477 之后）：

                # --- Vision 多模态增强 ---
                screenshot_data = tree.get("screenshot", b"")
                if cfg.vision_enabled and screenshot_data:
                    from cliany_site.browser.screenshot import (
                        annotate_screenshot_with_som,
                        enrich_selector_map_with_bounds,
                    )
                    from cliany_site.explorer.prompts import VISION_SUPPLEMENT_PROMPT
                    from cliany_site.explorer.vision import build_multimodal_message

                    # 采集坐标 + SoM 标注
                    enriched_map = await enrich_selector_map_with_bounds(
                        browser_session, selector_map,
                    )
                    annotated_screenshot, ref_to_label = annotate_screenshot_with_som(
                        screenshot_data, enriched_map,
                        format=cfg.screenshot_format,
                        quality=cfg.screenshot_quality,
                    )

                    # 构建多模态消息
                    full_text = f"{SYSTEM_PROMPT}\n\n{prompt_text}\n\n{VISION_SUPPLEMENT_PROMPT}"
                    llm_input = build_multimodal_message(
                        full_text,
                        annotated_screenshot or screenshot_data,
                        screenshot_format=cfg.screenshot_format,
                    )
                else:
                    llm_input = f"{SYSTEM_PROMPT}\n\n{prompt_text}"

                try:
                    logger.debug("步骤 %d: 调用 LLM (page=%s vision=%s)",
                                 step_num + 1, tree.get("url", ""),
                                 bool(cfg.vision_enabled and screenshot_data))
                    reporter.on_explore_llm_start(step_num)
                    response = await _invoke_llm_with_retry(
                        llm,
                        llm_input,  # 替换原来的纯文本 prompt
                        max_attempts=cfg.llm_retry_max_attempts,
                        base_delay=cfg.llm_retry_base_delay,
                        backoff_factor=cfg.llm_retry_backoff_factor,
                    )
```

- [ ] **Step 17: 运行现有测试确认无回归**

Run: `uv run pytest tests/test_engine.py -v`

- [ ] **Step 18: Commit**

```bash
git add src/cliany_site/explorer/engine.py
git commit -m "feat(engine): 探索循环集成 Vision 多模态 — 截图 + SoM 标注 + 图文消息"
```

---

## Chunk 4: Vision 兜底元素定位

### Task 7: 在 action_runtime 中新增 Vision 定位层

**Files:**
- Modify: `src/cliany_site/action_runtime.py`

- [ ] **Step 19: 新增 _attempt_vision_locate() 函数**

在 `action_runtime.py` 中 `_attempt_adaptive_repair()` 之前（约 L256 处）新增 Vision 定位函数：

```python
async def _attempt_vision_locate(
    browser_session: Any,
    action_data: dict[str, Any],
) -> Any | None:
    """Vision LLM 兜底元素定位。

    当 AXTree 模糊匹配和自适应修复均失败时，
    使用截图 + Vision LLM 尝试视觉定位目标元素。
    
    执行策略分层：
    - L0 精确匹配（_resolve_action_node 直接命中）
    - L1 模糊匹配（_score_candidate 找到相似元素）
    - L2 自适应修复（_attempt_adaptive_repair LLM 文本修复）
    - L3 Vision 定位（本函数 — Vision LLM 视觉定位）← 新增
    """
    import importlib

    from cliany_site.browser.axtree import capture_axtree, serialize_axtree
    from cliany_site.browser.screenshot import (
        annotate_screenshot_with_som,
        capture_screenshot,
        enrich_selector_map_with_bounds,
    )
    from cliany_site.config import get_config
    from cliany_site.explorer.vision import (
        build_vision_locate_message,
        parse_vision_locate_response,
    )

    cfg = get_config()
    if not cfg.vision_enabled:
        return None

    try:
        engine_module = importlib.import_module("cliany_site.explorer.engine")
        get_llm = getattr(engine_module, "_get_llm", None)
        if not callable(get_llm):
            return None
        llm = get_llm(role="explore")  # Vision 需要较强模型
    except (ImportError, OSError, ValueError):
        return None

    # 采集截图 + AXTree
    screenshot_data = await capture_screenshot(
        browser_session,
        format=cfg.screenshot_format,
        quality=cfg.screenshot_quality,
    )
    if not screenshot_data:
        return None

    tree = await capture_axtree(browser_session)
    selector_map = tree.get("selector_map", {})
    element_tree_text = serialize_axtree(tree)

    # SoM 标注
    enriched_map = await enrich_selector_map_with_bounds(browser_session, selector_map)
    annotated, ref_to_label = annotate_screenshot_with_som(
        screenshot_data, enriched_map,
        format=cfg.screenshot_format,
        quality=cfg.screenshot_quality,
    )

    # 构建 Vision 定位消息
    message = build_vision_locate_message(
        action_data,
        annotated or screenshot_data,
        element_tree_text,
        screenshot_format=cfg.screenshot_format,
    )

    try:
        response = await llm.ainvoke([message])
        response_text = str(getattr(response, "content", response))
        parsed = parse_vision_locate_response(response_text)
    except (RuntimeError, OSError, TypeError, ValueError) as exc:
        logger.debug("Vision 定位 LLM 调用失败: %s", exc)
        return None

    ref = parsed.get("ref", "")
    confidence = parsed.get("confidence", 0)
    reasoning = parsed.get("reasoning", "")

    if not ref or confidence < cfg.vision_min_confidence:
        logger.debug(
            "Vision 定位置信度不足: ref=%s confidence=%.2f reason=%s",
            ref, confidence, reasoning,
        )
        return None

    # 尝试通过 ref 获取元素
    ref_index = _parse_ref_to_index(ref)
    if ref_index is None:
        return None

    try:
        node = await browser_session.get_element_by_index(ref_index)
        logger.info(
            "Vision 定位成功: ref=%s confidence=%.2f reason=%s",
            ref, confidence, reasoning,
        )
        return node
    except (IndexError, KeyError, RuntimeError, OSError):
        return None
```

- [ ] **Step 20: 在 _resolve_action_node 末尾集成 Vision 定位**

修改 `_resolve_action_node()`（约 L399-439），在 adaptive_repair 之后新增 Vision 兜底：

```python
    # 在 _resolve_action_node() 中，adaptive_repair 判断之后：
    
    if _adaptive_repair_enabled():
        repaired = await _attempt_adaptive_repair(browser_session, action_data)
        if repaired is not None:
            return repaired

    # L3: Vision LLM 兜底定位（新增）
    vision_result = await _attempt_vision_locate(browser_session, action_data)
    if vision_result is not None:
        return vision_result

    return None
```

- [ ] **Step 21: 运行现有测试确认无回归**

Run: `uv run pytest tests/test_action_runtime.py -v`

- [ ] **Step 22: Commit**

```bash
git add src/cliany_site/action_runtime.py
git commit -m "feat(runtime): 新增 L3 Vision 兜底元素定位 — 截图 + Vision LLM 视觉匹配"
```

---

## Chunk 5: 配置、测试与文档

### Task 8: 新增 Vision 配置项

**Files:**
- Modify: `src/cliany_site/config.py`

- [ ] **Step 23: 在 ClanySiteConfig 中新增 Vision 配置**

在 `config.py` 的 `ClanySiteConfig` dataclass（L38-113）中追加字段：

```python
    # Vision 多模态配置
    vision_enabled: bool = False
    screenshot_format: str = "jpeg"
    screenshot_quality: int = 75
    vision_min_confidence: float = 0.6
    vision_som_max_labels: int = 50
```

在 `load_config()`（L116-136）中追加环境变量绑定：

```python
        vision_enabled=_env_bool("CLIANY_VISION_ENABLED", False),
        screenshot_format=os.environ.get("CLIANY_SCREENSHOT_FORMAT", "jpeg"),
        screenshot_quality=_env_int("CLIANY_SCREENSHOT_QUALITY", 75),
        vision_min_confidence=_env_float("CLIANY_VISION_MIN_CONFIDENCE", 0.6),
        vision_som_max_labels=_env_int("CLIANY_VISION_SOM_MAX_LABELS", 50),
```

在 `to_dict()` 中追加对应字段。

- [ ] **Step 24: 运行配置测试确认无回归**

Run: `uv run pytest tests/test_config.py -v`

- [ ] **Step 25: Commit**

```bash
git add src/cliany_site/config.py
git commit -m "feat(config): 新增 Vision 多模态配置项（vision_enabled、截图格式/质量/置信度/标注数）"
```

### Task 9: 截图模块单元测试

**Files:**
- Create: `tests/test_screenshot.py`

- [ ] **Step 26: 编写截图模块测试**

```python
"""截图采集与 SoM 标注模块测试。"""

import base64

import pytest


class TestScreenshotToBase64:
    def test_empty_data_returns_empty_string(self):
        from cliany_site.browser.screenshot import screenshot_to_base64
        assert screenshot_to_base64(b"") == ""

    def test_valid_data_returns_data_url(self):
        from cliany_site.browser.screenshot import screenshot_to_base64
        data = b"\x89PNG\r\n\x1a\nfakedata"
        result = screenshot_to_base64(data, format="png")
        assert result.startswith("data:image/png;base64,")
        # 解码验证
        b64_part = result.split(",", 1)[1]
        decoded = base64.b64decode(b64_part)
        assert decoded == data

    def test_jpeg_format(self):
        from cliany_site.browser.screenshot import screenshot_to_base64
        result = screenshot_to_base64(b"fake", format="jpeg")
        assert "image/jpeg" in result


class TestScreenshotToRawBase64:
    def test_empty_data(self):
        from cliany_site.browser.screenshot import screenshot_to_raw_base64
        assert screenshot_to_raw_base64(b"") == ""

    def test_valid_data(self):
        from cliany_site.browser.screenshot import screenshot_to_raw_base64
        data = b"hello world"
        result = screenshot_to_raw_base64(data)
        assert base64.b64decode(result) == data


class TestAnnotateScreenshotWithSom:
    """SoM 标注测试（需要 Pillow）。"""

    @pytest.fixture
    def sample_png(self):
        """生成一个 100x100 的纯色 PNG 用于测试。"""
        try:
            from PIL import Image
            from io import BytesIO
        except ImportError:
            pytest.skip("Pillow not installed")

        img = Image.new("RGB", (100, 100), (200, 200, 200))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_empty_screenshot_returns_empty(self):
        from cliany_site.browser.screenshot import annotate_screenshot_with_som
        data, mapping = annotate_screenshot_with_som(b"", {})
        assert data == b""
        assert mapping == {}

    def test_no_bounds_returns_original(self, sample_png):
        from cliany_site.browser.screenshot import annotate_screenshot_with_som
        selector_map = {"1": {"role": "button", "name": "Click"}}
        data, mapping = annotate_screenshot_with_som(sample_png, selector_map)
        # 无坐标信息则无标注
        assert len(data) > 0
        assert mapping == {}

    def test_with_bounds_annotates(self, sample_png):
        from cliany_site.browser.screenshot import annotate_screenshot_with_som
        selector_map = {
            "1": {
                "role": "button",
                "name": "Click",
                "_bounds": {"x": 10, "y": 10, "width": 30, "height": 20},
            }
        }
        data, mapping = annotate_screenshot_with_som(sample_png, selector_map)
        assert len(data) > 0
        assert "1" in mapping
        assert mapping["1"] == "0"  # 第一个标签编号为 "0"

    def test_max_labels_limit(self, sample_png):
        from cliany_site.browser.screenshot import annotate_screenshot_with_som
        selector_map = {
            str(i): {
                "role": "button",
                "name": f"Btn {i}",
                "_bounds": {"x": i * 2, "y": 10, "width": 10, "height": 10},
            }
            for i in range(100)
        }
        data, mapping = annotate_screenshot_with_som(
            sample_png, selector_map, max_labels=5,
        )
        assert len(mapping) == 5
```

- [ ] **Step 27: 运行截图测试**

Run: `uv run pytest tests/test_screenshot.py -v`
Expected: 7 passed

- [ ] **Step 28: Commit**

```bash
git add tests/test_screenshot.py
git commit -m "test: 截图采集与 SoM 标注模块单元测试（7 用例）"
```

### Task 10: Vision 模块单元测试

**Files:**
- Create: `tests/test_vision.py`

- [ ] **Step 29: 编写 Vision 模块测试**

```python
"""多模态 Vision LLM 集成测试。"""


class TestBuildMultimodalMessage:
    def test_empty_screenshot_returns_text_only(self):
        from cliany_site.explorer.vision import build_multimodal_message
        msg = build_multimodal_message("hello", b"")
        assert msg.content == "hello"

    def test_with_screenshot_returns_multimodal(self):
        from cliany_site.explorer.vision import build_multimodal_message
        msg = build_multimodal_message("hello", b"fake-image-data")
        assert isinstance(msg.content, list)
        assert len(msg.content) == 2
        assert msg.content[0]["type"] == "image_url"
        assert msg.content[1]["type"] == "text"
        assert msg.content[1]["text"] == "hello"

    def test_image_url_format(self):
        from cliany_site.explorer.vision import build_multimodal_message
        msg = build_multimodal_message("test", b"data", screenshot_format="png")
        url = msg.content[0]["image_url"]["url"]
        assert url.startswith("data:image/png;base64,")


class TestBuildVisionLocateMessage:
    def test_builds_message_with_action_data(self):
        from cliany_site.explorer.vision import build_vision_locate_message
        action = {
            "type": "click",
            "description": "点击搜索按钮",
            "target_name": "Search",
            "target_role": "button",
        }
        msg = build_vision_locate_message(
            action, b"screenshot", "element tree text",
        )
        assert isinstance(msg.content, list)
        text_part = msg.content[1]["text"]
        assert "click" in text_part
        assert "点击搜索按钮" in text_part
        assert "element tree text" in text_part


class TestParseVisionLocateResponse:
    def test_valid_json_response(self):
        from cliany_site.explorer.vision import parse_vision_locate_response
        text = '{"ref": "42", "confidence": 0.85, "reasoning": "按钮文字匹配"}'
        result = parse_vision_locate_response(text)
        assert result["ref"] == "42"
        assert result["confidence"] == 0.85
        assert "匹配" in result["reasoning"]

    def test_json_in_markdown(self):
        from cliany_site.explorer.vision import parse_vision_locate_response
        text = '```json\n{"ref": "7", "confidence": 0.9, "reasoning": "ok"}\n```'
        result = parse_vision_locate_response(text)
        assert result["ref"] == "7"

    def test_invalid_response(self):
        from cliany_site.explorer.vision import parse_vision_locate_response
        result = parse_vision_locate_response("这不是 JSON")
        assert result["ref"] == ""
        assert result["confidence"] == 0

    def test_empty_response(self):
        from cliany_site.explorer.vision import parse_vision_locate_response
        result = parse_vision_locate_response("")
        assert result["ref"] == ""
```

- [ ] **Step 30: 运行 Vision 测试**

Run: `uv run pytest tests/test_vision.py -v`
Expected: 8 passed

- [ ] **Step 31: Commit**

```bash
git add tests/test_vision.py
git commit -m "test: 多模态 Vision 模块单元测试（8 用例）"
```

### Task 11: 运行完整测试套件 + lint

- [ ] **Step 32: 运行全量测试**

Run: `uv run pytest tests/ -v --tb=short -q`
Expected: 583 + ~15 = ~598 passed, 0 failed

- [ ] **Step 33: 运行 lint + type check**

Run: `uv run ruff check src/ && uv run mypy src/cliany_site/browser/screenshot.py src/cliany_site/explorer/vision.py`

- [ ] **Step 34: Commit（如有 lint 修复）**

### Task 12: Walkthrough 文档

**Files:**
- Create: `docs/walkthroughs/2026-03-31-multimodal-perception.md`

- [ ] **Step 35: 编写变更说明文档**

内容要点：
- 变更摘要：引入截图 + Vision LLM 双通道感知
- 架构说明：截图管道、SoM 标注引擎、多模态消息构建、Vision 兜底定位
- 配置说明：`CLIANY_VISION_ENABLED`、`CLIANY_SCREENSHOT_FORMAT` 等环境变量
- 使用方式：`export CLIANY_VISION_ENABLED=true && cliany-site explore ...`
- 执行策略分层：L0 精确匹配 → L1 模糊匹配 → L2 自适应修复 → L3 Vision 定位
- 成本估算：每步探索增加 ~$0.005-0.01 Vision API 费用（仅 vision_enabled 时）
- 已知限制：依赖 Pillow（可选）、Vision API 增加延迟约 1-2 秒/步

- [ ] **Step 36: Commit**

```bash
git add docs/walkthroughs/2026-03-31-multimodal-perception.md
git commit -m "docs: v0.7.0 多模态感知变更说明 — 架构/配置/分层策略/成本"
```

---

## 依赖关系

```
Chunk 1 (截图基础设施)
  ├── Task 1: screenshot.py 核心函数 ← 无依赖
  └── Task 2: axtree.py 集成截图 ← 依赖 Task 1 + config (Chunk 5 Task 8)

Chunk 2 (SoM 标注引擎)
  └── Task 3: SoM 标注 + 坐标采集 ← 依赖 Task 1

Chunk 3 (多模态探索)
  ├── Task 4: Vision 提示词 ← 无依赖
  ├── Task 5: vision.py 消息构建 ← 依赖 Task 1
  └── Task 6: 探索循环集成 ← 依赖 Task 2 + Task 3 + Task 5

Chunk 4 (Vision 兜底定位)
  └── Task 7: action_runtime 集成 ← 依赖 Task 1 + Task 3 + Task 5

Chunk 5 (配置/测试/文档)
  ├── Task 8: config.py ← 无依赖，可与 Chunk 1 并行
  ├── Task 9-10: 测试 ← 依赖 Chunk 1-4 对应模块
  └── Task 12: 文档 ← 最后
```

**推荐执行顺序：** Task 8 → Task 1 → Task 2 → Task 3 → Task 4+5 → Task 6 → Task 7 → Task 9+10 → Task 11 → Task 12

---

## 新增依赖

| 包 | 用途 | 必选 |
|---|------|------|
| `Pillow` | SoM 截图标注绘制 | 可选（无 Pillow 时跳过标注，发送原始截图） |
| `langchain-core` | HumanMessage 多模态消息 | 已有（langchain-anthropic/openai 已依赖） |

**不需要新增 pip 依赖。** Pillow 作为可选依赖（SoM 标注降级为无标注），langchain-core 已通过现有依赖链引入。

---

## 配置项速查

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `CLIANY_VISION_ENABLED` | `false` | 是否启用 Vision 多模态感知 |
| `CLIANY_SCREENSHOT_FORMAT` | `jpeg` | 截图格式 (jpeg/png/webp) |
| `CLIANY_SCREENSHOT_QUALITY` | `75` | JPEG/WebP 压缩质量 |
| `CLIANY_VISION_MIN_CONFIDENCE` | `0.6` | Vision 定位最低置信度阈值 |
| `CLIANY_VISION_SOM_MAX_LABELS` | `50` | SoM 标注最大元素数 |

---

## 度量指标

| 指标 | v0.6.2 现状 | v0.7.0 目标 |
|------|------------|------------|
| 探索成功率（复杂页面） | ~70% | ≥85%（vision_enabled 时） |
| 元素定位失败率 | ~15% | ≤5%（L3 Vision 兜底后） |
| 每步探索耗时 | ~3-5s | ~5-7s（含截图+Vision，可接受） |
| 每步 API 成本增量 | $0 | ~$0.005-0.01（仅 vision_enabled 时） |
| 新增测试用例 | 0 | ≥15 |
| 新增代码量 | 0 | ~400-500 行 |
