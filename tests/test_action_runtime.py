
from cliany_site.action_runtime import (
    _action_has_href,
    _action_opens_new_tab,
    _extract_repair_selector_refs,
    _normalize_text,
    _parse_ref_to_index,
    _score_candidate,
    normalize_navigation_url,
    substitute_parameters,
)


class TestNormalizeText:
    def test_normal_text(self):
        assert _normalize_text("Hello") == "hello"

    def test_collapses_whitespace(self):
        assert _normalize_text("a  b\t\nc") == "a b c"

    def test_strips_edges(self):
        assert _normalize_text("  hello  ") == "hello"

    def test_none_input(self):
        assert _normalize_text(None) == ""

    def test_numeric_input(self):
        assert _normalize_text(123) == "123"


class TestParseRefToIndex:
    def test_ref_with_number(self):
        assert _parse_ref_to_index("ref_123") == 123

    def test_plain_number(self):
        assert _parse_ref_to_index("456") == 456

    def test_no_number(self):
        assert _parse_ref_to_index("nodigits") is None

    def test_empty_string(self):
        assert _parse_ref_to_index("") is None

    def test_none_input(self):
        assert _parse_ref_to_index(None) is None  # type: ignore[arg-type]

    def test_first_number_extracted(self):
        assert _parse_ref_to_index("a1b2") == 1


class TestNormalizeNavigationUrl:
    def test_valid_absolute_url(self):
        assert (
            normalize_navigation_url("https://example.com/page", "")
            == "https://example.com/page"
        )

    def test_http_url(self):
        assert (
            normalize_navigation_url("http://example.com", "") == "http://example.com"
        )

    def test_relative_url_with_current(self):
        result = normalize_navigation_url("/about", "https://example.com/page")
        assert result == "https://example.com/about"

    def test_relative_dot_slash(self):
        result = normalize_navigation_url("./other", "https://example.com/dir/page")
        assert "other" in result

    def test_query_string_relative(self):
        result = normalize_navigation_url("?q=test", "https://example.com/search")
        assert "q=test" in result

    def test_hash_relative(self):
        result = normalize_navigation_url("#section", "https://example.com/page")
        assert "#section" in result

    def test_none_input(self):
        assert normalize_navigation_url(None, "") == ""

    def test_non_string_input(self):
        assert normalize_navigation_url(42, "") == ""

    def test_empty_string(self):
        assert normalize_navigation_url("", "") == ""

    def test_spaces_in_url(self):
        assert normalize_navigation_url("has spaces", "") == ""

    def test_unwraps_quotes(self):
        assert (
            normalize_navigation_url('"https://example.com"', "")
            == "https://example.com"
        )

    def test_unwraps_brackets(self):
        assert (
            normalize_navigation_url("[https://example.com]", "")
            == "https://example.com"
        )

    def test_strips_trailing_punctuation(self):
        assert (
            normalize_navigation_url("https://example.com，", "")
            == "https://example.com"
        )

    def test_invalid_scheme(self):
        assert normalize_navigation_url("ftp://example.com", "") == ""

    def test_relative_without_current_url(self):
        assert normalize_navigation_url("/about", "") == ""


class TestSubstituteParameters:
    def test_no_params(self):
        actions = [{"value": "hello {{name}}"}]
        result = substitute_parameters(actions, {})
        assert result[0]["value"] == "hello {{name}}"

    def test_matching_params(self):
        actions = [{"value": "hello {{name}}", "url": "https://{{host}}/api"}]
        result = substitute_parameters(
            actions, {"name": "world", "host": "example.com"}
        )
        assert result[0]["value"] == "hello world"
        assert result[0]["url"] == "https://example.com/api"

    def test_missing_param_keeps_placeholder(self):
        actions = [{"value": "{{missing}}"}]
        result = substitute_parameters(actions, {"other": "val"})
        assert result[0]["value"] == "{{missing}}"

    def test_deep_copy(self):
        original = [{"value": "{{x}}"}]
        result = substitute_parameters(original, {"x": "replaced"})
        assert original[0]["value"] == "{{x}}"
        assert result[0]["value"] == "replaced"

    def test_non_string_field_skipped(self):
        actions = [{"value": 42}]
        result = substitute_parameters(actions, {"x": "y"})
        assert result[0]["value"] == 42

    def test_non_dict_params(self):
        actions = [{"value": "{{x}}"}]
        result = substitute_parameters(actions, None)  # type: ignore[arg-type]
        assert result[0]["value"] == "{{x}}"


