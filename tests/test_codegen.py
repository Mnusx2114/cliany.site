from __future__ import annotations

from cliany_site.codegen.generator import (
    AdapterGenerator,
    _extract_commands_from_code,
    _extract_header_value,
    _safe_domain,
)
from cliany_site.codegen.naming import (
    sanitize_docstring_text,
    sanitize_inline_text,
    to_command_name,
    to_function_name,
    to_parameter_name,
    unique_parameter_name,
)
from cliany_site.codegen.templates import action_detail, render_args_payload, render_click_type, render_command_block


class TestToCommandName:
    def test_normal_name(self):
        assert to_command_name("search-repo", 0) == "search-repo"

    def test_uppercase_lowered(self):
        assert to_command_name("Search Repo", 0) == "search-repo"

    def test_special_chars_replaced(self):
        assert to_command_name("my!command@name", 0) == "my-command-name"

    def test_consecutive_separators_collapsed(self):
        assert to_command_name("a---b___c", 0) == "a-b-c"

    def test_empty_name_uses_index(self):
        assert to_command_name("", 0) == "command-1"
        assert to_command_name("", 4) == "command-5"

    def test_leading_digit_prefixed(self):
        assert to_command_name("123start", 0) == "cmd-123start"

    def test_whitespace_stripped(self):
        assert to_command_name("  hello  ", 0) == "hello"

    def test_none_handled(self):
        assert to_command_name("", 0) == "command-1"


class TestToFunctionName:
    def test_dashes_to_underscores(self):
        assert to_function_name("search-repo") == "search_repo"

    def test_special_chars_removed(self):
        assert to_function_name("a@b!c") == "a_b_c"

    def test_consecutive_underscores_collapsed(self):
        assert to_function_name("a--b--c") == "a_b_c"

    def test_empty_returns_default(self):
        assert to_function_name("") == "generated_command"

    def test_leading_digit_prefixed(self):
        assert to_function_name("1st-command") == "cmd_1st_command"

    def test_leading_trailing_stripped(self):
        assert to_function_name("-hello-") == "hello"


class TestToParameterName:
    def test_dashes_to_underscores(self):
        assert to_parameter_name("search-query") == "search_query"

    def test_special_chars_removed(self):
        assert to_parameter_name("my!param") == "my_param"

    def test_empty_returns_arg(self):
        assert to_parameter_name("") == "arg"

    def test_leading_digit_prefixed(self):
        assert to_parameter_name("2nd") == "arg_2nd"

    def test_consecutive_underscores_collapsed(self):
        assert to_parameter_name("a___b") == "a_b"

    def test_leading_trailing_stripped(self):
        assert to_parameter_name("_hello_") == "hello"


class TestUniqueParameterName:
    def test_not_taken(self):
        assert unique_parameter_name("query", set()) == "query"

    def test_taken_once(self):
        assert unique_parameter_name("query", {"query"}) == "query_2"

    def test_taken_multiple(self):
        assert unique_parameter_name("q", {"q", "q_2", "q_3"}) == "q_4"

    def test_does_not_mutate_used_set(self):
        used = {"query"}
        unique_parameter_name("query", used)
        assert used == {"query"}


class TestSanitizeInlineText:
    def test_newlines_removed(self):
        assert sanitize_inline_text("a\nb\rc") == "a b c"

    def test_stripped(self):
        assert sanitize_inline_text("  hello  ") == "hello"

    def test_none_handled(self):
        assert sanitize_inline_text("") == ""

    def test_empty_string(self):
        assert sanitize_inline_text("") == ""


class TestSanitizeDocstringText:
    def test_triple_quotes_escaped(self):
        result = sanitize_docstring_text('has """ inside')
        assert '"""' not in result
        assert '\\"\\"\\"' in result

    def test_newlines_removed(self):
        result = sanitize_docstring_text("line1\nline2")
        assert "\n" not in result

    def test_none_handled(self):
        assert sanitize_docstring_text("") == ""


class TestSafeDomain:
    def test_normal_domain(self):
        assert _safe_domain("github.com") == "github.com"

    def test_slashes_replaced(self):
        assert _safe_domain("a/b/c") == "a_b_c"

    def test_colons_replaced(self):
        assert _safe_domain("host:8080") == "host_8080"

    def test_empty_returns_unknown(self):
        assert _safe_domain("") == "unknown-domain"

    def test_none_returns_unknown(self):
        assert _safe_domain("") == "unknown-domain"

    def test_whitespace_only_returns_unknown(self):
        assert _safe_domain("   ") == "unknown-domain"


class TestExtractHeaderValue:
    def test_found(self):
        code = "# 来源 URL: https://example.com\n# 工作流: test\n"
        assert _extract_header_value(code, "# 来源 URL:") == "https://example.com"

    def test_not_found(self):
        assert _extract_header_value("import click\n", "# 来源 URL:") == ""

    def test_empty_value(self):
        assert _extract_header_value("# 来源 URL:\n", "# 来源 URL:") == ""

    def test_strips_whitespace(self):
        code = "# 工作流:   hello world  \n"
        assert _extract_header_value(code, "# 工作流:") == "hello world"


class TestExtractCommandsFromCode:
    def test_double_quoted(self):
        code = '@cli.command("search")\ndef search(): pass\n'
        assert _extract_commands_from_code(code) == ["search"]

    def test_single_quoted(self):
        code = "@cli.command('login')\ndef login(): pass\n"
        assert _extract_commands_from_code(code) == ["login"]

    def test_multiple_commands(self):
        code = '@cli.command("search")\ndef search(): pass\n@cli.command("login")\ndef login(): pass\n'
        assert _extract_commands_from_code(code) == ["search", "login"]

    def test_no_commands(self):
        assert _extract_commands_from_code("import click\n") == []


