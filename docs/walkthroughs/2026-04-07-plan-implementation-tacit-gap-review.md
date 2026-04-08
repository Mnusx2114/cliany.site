# 规划方案与近期实现差距评审：默会知识视角

**日期：** 2026-04-07
**评审基线：** `docs/brainstorm-iteration-directions.md` 与 `ee9bbf6..HEAD`
**评审方法：** Git 提交轨迹 + 代码落点核对 + Michael Polanyi 默会知识理论

## 结论摘要

本次评审的核心结论不是“规划没有执行”，而是“规划执行速度很快，但只有一部分已经内化为团队的默认工作方式”。

从 2026-03-29 之后的提交轨迹看，项目用很短时间把大量 brainstorming 条目转成了模块、命令和测试：统一配置、结构化日志、pytest、CI、headless/远程 CDP、工作流编排、安全加固、适配器市场、Python SDK、HTTP API、iframe/Shadow DOM、交互式探索、录像与回放等方向都已经进入仓库。

但按 Polanyi 的默会知识理论来看，真正已经“内化”的，主要是功能扩张和探索链路相关能力；跨切面的稳定性治理仍更多停留在显性文档、独立模块或 README 叙事中，还没有彻底进入 CLI 主路径、CI 门禁和日常编码习惯。

换句话说：项目已经形成了不少“会做”的默会知识，但很多治理型知识还只完成了第一层模块化，没有完成第二层制度化。

## 一、评审基准

### 1.1 规划文档的优先级主张

`docs/brainstorm-iteration-directions.md` 将迭代方向分为四层：

- P0：裸 except 修复、结构化日志、pytest 套件
- P1：CI/CD、执行进度反馈、凭证安全、智能自愈
- P2：工作流编排、交互式探索、适配器市场、headless 模式
- P3：SDK/API、多语言、并行执行、TUI 增强

文档明确建议先稳固地基，再做体验和增长能力。

### 1.2 实际实现的时间轨迹

从 `ee9bbf6` 到当前 HEAD 的提交显示，3/29 至 4/3 的节奏大致如下：

- 2026-03-29：`aa6340f`、`e251275`、`2bfb68d`、`fe31250`、`4dc5be9`、`cf5a8b1`、`601d74a`、`c429dc9`
- 2026-03-30：extract、selector 预计算、LLM 重试、SDK/API、iframe/Shadow DOM
- 2026-03-31：多模态感知、开源社区基础设施、文档与发版补齐
- 2026-04-02：v0.8 交互式探索、录像、回放、增量扩展、优雅中断
- 2026-04-03：官网内容重构与 v0.8.1 发布

这说明规划并未被搁置，而是被快速 phase 化并落地。

## 二、按默会知识理论理解当前状态

Polanyi 的经典判断是：“我们知道的，多于我们能说出的。”

落到本项目，可以把知识分成三层：

- 显性知识：brainstorm 文档、walkthrough、README、phase 提交说明
- 半内化知识：已经形成模块，但未成为默认工作流
- 默会知识：开发者不必回看文档，也会自然按这种方式继续实现

本仓库目前最强的默会知识，明显集中在“浏览器探索与执行链路”而不是“跨切面治理纪律”。

## 三、已经内化为默会知识的部分

### 3.1 探索链路的人机协作能力已经非常成熟

近期 v0.8 系列提交集中实现：

- `src/cliany_site/commands/explore.py`
- `src/cliany_site/explorer/interactive.py`
- `src/cliany_site/explorer/recording.py`
- `src/cliany_site/commands/replay.py`

这组改动体现出一类非常明显的默会知识：团队已经不再把 explore 理解为“一次性生成命令”，而是理解为一个可暂停、可回退、可录像、可回放、可增量扩展的人机协同过程。

这种理解不是规划文本本身，而是被编码进了探索循环、交互控制器、录像管理器和回放命令里。

### 3.2 浏览器运行环境适配已经形成稳定手感

以下文件显示，团队对“浏览器并不总是本地 GUI Chrome”的认识已经非常具身化：

