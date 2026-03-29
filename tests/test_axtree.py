from cliany_site.browser.axtree import (
    MAX_CHARS,
    _count_nested_contexts,
    axtree_to_markdown,
    extract_interactive_elements,
    serialize_axtree,
)


class TestSerializeAxtree:
    def test_empty_element_tree(self):
        assert "empty" in serialize_axtree({"element_tree": ""})

    def test_missing_element_tree_key(self):
        assert "empty" in serialize_axtree({})

    def test_short_text_unchanged(self):
        text = "button 'Submit' @ref=1"
        assert serialize_axtree({"element_tree": text}) == text

    def test_long_text_truncated(self):
        text = "x" * (MAX_CHARS + 500)
        result = serialize_axtree({"element_tree": text})
        assert len(result) < len(text)
        assert "truncated" in result
        assert str(len(text)) in result

    def test_exactly_max_chars_not_truncated(self):
        text = "a" * MAX_CHARS
        result = serialize_axtree({"element_tree": text})
        assert "truncated" not in result


class TestExtractInteractiveElements:
    def test_empty_selector_map(self):
        assert extract_interactive_elements({"selector_map": {}}) == []

    def test_missing_selector_map(self):
        assert extract_interactive_elements({}) == []

    def test_extracts_elements(self):
        tree = {
            "selector_map": {
                "1": {"ref": "1", "role": "button", "name": "OK", "attributes": {}},
                "2": {
                    "ref": "2",
                    "role": "link",
                    "name": "Home",
                    "attributes": {"href": "/"},
                },
            }
        }
        result = extract_interactive_elements(tree)
        assert len(result) == 2
        assert result[0]["role"] == "button"
        assert result[1]["name"] == "Home"

    def test_missing_fields_use_defaults(self):
        tree = {"selector_map": {"5": {}}}
        result = extract_interactive_elements(tree)
        assert len(result) == 1
        assert result[0]["ref"] == "5"
        assert result[0]["role"] == "unknown"
        assert result[0]["name"] == ""
        assert result[0]["attributes"] == {}


class TestAxtreeToMarkdown:
    def test_full_tree(self):
        tree = {
            "url": "https://example.com",
            "title": "Test Page",
            "element_tree": "button 'Submit'",
        }
        md = axtree_to_markdown(tree)
        assert "# Test Page" in md
        assert "URL: https://example.com" in md
        assert "button 'Submit'" in md
        assert "## Interactive Elements" in md

    def test_missing_title(self):
        tree = {"url": "https://example.com", "title": "", "element_tree": "content"}
        md = axtree_to_markdown(tree)
        assert not any(line.startswith("# ") for line in md.splitlines())
        assert "URL: https://example.com" in md

    def test_missing_url(self):
        tree = {"url": "", "title": "Page", "element_tree": "content"}
        md = axtree_to_markdown(tree)
        assert "URL:" not in md
        assert "# Page" in md

    def test_empty_tree(self):
        md = axtree_to_markdown({})
        assert "empty" in md


class TestExtractInteractiveElementsWithContext:
    def test_includes_frame_id_when_present(self):
        tree = {
            "selector_map": {
                "1": {"ref": "1", "role": "button", "name": "OK", "attributes": {}, "frame_id": "frame-abc"},
            }
        }
        result = extract_interactive_elements(tree)
        assert result[0]["frame_id"] == "frame-abc"

    def test_includes_shadow_root_type_when_present(self):
        tree = {
            "selector_map": {
                "1": {"ref": "1", "role": "input", "name": "", "attributes": {}, "shadow_root_type": "open"},
            }
        }
        result = extract_interactive_elements(tree)
        assert result[0]["shadow_root_type"] == "open"

    def test_omits_frame_id_when_absent(self):
        tree = {
            "selector_map": {
                "1": {"ref": "1", "role": "button", "name": "OK", "attributes": {}},
            }
        }
        result = extract_interactive_elements(tree)
        assert "frame_id" not in result[0]

    def test_omits_shadow_root_type_when_absent(self):
        tree = {
            "selector_map": {
                "1": {"ref": "1", "role": "button", "name": "OK", "attributes": {}},
            }
        }
        result = extract_interactive_elements(tree)
        assert "shadow_root_type" not in result[0]


class TestCountNestedContexts:
    def _make_element(self, frame_id=None, shadow_root_type=None):
        class FakeElement:
            def __init__(self):
                self.frame_id: str | None = None
                self.shadow_root_type: str | None = None

        el = FakeElement()
        if frame_id is not None:
            el.frame_id = frame_id
        if shadow_root_type is not None:
            el.shadow_root_type = shadow_root_type
        return el

    def test_no_iframes_no_shadow(self):
        elements = {0: self._make_element(), 1: self._make_element()}
        stats = _count_nested_contexts(elements)
        assert stats["iframe_count"] == 0
        assert stats["shadow_root_count"] == 0

    def test_single_frame_id_no_iframe(self):
        elements = {
            0: self._make_element(frame_id="main"),
            1: self._make_element(frame_id="main"),
        }
        stats = _count_nested_contexts(elements)
        assert stats["iframe_count"] == 0
        assert stats["unique_frame_ids"] == 1

    def test_multiple_frame_ids_counted(self):
        elements = {
            0: self._make_element(frame_id="main"),
            1: self._make_element(frame_id="iframe-1"),
            2: self._make_element(frame_id="iframe-2"),
        }
        stats = _count_nested_contexts(elements)
        assert stats["iframe_count"] == 2
        assert stats["unique_frame_ids"] == 3

    def test_shadow_roots_counted(self):
        elements = {
            0: self._make_element(shadow_root_type="open"),
            1: self._make_element(shadow_root_type="closed"),
            2: self._make_element(),
        }
        stats = _count_nested_contexts(elements)
        assert stats["shadow_root_count"] == 2

    def test_mixed_iframes_and_shadow(self):
        elements = {
            0: self._make_element(frame_id="main"),
            1: self._make_element(frame_id="iframe-1", shadow_root_type="open"),
            2: self._make_element(frame_id="iframe-1"),
        }
        stats = _count_nested_contexts(elements)
        assert stats["iframe_count"] == 1
        assert stats["shadow_root_count"] == 1


class TestAxtreeToMarkdownWithContext:
    def test_shows_nested_context_info(self):
        tree = {
            "url": "https://example.com",
            "title": "Page",
            "element_tree": "content",
            "iframe_count": 2,
            "shadow_root_count": 3,
        }
        md = axtree_to_markdown(tree)
        assert "2 iframe(s)" in md
        assert "3 shadow root(s)" in md

    def test_no_context_line_when_zero(self):
        tree = {
            "url": "https://example.com",
            "title": "Page",
            "element_tree": "content",
            "iframe_count": 0,
            "shadow_root_count": 0,
        }
        md = axtree_to_markdown(tree)
        assert "iframe" not in md.lower()
        assert "shadow" not in md.lower()
