"""生成代码审计 — AST 静态分析检测危险模式"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

_DANGEROUS_CALLS = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "execfile",
        "__import__",
    }
)

_DANGEROUS_ATTR_CALLS = frozenset(
    {
        "os.system",
        "os.popen",
        "os.exec",
        "os.execl",
        "os.execle",
        "os.execlp",
        "os.execv",
        "os.execve",
        "os.execvp",
        "os.execvpe",
        "os.spawn",
        "os.spawnl",
        "os.spawnle",
        "subprocess.call",
        "subprocess.run",
        "subprocess.Popen",
        "subprocess.check_call",
        "subprocess.check_output",
        "shutil.rmtree",
    }
)

_DANGEROUS_IMPORTS = frozenset(
    {
        "ctypes",
        "pickle",
        "shelve",
        "marshal",
    }
)


@dataclass(frozen=True)
class AuditFinding:
    severity: Literal["critical", "warning", "info"]
    category: str
    message: str
    line: int
    col: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "line": self.line,
            "col": self.col,
        }


class _DangerousPatternVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.findings: list[AuditFinding] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if isinstance(node.func, ast.Name) and node.func.id in _DANGEROUS_CALLS:
            self.findings.append(
                AuditFinding(
                    severity="critical",
                    category="dangerous_call",
                    message=f"检测到危险调用: {node.func.id}()",
                    line=node.lineno,
                    col=node.col_offset,
                )
            )

        if isinstance(node.func, ast.Attribute):
            full_name = _resolve_attr_name(node.func)
            if full_name:
                for pattern in _DANGEROUS_ATTR_CALLS:
                    if full_name == pattern or full_name.endswith(f".{pattern}"):
                        self.findings.append(
                            AuditFinding(
                                severity="critical",
                                category="dangerous_call",
                                message=f"检测到危险调用: {full_name}()",
                                line=node.lineno,
                                col=node.col_offset,
                            )
                        )
                        break

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            if alias.name in _DANGEROUS_IMPORTS:
                self.findings.append(
                    AuditFinding(
                        severity="warning",
                        category="dangerous_import",
                        message=f"检测到高风险模块导入: {alias.name}",
                        line=node.lineno,
                        col=node.col_offset,
                    )
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module and node.module.split(".")[0] in _DANGEROUS_IMPORTS:
            self.findings.append(
                AuditFinding(
                    severity="warning",
                    category="dangerous_import",
                    message=f"检测到高风险模块导入: {node.module}",
                    line=node.lineno,
                    col=node.col_offset,
                )
            )
        self.generic_visit(node)


def _resolve_attr_name(node: ast.Attribute) -> str | None:
    parts: list[str] = [node.attr]
    current: ast.expr = node.value
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def audit_source(source: str, filename: str = "<generated>") -> list[AuditFinding]:
    """对 Python 源代码做 AST 安全审计，返回发现列表"""
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as exc:
        return [
            AuditFinding(
                severity="critical",
                category="syntax_error",
                message=f"代码语法错误: {exc}",
                line=exc.lineno or 0,
                col=exc.offset or 0,
            )
        ]

    visitor = _DangerousPatternVisitor()
    visitor.visit(tree)
    return visitor.findings


def audit_file(path: str | Path) -> list[AuditFinding]:
    """审计指定文件"""
    p = Path(path)
    if not p.exists():
        return [
            AuditFinding(
                severity="critical",
                category="file_error",
                message=f"文件不存在: {p}",
                line=0,
                col=0,
            )
        ]
    source = p.read_text(encoding="utf-8")
    return audit_source(source, filename=str(p))


def audit_adapter(domain: str) -> dict[str, Any]:
    """审计指定域名的 adapter，返回结构化结果"""
    from cliany_site.config import get_config

    adapter_dir = get_config().adapters_dir / domain
    commands_py = adapter_dir / "commands.py"

    if not commands_py.exists():
        return {
            "domain": domain,
            "safe": False,
            "error": f"adapter 不存在: {adapter_dir}",
            "findings": [],
        }

    findings = audit_file(commands_py)
    critical_count = sum(1 for f in findings if f.severity == "critical")

    return {
        "domain": domain,
        "safe": critical_count == 0,
        "finding_count": len(findings),
        "critical_count": critical_count,
        "findings": [f.to_dict() for f in findings],
    }
