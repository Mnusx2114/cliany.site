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
    from langchain_core.messages import HumanMessage

    if not screenshot_data:
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
