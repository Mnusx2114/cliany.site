import json
import logging
from dataclasses import dataclass
from datetime import datetime

from cliany_site.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class ActionStepResult:
    """单个动作步骤的执行结果"""

    step_index: int
    action_type: str
    description: str
    success: bool
    error_message: str | None = None
    timestamp: str | None = None
    page_url: str = ""
    elapsed_ms: float = 0.0


@dataclass
class ExecutionReport:
    """执行报告数据模型"""

    adapter_domain: str
    command_name: str
    started_at: str
    finished_at: str
    total_steps: int
    succeeded_steps: int
    failed_steps: int
    repaired_steps: int
    step_results: list[ActionStepResult]

    @property
    def status(self) -> str:
        """计算执行状态"""
        if self.failed_steps == 0:
            return "success"
        elif self.succeeded_steps + self.repaired_steps > 0:
            return "partial_success"
        else:
            return "failure"


def save_report(report: ExecutionReport, domain: str) -> str:
    """保存执行报告到文件，返回文件路径"""
    reports_dir = get_config().reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)
    # 将 domain 中的非法文件名字符替换为 _
    safe_domain = domain.replace("/", "_").replace(":", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_domain}_{timestamp}.json"
    path = reports_dir / filename

    data = {
        "adapter_domain": report.adapter_domain,
        "command_name": report.command_name,
        "started_at": report.started_at,
        "finished_at": report.finished_at,
        "total_steps": report.total_steps,
        "succeeded_steps": report.succeeded_steps,
        "failed_steps": report.failed_steps,
        "repaired_steps": report.repaired_steps,
        "status": report.status,
        "step_results": [
            {
                "step_index": step.step_index,
                "action_type": step.action_type,
                "description": step.description,
                "success": step.success,
                "error_message": step.error_message,
                "timestamp": step.timestamp,
                "page_url": step.page_url,
                "elapsed_ms": step.elapsed_ms,
            }
            for step in report.step_results
        ],
    }

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def list_reports(domain: str | None) -> list[dict]:
    """列出指定域名的执行报告，不指定域名则列出所有"""
    reports_dir = get_config().reports_dir
    if not reports_dir.exists():
        return []

    reports = []
    for path in reports_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if domain is None or data.get("adapter_domain") == domain:
                reports.append(
                    {
                        "domain": data.get("adapter_domain"),
                        "command": data.get("command_name"),
                        "started_at": data.get("started_at"),
                        "finished_at": data.get("finished_at"),
                        "status": data.get("status"),
                        "total_steps": data.get("total_steps"),
                        "succeeded_steps": data.get("succeeded_steps"),
                        "failed_steps": data.get("failed_steps"),
                        "repaired_steps": data.get("repaired_steps"),
                        "path": str(path),
                    }
                )
        except (json.JSONDecodeError, OSError, KeyError):
            continue

    # 按开始时间倒序排列
    reports.sort(key=lambda x: x["started_at"], reverse=True)
    return reports


def save_execution_log(report: ExecutionReport, domain: str) -> str:
    """保存详细执行日志到 ~/.cliany-site/logs/，返回文件路径"""
    logs_dir = get_config().logs_dir
    logs_dir.mkdir(parents=True, exist_ok=True)

    safe_domain = domain.replace("/", "_").replace(":", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_domain}_{timestamp}.log.json"
    path = logs_dir / filename

    log_entries = []
    for step in report.step_results:
        entry: dict[str, object] = {
            "step_index": step.step_index,
            "action_type": step.action_type,
            "description": step.description,
            "success": step.success,
            "timestamp": step.timestamp,
            "page_url": step.page_url,
            "elapsed_ms": round(step.elapsed_ms, 2),
        }
        if step.error_message:
            entry["error"] = step.error_message
        log_entries.append(entry)

    data = {
        "adapter_domain": report.adapter_domain,
        "command_name": report.command_name,
        "started_at": report.started_at,
        "finished_at": report.finished_at,
        "status": report.status,
        "summary": {
            "total": report.total_steps,
            "succeeded": report.succeeded_steps,
            "failed": report.failed_steps,
            "repaired": report.repaired_steps,
        },
        "steps": log_entries,
    }

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.debug("执行日志已保存: %s", path)
    return str(path)
