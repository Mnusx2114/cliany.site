from cliany_site.explorer.models import (
    ActionStep,
    CommandSuggestion,
    ExploreResult,
    PageInfo,
)
from cliany_site.explorer.prompts import EXPLORE_PROMPT_TEMPLATE, SYSTEM_PROMPT

__all__ = [
    "WorkflowExplorer",
    "ExploreResult",
    "PageInfo",
    "ActionStep",
    "CommandSuggestion",
    "SYSTEM_PROMPT",
    "EXPLORE_PROMPT_TEMPLATE",
]


def __getattr__(name: str):
    if name == "WorkflowExplorer":
        from cliany_site.explorer.engine import WorkflowExplorer

        return WorkflowExplorer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
