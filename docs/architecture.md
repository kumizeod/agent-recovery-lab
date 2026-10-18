# Architecture / 设计边界

## One episode

1. `make_task(seed)` 生成不可变输入；seed 只影响模拟数据。
2. runner 建立全新的 `JobEnvironment`。
3. Agent 只接收 `TaskView` 与 `Tools` 接口。
4. 每次工具调用检查预算，执行逻辑并记录公开返回与私有事件。
5. Agent 返回结构化 `Outcome`，异常则被记录为 failed。
6. runner 获取深拷贝 snapshot，由独立 grader 评分。

默认 memory 后端同步运行。process 后端由子进程执行真实 CSV 去重，工具返回 running/failed/ok；通过 wait_job/read_job_logs 查询。工具异常状态使用 `ToolReply` 表达；非预期代码异常由 runner 保存，不会从实验记录中丢弃。

## Fault semantics

| 模式 | 内部提交 | Agent 看到什么 | 查询稳定键 |
|---|---|---|---|
| none | 一次 | job/artifact ID | 存在 |
| before_commit | 首次未提交 | 通用 timeout | 不存在 |
| after_commit | 已提交一次 | 与 before 完全相同的 timeout | 存在 |

同一幂等键映射到同一已完成作业；新 episode 清空映射。幂等检查在注入故障之前，重复查询已知 key 不触发新故障。此行为是显式服务契约，不是模型推理的保证。

memory 后端提交后立即完成；process 后端提交代表启动并注册 worker，不代表任务完成。注册立即一致，不模拟延迟提交。`publish_artifact` 特意不幂等，所以重复发布会留下多次副作用。

## Public vs privileged

Public: instruction、工具参数/返回、source 内容、按 key 查询、结构校验、审批回复。

Privileged: FaultMode、故障是否消费、完整 job/效果账本、评分器参考结果、审计 trace。

接口分离只方便组织可信脚本。若要接入能任意执行 Python/命令的 Agent，不能把环境内存、评分源码、测试数据和模型放在同一个可访问进程或挂载目录中。

## Add a fault

先写清：触发条件、发生在提交前/后、状态变化、公开观察、持续次数、是否可恢复、可恢复需要哪些信息。再添加枚举/实现/对照测试。不要在 message 中泄漏真实提交状态。

延迟提交需要显式虚拟时钟或事件队列；不能直接把 not_found 当作“将来一定不会提交”。这是后续独立设计工作。

## Add a task

新任务需要独立规范、输入、执行动作、评分参考、脚本可解性证明和负例。不要把所有任务都压进当前固定的 `submit_job`：任务超过两类后再抽取 operation/job spec。

