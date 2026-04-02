# pyright: reportMissingImports=false

"""TDD 测试 — InteractiveController 用户确认循环骨架

测试清单（8+ 个）：
1. test_non_tty_raises_error         — 非 TTY 抛出 UsageError
2. test_confirm_returns_confirm      — 输入 "y" 返回 CONFIRM
3. test_skip_returns_skip            — 输入 "s" 返回 SKIP
4. test_rollback_returns_rollback    — 输入 "b" 返回 ROLLBACK
5. test_modify_returns_modify        — 输入 "m" + field + value 返回 MODIFY
6. test_modify_only_allows_value_or_ref — 非法字段要求重新输入
7. test_invalid_input_reprompts      — 无效输入后重新提示
8. test_async_prompt_returns_decision — async 接口测试
9. test_confirm_aliases              — 多种确认别名（"1"/"confirm"/"yes"/中文）
10. test_skip_aliases                — 多种跳过别名（"2"/"skip"）
11. test_rollback_aliases            — 多种回退别名（"4"/"rollback"）
"""

import sys
from types import SimpleNamespace

import click
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cliany_site.explorer.models import ActionStep, ExploreResult, PageInfo, TurnSnapshot
from cliany_site.explorer.interactive import (
    DecisionType,
    InteractiveController,
    InteractiveDecision,
)


# ─── 辅助工具 ────────────────────────────────────────────────


def make_controller():
    """创建一个使用 MagicMock Console 的 Controller"""
    return InteractiveController(console=MagicMock())


# ─── 1. 非 TTY 检测 ─────────────────────────────────────────


def test_non_tty_raises_error(monkeypatch):
    """非 TTY 环境应抛出 click.UsageError"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    controller = make_controller()

    with pytest.raises(click.UsageError):
        controller._check_tty()


def test_tty_does_not_raise(monkeypatch):
    """TTY 环境不应抛出异常"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    controller = make_controller()
    # 不应抛出
    controller._check_tty()


# ─── 2. 确认 ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_confirm_returns_confirm(monkeypatch):
    """输入 'y' 返回 DecisionType.CONFIRM"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    controller = make_controller()
    controller._async_input = AsyncMock(return_value="y")

    result = await controller.prompt_action_confirmation([], "test page")

    assert result.decision_type == DecisionType.CONFIRM
    assert result.field is None
    assert result.new_value is None


# ─── 3. 跳过 ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_skip_returns_skip(monkeypatch):
    """输入 's' 返回 DecisionType.SKIP"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    controller = make_controller()
    controller._async_input = AsyncMock(return_value="s")

    result = await controller.prompt_action_confirmation([], "test page")

    assert result.decision_type == DecisionType.SKIP


# ─── 4. 回退 ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rollback_returns_rollback(monkeypatch):
    """输入 'b' 返回 DecisionType.ROLLBACK"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    controller = make_controller()
    controller._async_input = AsyncMock(return_value="b")

    result = await controller.prompt_action_confirmation([], "test page")

    assert result.decision_type == DecisionType.ROLLBACK


# ─── 5. 修改 — 正常流程 ─────────────────────────────────────


@pytest.mark.asyncio
async def test_modify_returns_modify_with_field_value(monkeypatch):
    """输入 'm' + 字段名 'value' + 新值 'new_val' → MODIFY decision"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    controller = make_controller()
    # 模拟: 主提示 -> "m", 字段提示 -> "value", 新值提示 -> "new_val"
    controller._async_input = AsyncMock(side_effect=["m", "value", "new_val"])

    result = await controller.prompt_action_confirmation([], "test page")

    assert result.decision_type == DecisionType.MODIFY
    assert result.field == "value"
    assert result.new_value == "new_val"


@pytest.mark.asyncio
async def test_modify_ref_field(monkeypatch):
    """修改 'ref' 字段也应正常工作"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    controller = make_controller()
    controller._async_input = AsyncMock(side_effect=["m", "ref", "new_ref_value"])

    result = await controller.prompt_action_confirmation([], "test page")

    assert result.decision_type == DecisionType.MODIFY
    assert result.field == "ref"
    assert result.new_value == "new_ref_value"


# ─── 6. 修改 — 非法字段重新输入 ─────────────────────────────


@pytest.mark.asyncio
async def test_modify_only_allows_value_or_ref(monkeypatch):
    """字段名输入 'description' 时要求重新输入，再输入 'value' 才通过"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    controller = make_controller()
    # 主提示 -> "m"
    # 字段提示 -> "description" (非法), 再 -> "value" (合法)
    # 新值提示 -> "hello"
    controller._async_input = AsyncMock(side_effect=["m", "description", "value", "hello"])

    result = await controller.prompt_action_confirmation([], "test page")

    assert result.decision_type == DecisionType.MODIFY
    assert result.field == "value"
    assert result.new_value == "hello"


# ─── 7. 无效输入重新提示 ─────────────────────────────────────


@pytest.mark.asyncio
async def test_invalid_input_reprompts(monkeypatch):
    """输入 'xyz' 后应重新提示，再输入 'y' 才返回 CONFIRM"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    controller = make_controller()
    controller._async_input = AsyncMock(side_effect=["xyz", "y"])

    result = await controller.prompt_action_confirmation([], "test page")

    assert result.decision_type == DecisionType.CONFIRM
    # 应该调用了两次 _async_input
    assert controller._async_input.call_count == 2


# ─── 8. async 接口测试 ───────────────────────────────────────


@pytest.mark.asyncio
async def test_async_prompt_returns_decision(monkeypatch):
    """async prompt_action_confirmation 返回正确的 InteractiveDecision 实例"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    controller = make_controller()
    controller._async_input = AsyncMock(return_value="1")

    result = await controller.prompt_action_confirmation(["action1", "action2"], "some page")

    assert isinstance(result, InteractiveDecision)
    assert result.decision_type == DecisionType.CONFIRM


