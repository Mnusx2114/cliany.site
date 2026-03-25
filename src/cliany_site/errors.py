CDP_UNAVAILABLE = "CDP_UNAVAILABLE"
SESSION_EXPIRED = "SESSION_EXPIRED"
EXPLORE_FAILED = "EXPLORE_FAILED"
ADAPTER_NOT_FOUND = "ADAPTER_NOT_FOUND"
COMMAND_NOT_FOUND = "COMMAND_NOT_FOUND"
LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
EXECUTION_FAILED = "EXECUTION_FAILED"
CHROME_NOT_FOUND = "CHROME_NOT_FOUND"

ERROR_FIX_HINTS: dict[str, str] = {
    CDP_UNAVAILABLE: "请先启动 Chrome：google-chrome --remote-debugging-port=9222",
    SESSION_EXPIRED: "请重新运行 cliany-site login <url> 登录",
    EXPLORE_FAILED: "请检查 LLM API key 和 Chrome CDP 连接",
    ADAPTER_NOT_FOUND: "请先运行 cliany-site explore <url> <workflow> 生成 adapter",
    COMMAND_NOT_FOUND: "请运行 cliany-site list 查看可用命令",
    LLM_UNAVAILABLE: "请设置 CLIANY_LLM_PROVIDER、CLIANY_ANTHROPIC_API_KEY 或 CLIANY_OPENAI_API_KEY 环境变量",
    EXECUTION_FAILED: "请检查 Chrome CDP 连接和 adapter 状态",
    CHROME_NOT_FOUND: "请安装 Chrome 或确认 Chrome 可执行文件在 PATH 中",
}