- `src/cliany_site/cli.py`
- `src/cliany_site/browser/cdp.py`
- `src/cliany_site/browser/launcher.py`

`--cdp-url`、`--headless`、本地自动拉起与远程探测逻辑共同说明，团队已经把“环境差异”当成默认问题处理，而不是例外。

### 3.3 代码生成拆分能力已经进入实现习惯

规划文档把 `generator.py` 超大文件拆分列为重点。当前代码已经形成：

- `src/cliany_site/codegen/generator.py`
- `src/cliany_site/codegen/templates.py`
- `src/cliany_site/codegen/params.py`
- `src/cliany_site/codegen/dedup.py`
- `src/cliany_site/codegen/naming.py`
- `src/cliany_site/codegen/merger.py`

这说明“先把热点大文件拆成稳定边界，再继续加功能”已经不只是文档建议，而是实际被执行过的开发套路。

### 3.4 测试已经从愿景变成组织能力

规划中提出引入 pytest。当前仓库已具备：

- `pyproject.toml`
- `.github/workflows/ci.yml`
- `tests/`

这不是“计划里写了测试”，而是“项目已经默认有 tests 目录、pytest 配置和 CI test job”。这部分是显性知识成功转成默会知识的代表案例。

## 四、仍主要停留在显性文本或半内化状态的部分

### 4.1 裸 except 没有完成从声明到习惯的迁移

规划把裸 except 修复列为 P0，但当前热路径中仍有宽泛异常捕获，例如：

- `src/cliany_site/action_runtime.py`
- `src/cliany_site/explorer/engine.py`
- `src/cliany_site/session.py`
- `src/cliany_site/security.py`
- `src/cliany_site/codegen/templates.py`

这说明异常体系虽然已经通过 `src/cliany_site/errors.py` 建模，但“优先写具体异常、保留传播语义”的习惯尚未内化。

### 4.2 结构化日志已存在，但尚未成为唯一正统通道

结构化日志的模块和初始化入口已经建立：

- `src/cliany_site/logging_config.py`
- `src/cliany_site/cli.py`

但命令主路径里仍可见直接 `print`、`click.echo` 和 Rich 输出混用，例如：

- `src/cliany_site/commands/explore.py`
- `src/cliany_site/commands/replay.py`

这说明日志框架已经“写出来”，却还没有变成每个新增命令的默认写法。

### 4.3 错误恢复 UX 只完成了底层能力，未完成用户入口闭环

`src/cliany_site/checkpoint.py` 与 `src/cliany_site/action_runtime.py` 已支持 checkpoint 保存、dry-run 和执行日志，这证明底层能力真实存在。

但运行时文案提示“可使用 `--resume` 继续执行”，而当前 CLI 主入口并没有对应选项：

- 已有能力：`src/cliany_site/action_runtime.py`
- 缺失入口：`src/cliany_site/commands/explore.py`

这是一种典型的“代码里有，产品面不可达”的半内化状态。

### 4.4 智能自愈尚未形成规划中的主动闭环

当前仓库已经具备：

- `src/cliany_site/snapshot.py`
- `src/cliany_site/healthcheck.py`
- `src/cliany_site/commands/check.py`

这更接近“快照比对 + 健康检查 + 可选修复”。

而规划中的目标是：执行前预检、主动检测 UI 变化、热修复 selector、健康度评分与告警。现阶段还没有证据表明这些能力已经全部进入默认执行链路。

### 4.5 工作流编排实现的是受控线性版，不是规划版全量形态

`src/cliany_site/workflow/engine.py` 已支持：

- 线性步骤
- 条件 `when`
- retry
- 变量插值

但从实现看，仍偏向线性 pipeline，不是规划中强调的分支、循环和复杂数据引用全量能力。README 示例中的 `$prev.data.results[0].name` 也超前于当前解析器能力。

### 4.6 安全模块存在，但制度化接线仍需核实

仓库已经有：

- `src/cliany_site/security.py`
- `src/cliany_site/sandbox.py`
- `src/cliany_site/audit.py`

但从主入口能直接确认的是 `--sandbox` 被写入了 `ctx.obj`。是否所有执行主路径都真正受沙箱与审计约束，还需要进一步以“主路径调用链”方式核对。