# ─── 9. 确认别名测试 ─────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("alias", ["1", "confirm", "yes", "确认"])
async def test_confirm_aliases(alias, monkeypatch):
    """多种确认别名均应返回 CONFIRM"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    controller = make_controller()
    controller._async_input = AsyncMock(return_value=alias)

    result = await controller.prompt_action_confirmation([], "page")

    assert result.decision_type == DecisionType.CONFIRM


# ─── 10. 跳过别名测试 ────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("alias", ["2", "skip", "跳过"])
async def test_skip_aliases(alias, monkeypatch):
    """多种跳过别名均应返回 SKIP"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    controller = make_controller()
    controller._async_input = AsyncMock(return_value=alias)

    result = await controller.prompt_action_confirmation([], "page")

    assert result.decision_type == DecisionType.SKIP


# ─── 11. 回退别名测试 ────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("alias", ["4", "rollback", "回退"])
async def test_rollback_aliases(alias, monkeypatch):
    """多种回退别名均应返回 ROLLBACK"""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    controller = make_controller()
    controller._async_input = AsyncMock(return_value=alias)

    result = await controller.prompt_action_confirmation([], "page")

    assert result.decision_type == DecisionType.ROLLBACK


def _make_browser_session_for_rollback() -> tuple[MagicMock, MagicMock]:
    page_api = MagicMock()
    page_api.getNavigationHistory = AsyncMock(
        return_value={
            "currentIndex": 1,
            "entries": [
                {"id": 101, "url": "https://example.com/prev"},
                {"id": 202, "url": "https://example.com/current"},
            ],
        }
    )
    page_api.navigateToHistoryEntry = AsyncMock()
    page_api.navigate = AsyncMock()

    browser_session = MagicMock()
    browser_session.get_or_create_cdp_session = AsyncMock(return_value=SimpleNamespace(session_id="sid-1"))
    browser_session.cdp_client = SimpleNamespace(send=SimpleNamespace(Page=page_api))
    browser_session.navigate_to = AsyncMock()
    return browser_session, page_api


@pytest.mark.asyncio
async def test_rollback_restores_actions():
    controller = make_controller()
    browser_session, page_api = _make_browser_session_for_rollback()
    result = ExploreResult(
        actions=[
            ActionStep(action_type="click", page_url="https://example.com", description="step-1"),
            ActionStep(action_type="type", page_url="https://example.com", description="step-2"),
            ActionStep(action_type="click", page_url="https://example.com", description="step-3"),
        ],
        pages=[PageInfo(url="https://example.com", title="Example")],
    )
    snapshot = TurnSnapshot(turn_index=2, actions_before_count=2, pages_before_count=1, browser_history_index=2)

    with patch("cliany_site.explorer.interactive.capture_axtree", new_callable=AsyncMock) as capture_mock:
        ok = await controller.handle_rollback(snapshot, result, browser_session)

    assert ok is True
    assert len(result.actions) == 2
    assert [a.description for a in result.actions] == ["step-1", "step-2"]
    page_api.getNavigationHistory.assert_awaited_once()
    page_api.navigateToHistoryEntry.assert_awaited_once_with({"entryId": 101}, session_id="sid-1")
    capture_mock.assert_awaited_once_with(browser_session)


@pytest.mark.asyncio
async def test_rollback_first_step_returns_false():
    controller = make_controller()
    browser_session, page_api = _make_browser_session_for_rollback()
    result = ExploreResult()
    snapshot = TurnSnapshot(turn_index=0, actions_before_count=0, pages_before_count=0, browser_history_index=0)

    with patch("cliany_site.explorer.interactive.capture_axtree", new_callable=AsyncMock) as capture_mock:
        ok = await controller.handle_rollback(snapshot, result, browser_session)

    assert ok is False
    controller.console.print.assert_called_once()
    page_api.getNavigationHistory.assert_not_called()
    capture_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_rollback_restores_pages():
    controller = make_controller()
    browser_session, _ = _make_browser_session_for_rollback()
    result = ExploreResult(
        pages=[
            PageInfo(url="https://example.com/p1", title="P1"),
            PageInfo(url="https://example.com/p2", title="P2"),
            PageInfo(url="https://example.com/p3", title="P3"),
        ]
    )
    snapshot = TurnSnapshot(turn_index=2, actions_before_count=1, pages_before_count=2, browser_history_index=2)

    with patch("cliany_site.explorer.interactive.capture_axtree", new_callable=AsyncMock):
        ok = await controller.handle_rollback(snapshot, result, browser_session)

    assert ok is True
    assert len(result.pages) == 2
    assert [p.url for p in result.pages] == ["https://example.com/p1", "https://example.com/p2"]


@pytest.mark.asyncio
async def test_rollback_calls_recording_manager_mark_rolled_back():
    controller = make_controller()
    browser_session, _ = _make_browser_session_for_rollback()
    result = ExploreResult(
        actions=[ActionStep(action_type="click", page_url="https://example.com", description="step-1")],
        pages=[PageInfo(url="https://example.com", title="Example")],
    )
    snapshot = TurnSnapshot(turn_index=7, actions_before_count=1, pages_before_count=1, browser_history_index=7)

    recording_manager = MagicMock()
    manifest = MagicMock()

    with patch("cliany_site.explorer.interactive.capture_axtree", new_callable=AsyncMock):
        ok = await controller.handle_rollback(
            snapshot,
            result,
            browser_session,
            recording_manager=recording_manager,
            recording_manifest=manifest,
        )

    assert ok is True
    recording_manager.mark_rolled_back.assert_called_once_with(manifest, 7)
