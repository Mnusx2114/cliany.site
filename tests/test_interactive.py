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

import click
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

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
