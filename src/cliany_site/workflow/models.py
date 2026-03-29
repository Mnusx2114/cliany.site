from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1
    delay: float = 1.0
    backoff: float = 1.0


@dataclass(frozen=True)
class StepDef:
    name: str
    adapter: str
    command: str
    params: dict[str, str] = field(default_factory=dict)
    when: str = ""
    retry: RetryPolicy = field(default_factory=RetryPolicy)


@dataclass(frozen=True)
class WorkflowDef:
    name: str
    steps: list[StepDef] = field(default_factory=list)
    description: str = ""
