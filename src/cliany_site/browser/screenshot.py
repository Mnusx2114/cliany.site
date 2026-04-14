from __future__ import annotations

import base64
import logging
from io import BytesIO
from typing import Any

logger = logging.getLogger(__name__)


async def capture_screenshot(
    browser_session: Any,
    *,
    format: str = "jpeg",
    quality: int = 75,
    full_page: bool = False,
) -> bytes:
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
    if not data:
        return ""
    media_type = f"image/{format}"
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def screenshot_to_raw_base64(data: bytes) -> str:
    if not data:
        return ""
    return base64.b64encode(data).decode("ascii")


def annotate_screenshot_with_som(
    screenshot_data: bytes,
    selector_map: dict[str, dict],
    *,
    format: str = "jpeg",
    quality: int = 75,
    max_labels: int = 50,
) -> tuple[bytes, dict[str, str]]:
    if not screenshot_data:
        return b"", {}

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("Pillow 未安装，跳过 SoM 标注 (pip install Pillow)")
        return screenshot_data, {}

    img = Image.open(BytesIO(screenshot_data))
    draw = ImageDraw.Draw(img, "RGBA")

    font: ImageFont.FreeTypeFont | ImageFont.ImageFont
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 12)
    except OSError:
        try:
            font = ImageFont.truetype("DejaVuSansMono.ttf", 12)
        except OSError:
            font = ImageFont.load_default()

    ref_to_label: dict[str, str] = {}
    label_idx = 0

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

        text_bbox = draw.textbbox((0, 0), label, font=font)
        tw = text_bbox[2] - text_bbox[0] + 6
        th = text_bbox[3] - text_bbox[1] + 4

        lx = max(0, int(x) - 2)
        ly = max(0, int(y) - th - 2)

        draw.rectangle([lx, ly, lx + tw, ly + th], fill=(255, 0, 0, 180))
        draw.text((lx + 3, ly + 2), label, fill=(255, 255, 255, 255), font=font)
        draw.rectangle(
            [int(x), int(y), int(x + w), int(y + h)],
            outline=(255, 0, 0, 120),
            width=2,
        )

    output = BytesIO()
    if format == "png":
        img.save(output, format="PNG")
    else:
        converted_img = img.convert("RGB")
        converted_img.save(output, format="JPEG", quality=quality)

    annotated_data = output.getvalue()
    logger.debug("SoM 标注完成: %d 个元素, 输出 %d bytes", label_idx, len(annotated_data))
    return annotated_data, ref_to_label


async def enrich_selector_map_with_bounds(
    browser_session: Any,
    selector_map: dict[str, dict],
) -> dict[str, dict]:
    if not selector_map:
        return selector_map

    enriched = dict(selector_map)

    for ref, element in enriched.items():
        if not isinstance(element, dict):
            continue
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
