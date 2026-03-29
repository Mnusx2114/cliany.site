# src/cliany_site/commands/doctor.py
import asyncio
import os
from typing import Any

import click

from cliany_site.config import get_config
from cliany_site.response import error_response, print_response, success_response

try:
    from cliany_site.explorer.engine import _load_dotenv

    _load_dotenv()
except ImportError:
    pass


@click.command("doctor")
@click.option("--json", "json_mode", is_flag=True, default=None, help="JSON 输出模式")
@click.pass_context
def doctor(ctx: click.Context, json_mode: bool | None):
    """检查运行环境（CDP / LLM API key / 目录）"""
    root_ctx = ctx.find_root()
    root_obj = root_ctx.obj if isinstance(root_ctx.obj, dict) else {}
    effective_json_mode = json_mode if json_mode is not None else bool(root_obj.get("json_mode", False))

    from cliany_site.browser.cdp import cdp_from_context

    cdp_conn = cdp_from_context(ctx)
    result = asyncio.run(_run_checks(cdp_conn))
    print_response(result, json_mode=effective_json_mode, exit_on_error=True)


async def _run_checks(cdp_conn: Any = None) -> dict:
    from cliany_site.browser.cdp import CDPConnection
    from cliany_site.explorer.engine import _load_dotenv, _normalize_openai_base_url

    _load_dotenv()

    checks: dict[str, Any] = {}

    try:
        cdp = cdp_conn if cdp_conn is not None else CDPConnection()
        checks["cdp"] = "ok" if await cdp.check_available() else "fail"

        from cliany_site.browser.launcher import find_chrome_binary

        chrome_binary = find_chrome_binary()
        checks["chrome_binary_path"] = str(chrome_binary) if chrome_binary else None
        checks["chrome_auto_launched"] = getattr(cdp, "_chrome_auto_launched", False)
        checks["cdp_remote"] = getattr(cdp, "is_remote", False)
    except (OSError, RuntimeError, TimeoutError):
        checks["cdp"] = "fail"

    # 支持新旧环境变量名
    has_llm = bool(
        os.environ.get("CLIANY_ANTHROPIC_API_KEY")
        or os.environ.get("CLIANY_OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )
    checks["llm"] = "ok" if has_llm else "fail"

    provider = os.environ.get("CLIANY_LLM_PROVIDER", "anthropic").lower()
    checks["llm_provider"] = "ok" if provider in {"anthropic", "openai"} else "fail"

    if provider == "openai":
        base_url = os.environ.get("CLIANY_OPENAI_BASE_URL")
        try:
            normalized_base_url = _normalize_openai_base_url(base_url)
            checks["openai_base_url"] = "ok" if (normalized_base_url or not base_url) else "fail"
        except (ValueError, TypeError):
            checks["openai_base_url"] = "fail"

    cfg = get_config()
    adapters_dir = cfg.adapters_dir
    checks["adapters_dir"] = "ok" if adapters_dir.exists() else "fail"

    sessions_dir = cfg.sessions_dir
    checks["sessions_dir"] = "ok" if sessions_dir.exists() else "fail"

    if adapters_dir.exists():
        adapters = [d for d in adapters_dir.iterdir() if d.is_dir()]
        checks["adapters_count"] = len(adapters)
    else:
        checks["adapters_count"] = 0

    checks["config"] = cfg.to_dict()

    failed = [k for k, v in checks.items() if v == "fail"]
    if failed:
        return error_response(
            "DOCTOR_ISSUES",
            f"以下检查项失败: {', '.join(failed)}",
            fix=f"请检查 Chrome CDP 端口（--remote-debugging-port={cfg.cdp_port}）和 LLM API key",
        ) | {"data": checks}

    return success_response(checks)
