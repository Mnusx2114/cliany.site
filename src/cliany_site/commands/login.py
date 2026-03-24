import asyncio
from urllib.parse import urlparse

import click

from cliany_site.response import success_response, error_response, print_response
from cliany_site.errors import CDP_UNAVAILABLE


@click.command("login")
@click.argument("url")
@click.option("--json", "json_mode", is_flag=True, default=None, help="JSON 输出模式")
@click.pass_context
def login(ctx: click.Context, url: str, json_mode: bool | None):
    """捕获浏览器 Session 并持久化到本地文件

    URL: 目标网站地址（如 https://github.com）

    使用前请先在 Chrome 中手动登录目标网站。
    """
    root_ctx = ctx.find_root()
    root_obj = root_ctx.obj if isinstance(root_ctx.obj, dict) else {}
    effective_json_mode = (
        json_mode if json_mode is not None else bool(root_obj.get("json_mode", False))
    )

    result = asyncio.run(_capture_session(url))
    print_response(result, json_mode=effective_json_mode)


async def _capture_session(url: str) -> dict:
    from cliany_site.browser.cdp import CDPConnection
    from cliany_site.session import save_session

    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    if not domain:
        return error_response("INVALID_URL", f"无法从 URL 提取 domain: {url}")

    cdp = CDPConnection()
    available = await cdp.check_available()
    if not available:
        return error_response(
            CDP_UNAVAILABLE,
            "Chrome 未通过 CDP 运行",
            fix="请使用 --remote-debugging-port=9222 启动 Chrome",
        )

    try:
        browser_session = await cdp.connect()
    except Exception as e:
        return error_response(CDP_UNAVAILABLE, f"连接 Chrome 失败: {e}")

    try:
        try:
            page = await browser_session.get_current_page()
            if page is not None:
                await page.goto(url)
        except Exception:
            pass

        click.echo("提示：请确认已在 Chrome 中登录目标网站，然后继续...", err=True)

        path = await save_session(domain, browser_session)

        return success_response(
            {
                "domain": domain,
                "session_file": path,
                "message": f"Session 已保存到 {path}",
            }
        )
    except Exception as e:
        return error_response("EXECUTION_FAILED", f"Session 捕获失败: {e}")
    finally:
        await cdp.disconnect()