这类问题正是 Polanyi 意义上的“尚未内化”：团队知道这件事重要，也写了模块，但还没有保证它每次自然生效。

## 五、最近提交与规划优先级的偏移

如果只看最近 8-12 个提交，会得到一个明显印象：

- 交互式探索
- 录像
- 回放
- 增量扩展
- 官网改版

这些都属于高可见度、强展示性的能力。

而 P0/P1 类型的治理工作虽然在 3/29 附近集中做过一轮，但在最近节奏里已经不再是主旋律。于是形成一种结构性偏移：

- 计划建议：先稳固治理，再推体验
- 实际节奏：治理能力做出第一层后，快速转向体验强化和对外叙事

这并不等于规划失败，但会增加“假完成感”：模块在，文档在，README 在，但默认路径和组织纪律未必同样成熟。

## 六、转换管道断裂点

结合代码与提交，当前“计划 -> 实现 -> 内化”的转换管道主要断在四个地方。

### 6.1 断在模块化之后、制度化之前

表现为：

- 已有独立模块
- 已有文档或 walkthrough
- 但没有成为所有主路径的默认行为

典型对象包括日志、沙箱、审计、自愈和断点恢复。

### 6.2 断在 README 与主路径之间

部分能力在 README 中已被作为完成特性表达，但主路径仍缺入口、缺默认调用或缺示例可达性。

这会让“显性叙事”先于“真实可达能力”完成闭环。

### 6.3 断在经验验证与 CI 门禁之间

仓库的 `qa/` 已经积累大量浏览器 smoke/integration 脚本，但 `.github/workflows/ci.yml` 目前只覆盖 ruff、mypy、pytest，没有把这些强依赖浏览器 tacit know-how 的验证接入门禁。

于是很多关键经验仍然依赖作者知道该怎么手动验证，而不是组织机制自动防守。

### 6.4 断在模板层的旧习惯复制

即便核心层已经开始治理，若模板层仍保留宽泛异常和旧输出方式，就会把旧习惯继续扩散到生成代码和后续适配器中。

这使“治理改进”难以通过生成体系自动放大。

## 七、总体评估

### 7.1 规划完成度

中高。大量规划项已经实际落地，不应简单定性为“与规划差距很大”。

### 7.2 规划内化度

不均衡。功能类能力内化明显，治理类能力多处停留在半内化状态。

### 7.3 近期趋势

近期提交持续强化的是：

- 交互探索体验
- 回放与记录能力
- 官网叙事与对外展示

而不是继续压缩治理债务。

## 八、建议的后续行动

### 8.1 重新定义“完成”标准

建议将规划项完成从“有模块/有 commit”改为以下四级：

1. 有模块
2. 有 CLI 或主路径可达入口
3. 有自动化测试覆盖
4. 有 CI 门禁保护

只有达到第 3-4 级，才可视为真正进入组织性默会知识。

### 8.2 优先回审 P0/P1 热路径

建议优先复核以下方向：

- `except Exception` 清理
- 结构化日志与用户输出分流
- `--resume` 与 checkpoint 闭环
- `sandbox` / `audit` 主路径接线
- 自愈从 check 命令走向执行前预检

### 8.3 做一次“计划项 -> 默认路径可达性”对账

建议后续单独产出对账表，核对以下维度：

- 规划项
- 模块落点
- CLI 入口
- 运行时调用
- 测试覆盖
- CI 门禁
- README 承诺

## 九、最终判断

这个仓库不是“规划没有执行”，而是“规划执行很快，但只有一部分已经沉淀为团队默认做法”。

最成熟的默会知识，已经体现在浏览器探索、交互控制、录像回放和生成链路等功能扩张能力里；最大的差距，则体现在异常处理、日志纪律、安全约束、自愈闭环和主路径收口等治理能力尚未全面制度化。

从 Polanyi 视角看，当前项目的下一步重点不应只是继续扩功能，而应把已经写出来的治理知识继续压实为“下次开发者无需翻文档，也会自然这样做”的默认实践。
