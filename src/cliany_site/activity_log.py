import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".cliany-site" / "activity.log"


def write_log(
    action: str,
    domain: str = "",
    command: str = "",
    status: str = "",
    details: str = "",
) -> None:
    """Append one log line: {timestamp} | {action} | {domain} | {command} | {status} | {details}"""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        line = f"[{timestamp}] {action.upper()} | {domain} | {command} | {status} | {details}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # Silently fail if logging fails, to not interrupt the main workflow
        pass


def read_recent_logs(limit: int = 50) -> list[str]:
    """Read last N lines from the log file"""
    if not LOG_FILE.exists():
        return []
    try:
        lines = LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
        return lines[-limit:]
    except Exception:
        return ["读取日志失败"]