class TestScoreCandidate:
    def test_exact_name_match(self):
        action = {"target_name": "Submit", "target_role": "", "target_attributes": {}}
        candidate = {"name": "Submit", "role": "", "attributes": {}}
        score = _score_candidate(action, candidate, "")
        assert score >= 40

    def test_partial_name_match(self):
        action = {
            "target_name": "Submit Button",
            "target_role": "",
            "target_attributes": {},
        }
        candidate = {"name": "Submit", "role": "", "attributes": {}}
        score = _score_candidate(action, candidate, "")
        assert 0 < score < 40

    def test_role_match(self):
        action = {"target_name": "", "target_role": "button", "target_attributes": {}}
        candidate = {"name": "", "role": "button", "attributes": {}}
        score = _score_candidate(action, candidate, "")
        assert score >= 15

    def test_attribute_id_match(self):
        action = {
            "target_name": "",
            "target_role": "",
            "target_attributes": {"id": "login-btn"},
        }
        candidate = {"name": "", "role": "", "attributes": {"id": "login-btn"}}
        score = _score_candidate(action, candidate, "")
        assert score >= 30

    def test_no_match(self):
        action = {
            "target_name": "Submit",
            "target_role": "button",
            "target_attributes": {"id": "a"},
        }
        candidate = {"name": "Cancel", "role": "link", "attributes": {"id": "b"}}
        score = _score_candidate(action, candidate, "")
        assert score == 0

    def test_class_overlap(self):
        action = {
            "target_name": "",
            "target_role": "",
            "target_attributes": {"class": "btn btn-primary large"},
        }
        candidate = {
            "name": "",
            "role": "",
            "attributes": {"class": "btn btn-primary small"},
        }
        score = _score_candidate(action, candidate, "")
        assert score >= 6  # 2 overlapping classes * 3 = 6

    def test_empty_inputs(self):
        assert _score_candidate({}, {}, "") == 0


class TestActionHasHref:
    def test_has_href(self):
        assert _action_has_href({"target_attributes": {"href": "/page"}}) is True

    def test_empty_href(self):
        assert _action_has_href({"target_attributes": {"href": ""}}) is False

    def test_no_attributes(self):
        assert _action_has_href({}) is False

    def test_non_dict_attributes(self):
        assert _action_has_href({"target_attributes": "not a dict"}) is False


class TestActionOpensNewTab:
    def test_blank_target(self):
        assert (
            _action_opens_new_tab({"target_attributes": {"target": "_blank"}}) is True
        )

    def test_other_target(self):
        assert (
            _action_opens_new_tab({"target_attributes": {"target": "_self"}}) is False
        )

    def test_no_target(self):
        assert _action_opens_new_tab({"target_attributes": {}}) is False

    def test_no_attributes(self):
        assert _action_opens_new_tab({}) is False


class TestExtractRepairSelectorRefs:
    def test_valid_response(self):
        parsed = {"selectors": ["ref_1", "ref_2", "ref_3"]}
        assert _extract_repair_selector_refs(parsed) == ["ref_1", "ref_2", "ref_3"]

    def test_deduplicates(self):
        parsed = {"selectors": ["ref_1", "ref_1", "ref_2"]}
        assert _extract_repair_selector_refs(parsed) == ["ref_1", "ref_2"]

    def test_non_dict_input(self):
        assert _extract_repair_selector_refs("not a dict") == []
        assert _extract_repair_selector_refs(None) == []

    def test_non_list_selectors(self):
        assert _extract_repair_selector_refs({"selectors": "not a list"}) == []

    def test_empty_selectors(self):
        assert _extract_repair_selector_refs({"selectors": []}) == []

    def test_filters_empty_strings(self):
        parsed = {"selectors": ["ref_1", "", None, "ref_2"]}
        result = _extract_repair_selector_refs(parsed)
        assert "ref_1" in result
        assert "ref_2" in result
        assert "" not in result
