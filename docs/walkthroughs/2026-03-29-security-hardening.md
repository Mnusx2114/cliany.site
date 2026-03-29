# Phase 4.3 安全加固

**日期:** 2026-03-29
**Phase:** 4.3 (v0.5.0 生态建设)
**状态:** 已完成

## 概述

为 cliany-site 添加三层安全防护：Session 加密存储、动作沙箱模式、生成代码静态审计。

## 变更清单

### 4.3.1 Session 加密存储

**文件:** `src/cliany_site/security.py` (新增, ~238 行)

- 基于 Fernet 对称加密 (cryptography 库) 加密 Session JSON
- 密钥管理优先级：系统 keyring (macOS Keychain / Linux Secret Service) > 文件回退 (`~/.cliany-site/.keyfile`, chmod 600)
- 加密文件格式：`CLIANY_ENC_V1:` 前缀 + Fernet token
- 向后兼容：读取时自动检测明文 Session 并迁移为加密格式

**文件:** `src/cliany_site/session.py` (修改)

- `save_session_data()` 和 `load_session_data()` 委托给 security 模块加密/解密
- 明文文件自动迁移，无需用户干预

**依赖:** `pyproject.toml` 新增 `cryptography >= 43.0` 和 `keyring >= 25.0`

### 4.3.2 动作沙箱模式

**文件:** `src/cliany_site/sandbox.py` (新增, ~115 行)

- `SandboxPolicy` frozen dataclass：包含 `enabled`、`allowed_domains`、`block_js_eval`、`block_downloads` 等策略字段
- `SandboxPolicy.from_domain(domain)` 工厂方法：基于域名生成默认策略（允许子域名）
- `validate_navigation(policy, url)` — 拦截跨域导航、`javascript:`/`file:`/`data:text/html` 协议
- `validate_action(policy, action)` — 拦截 JS eval/exec、文件下载等危险动作
- `validate_action_steps(policy, steps)` — 批量验证，返回违规列表

**文件:** `src/cliany_site/cli.py` (修改)

- 新增 `--sandbox` 全局选项，通过 `ctx.obj` 传递给下游命令

### 4.3.3 生成代码审计

**文件:** `src/cliany_site/audit.py` (新增, ~210 行)

- AST 静态分析，使用 `ast.NodeVisitor` 模式
- 检测模式：
  - `eval()`/`exec()`/`compile()`/`__import__()` — 危险调用 (critical)
  - `os.system()`/`subprocess.*` — 系统命令执行 (critical)
  - `import pickle`/`ctypes`/`marshal` — 高风险模块 (warning)
- `AuditFinding` frozen dataclass：severity (Literal["critical","warning","info"])、category、message、line、col
- 公开 API：`audit_source()`、`audit_file()`、`audit_adapter(domain)`

### 错误体系扩展

**文件:** `src/cliany_site/errors.py` (修改)

- 新增 `SecurityError` 异常类
- 新增错误码：`SANDBOX_VIOLATION`、`AUDIT_FAILED`、`SESSION_DECRYPT_FAILED`

## 测试

**文件:** `tests/test_security.py` (新增, ~45 个测试)

| 测试类 | 用例数 | 覆盖 |
|--------|--------|------|
| TestEncryptDecrypt | 6 | 加密/解密往返、错误密钥、格式检测 |
| TestEncryptedSession | 3 | 保存/加载、明文迁移、不存在文件 |
| TestSandboxPolicy | 2 | from_domain 工厂、permissive 策略 |
| TestValidateNavigation | 7 | 同域/子域/跨域/协议拦截 |
| TestValidateAction | 7 | JS eval/下载/跨域导航拦截 |
| TestValidateActionSteps | 2 | 批量验证 |
| TestAuditSource | 9 | 各类危险模式检测 + 语法错误 |
| TestAuditFile | 3 | 文件级审计 |
| TestAuditAdapter | 3 | adapter 级审计 (mock config) |
| TestAuditFinding | 1 | to_dict 序列化 |

## 验证结果

```
ruff check:  All checks passed!
mypy:        Success: no issues found in 59 source files
pytest:      475 passed in 0.87s
```

## 架构决策

1. **密钥存储**: keyring 优先（系统级安全），文件回退保证 CI/无桌面环境可用
2. **加密格式前缀**: `CLIANY_ENC_V1:` 使格式版本化，便于后续升级加密算法
3. **沙箱为可选**: `--sandbox` 全局开关，默认关闭，不影响现有用户工作流
4. **AST 审计而非正则**: 准确性更高，避免字符串匹配误报（如注释中的 eval）