class TestRenderClickType:
    def test_choices_list(self):
        result = render_click_type(None, ["a", "b", "c"])
        assert result is not None
        assert "click.Choice" in result
        assert "'a'" in result

    def test_int_type(self):
        assert render_click_type("int", None) == "int"
        assert render_click_type("integer", None) == "int"

    def test_float_type(self):
        assert render_click_type("float", None) == "float"
        assert render_click_type("number", None) == "float"

    def test_path_type(self):
        result = render_click_type("path", None)
        assert result is not None
        assert "click.Path" in result

    def test_string_type_returns_none(self):
        assert render_click_type("str", None) is None
        assert render_click_type("string", None) is None
        assert render_click_type("", None) is None

    def test_unknown_type_returns_none(self):
        assert render_click_type("unknown", None) is None


class TestActionDetail:
    def _make_action(self, **kwargs):
        from cliany_site.explorer.models import ActionStep

        defaults = {
            "action_type": "",
            "page_url": "",
            "target_ref": "",
            "target_url": "",
            "value": "",
            "description": "",
            "target_name": "",
            "target_role": "",
            "target_attributes": {},
            "selector": "",
            "extract_mode": "text",
            "fields_map": {},
        }
        defaults.update(kwargs)
        return ActionStep(**defaults)

    def test_navigate(self):
        action = self._make_action(action_type="navigate", target_url="https://example.com")
        assert action_detail(action) == "https://example.com"

    def test_click(self):
        action = self._make_action(action_type="click", target_ref="@ref42")
        assert action_detail(action) == "@ref42"

    def test_type(self):
        action = self._make_action(action_type="type", target_ref="@ref1", value="hello")
        result = action_detail(action)
        assert "@ref1" in result
        assert "hello" in result
        assert "<-" in result

    def test_select(self):
        action = self._make_action(action_type="select", target_ref="@ref2", value="option1")
        result = action_detail(action)
        assert "=>" in result

    def test_submit(self):
        action = self._make_action(action_type="submit")
        assert "提交" in action_detail(action)

    def test_unknown_with_ref(self):
        action = self._make_action(action_type="custom", target_ref="@ref5")
        assert action_detail(action) == "@ref5"

    def test_unknown_no_ref(self):
        action = self._make_action(action_type="custom")
        assert action_detail(action) == "执行操作"


class TestRenderArgsPayload:
    def test_empty(self):
        assert render_args_payload([]) == "{}"

    def test_single(self):
        result = render_args_payload(["query"])
        assert result == "{'query': query}"

    def test_multiple(self):
        result = render_args_payload(["query", "limit"])
        assert "'query': query" in result
        assert "'limit': limit" in result


class TestBackwardCompatDelegates:
    def test_adapter_generator_delegates_naming(self):
        gen = AdapterGenerator()
        assert gen._to_command_name("hello-world", 0) == "hello-world"
        assert gen._to_function_name("hello-world") == "hello_world"
        assert gen._to_parameter_name("my-param") == "my_param"
        assert gen._unique_parameter_name("x", {"x"}) == "x_2"
        assert gen._sanitize_inline_text("a\nb") == "a b"


class TestRenderCommandBlock:
    def _make_command(self):
        from cliany_site.explorer.models import CommandSuggestion

        return CommandSuggestion(
            name="search",
            description="搜索仓库",
            args=[],
            action_steps=[0, 1],
        )

    def _make_actions(self):
        from cliany_site.explorer.models import ActionStep

        return [
            ActionStep(action_type="navigate", page_url="https://github.com", target_url="https://github.com/search"),
            ActionStep(action_type="click", page_url="https://github.com/search", target_ref="@ref1"),
        ]

    def test_generated_command_includes_resume_option(self):
        code = render_command_block(self._make_command(), self._make_actions(), 0)
        assert '@click.option("--resume", is_flag=True, default=False, help="从最近断点继续执行")' in code

    def test_generated_command_loads_checkpoint_when_resume(self):
        code = render_command_block(self._make_command(), self._make_actions(), 0)
        assert "from cliany_site.checkpoint import load_checkpoint" in code
        assert "checkpoint = load_checkpoint(DOMAIN, 'search')" in code
        assert (
            'return error_response(EXECUTION_FAILED, "未找到可恢复断点", "请先执行一次失败流程后再使用 --resume")'
            in code
        )

    def test_generated_command_builds_single_action_steps_list_for_resume(self):
        code = render_command_block(self._make_command(), self._make_actions(), 0)
        assert "action_steps = []" in code
        assert "action_steps.extend(" in code
        assert "start_index=start_index" in code

    def test_generated_command_reads_root_sandbox_flag(self):
        code = render_command_block(self._make_command(), self._make_actions(), 0)
        assert "root_ctx = ctx.find_root()" in code
        assert 'sandbox_enabled = root_obj.get("sandbox", False)' in code

    def test_generated_command_validates_actions_when_sandbox_enabled(self):
        code = render_command_block(self._make_command(), self._make_actions(), 0)
        assert "from cliany_site.sandbox import SandboxPolicy, validate_action_steps" in code
        assert "policy = SandboxPolicy.from_domain(DOMAIN)" in code
        assert "violations = validate_action_steps(action_steps, policy)" in code

    def test_generated_command_returns_sandbox_error_message(self):
        code = render_command_block(self._make_command(), self._make_actions(), 0)
        assert "沙箱阻止执行" in code
