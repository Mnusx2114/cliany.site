# src/cliany_site/commands/doctor.py
import asyncio
import os
from pathlib import Path
import click
from cliany_site.response import success_response, error_response, print_response


@click.command("doctor")
@click.option("--json", "json_mode", is_flag=True, default=False, help="JSON 输出模式")
def doctor(json_mode: bool):
    """检查运行环境（CDP / LLM API key / 目录）"""
    result = asyncio.run(_run_checks())
    print_response(result, json_mode=json_mode)


async def _run_checks() -> dict:
    checks = {}

    # 1. CDP 连接检查
    try:
        from cliany_site.browser.cdp import CDPConnection

        cdp = CDPConnection()
        checks["cdp"] = "ok" if await cdp.check_available() else "fail"
    except Exception:
        checks["cdp"] = "fail"

    # 2. LLM API Key 检查
    has_llm = bool(
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
    )
    checks["llm"] = "ok" if has_llm else "fail"

    # 3. Adapters 目录
    adapters_dir = Path.home() / ".cliany-site" / "adapters"
    checks["adapters_dir"] = "ok" if adapters_dir.exists() else "fail"

    # 4. Sessions 目录
    sessions_dir = Path.home() / ".cliany-site" / "sessions"
    checks["sessions_dir"] = "ok" if sessions_dir.exists() else "fail"

    # 5. 已安装 Adapter 数量
    if adapters_dir.exists():
        adapters = [d for d in adapters_dir.iterdir() if d.is_dir()]
        checks["adapters_count"] = len(adapters)
    else:
        checks["adapters_count"] = 0

    # 判断整体状态
    failed = [k for k, v in checks.items() if v == "fail"]
    if failed:
        return error_response(
            "DOCTOR_ISSUES",
            f"以下检查项失败: {', '.join(failed)}",
            fix="请检查 Chrome CDP 端口（--remote-debugging-port=9222）和 LLM API key",
        ) | {"data": checks}

    return success_response(checks)
