import datetime
from pathlib import Path

from cliany_site.config import get_config


def _log_file() -> Path:
    return get_config().activity_log_path


def write_log(
    action: str,
    domain: str = "",
    command: str = "",
    status: str = "",
    details: str = "",
) -> None:
    """Append one log line: {timestamp} | {action} | {domain} | {command} | {status} | {details}"""
    try:
        log_path = _log_file()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        line = f"[{timestamp}] {action.upper()} | {domain} | {command} | {status} | {details}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


def read_recent_logs(limit: int = 50) -> list[str]:
    """Read last N lines from the log file"""
    log_path = _log_file()
    if not log_path.exists():
        return []
    try:
        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        return lines[-limit:]
    except OSError:
        return ["读取日志失败"]
