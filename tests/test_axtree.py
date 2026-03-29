from cliany_site.browser.axtree import (
    MAX_CHARS,
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
