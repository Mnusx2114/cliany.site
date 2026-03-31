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
            action,
            b"screenshot",
            "element tree text",
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
