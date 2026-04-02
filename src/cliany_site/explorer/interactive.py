from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from enum import Enum

import click
from rich.console import Console
from rich.panel import Panel


class DecisionType(Enum):
    CONFIRM = "confirm"
    SKIP = "skip"
    MODIFY = "modify"
    ROLLBACK = "rollback"


@dataclass
class InteractiveDecision:
    decision_type: DecisionType
    field: str | None = None
    new_value: str | None = None


class InteractiveController:
    ALLOWED_MODIFY_FIELDS = {"value", "ref"}

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def _check_tty(self):
        if not sys.stdin.isatty():
            raise click.UsageError("--interactive 需要 TTY 终端，无法在管道/非交互环境运行")

    def _get_input(self, prompt: str) -> str:
        return input(prompt).strip()

    async def _async_input(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        return (await loop.run_in_executor(None, input, prompt)).strip()

    async def prompt_action_confirmation(
        self,
        actions: list,
        page_summary: str = "",
    ) -> InteractiveDecision:
        self._check_tty()

        self.console.print(
            Panel(
                f"页面: {page_summary}\n提议动作数量: {len(actions)}",
                title="交互确认",
                border_style="blue",
            )
        )

        while True:
            choice = await self._async_input("操作 [1/y=确认, 2/s=跳过, 3/m=修改, 4/b=回退]: ")

            if choice.lower() in ("1", "y", "confirm", "yes", "确认"):
                return InteractiveDecision(decision_type=DecisionType.CONFIRM)

            elif choice.lower() in ("2", "s", "skip", "跳过"):
                return InteractiveDecision(decision_type=DecisionType.SKIP)

            elif choice.lower() in ("3", "m", "modify", "修改"):
                return await self._handle_modify()

            elif choice.lower() in ("4", "b", "rollback", "回退"):
                return InteractiveDecision(decision_type=DecisionType.ROLLBACK)

            else:
                self.console.print(f"[red]无效输入 '{choice}'，请重新输入[/red]")

    async def _handle_modify(self) -> InteractiveDecision:
        while True:
            field = await self._async_input(f"要修改的字段 ({'/'.join(sorted(self.ALLOWED_MODIFY_FIELDS))}): ")
            if field in self.ALLOWED_MODIFY_FIELDS:
                break
            self.console.print(f"[red]只能修改: {self.ALLOWED_MODIFY_FIELDS}[/red]")

        new_value = await self._async_input(f"新的 {field} 值: ")
        return InteractiveDecision(
            decision_type=DecisionType.MODIFY,
            field=field,
            new_value=new_value,
        )
