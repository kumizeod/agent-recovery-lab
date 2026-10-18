# Agent Recovery Lab

**An early code foundation for studying how tool-using agents recover from failures.**

一个准备慢慢扩展的开源项目起点：构建可执行任务环境，记录工具副作用，独立验证结果，之后再接入模型评测与 RL 训练。

## Status / 当前状态

这是基础骨架，不是第一版产品，不是已完成的 benchmark，也不是论文实现。

已经实现：

- 一个内存中的数据去重任务，保留每个 ID 的首次出现及原始顺序。
- 三种提交条件：无故障、提交前超时、提交成功但响应丢失。
- 服务端幂等键、公开状态查询、结构校验与发布工具。
- 模拟审批允许/拒绝，独立评分，执行事件导出。
- 三种脚本策略、命令行、单元测试与 GitHub Actions 配置。
- Chat Completions 工具调用 Agent：模型决定下一步工具，严格检查参数、限制轮数与调用量。
- 可选 process 后端：复制输入 CSV、启动后台 Python worker、查询/等待状态、读取日志、原子写出与发布 CSV。

尚未实现：MCP、数据库持久化、延迟提交/最终一致性、RL/SFT、模型排行榜、真实人工接管或可视化界面。LLM 协议已用本地模拟 HTTP 服务测试，尚未调用真实提供商模型，没有任何模型效果声明。

## Why / 一个最小问题

智能体提交作业后遇到超时：作业可能没提交，也可能已提交，只是确认响应丢失。

两种情况返回完全相同的公开 `ToolReply`。评分器知道内部事实，策略只能通过工具查证。盲目重试可能产生两个作业；使用稳定幂等键并查询状态的脚本策略能处理当前模拟器支持的两种超时。

**这不是新颖性声明。** 故障注入、状态评分和幂等恢复均有已有工作，本项目目前只提供可理解、可测试的基础代码。

## Quick start / 开始运行

Python 3.11+，运行时只使用标准库。推荐在虚拟环境中安装；无需 GPU、模型权重、API key 或外部服务。

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .

recovery-lab run --agent verify-retry --fault after_commit
recovery-lab run --agent blind-retry --fault after_commit
recovery-lab run --agent claim-only --fault none
recovery-lab run --require-approval --deny-approval
recovery-lab suite --seeds 3 --output outputs/suite.json
python -m unittest discover -s tests -v
```

### Real CSV + background worker / 真实文件与进程

```bash
recovery-lab run --backend process --csv examples/data/samples.csv --fault after_commit --output outputs/csv-run.json
```

自动建立 `outputs/episode-<unique-id>/`，包含 `source.csv`、`artifacts/*.csv`、`logs/*.log`、`published/*.csv`。JSON 中的 `workdir` 指向该目录。原输入文件不会交给 worker 修改，处理的是规范化复制件。当前只支持 `record_id,value` 两列，value 为整数；最多 10000 行、2 MB。

可用 `--workdir outputs/my-run` 指定**尚不存在**的目录，防止覆盖或混合实验。新作业返回 `running`；通过 `wait_job` 等待，完成后才得到 artifact ID。作业注册元数据仍在内存中，不支持服务崩溃恢复。

### LLM-driven tools / 模型决定动作

模型服务需要支持 Chat Completions 的 `tools` / `tool_calls`。兼容协议不等于已经验证所有提供商。请设置自己账户可用的模型 ID，不要照抄过期模型名称。

Linux/macOS：

```bash
export RECOVERY_LLM_BASE_URL="https://api.moonshot.cn/v1"
export RECOVERY_LLM_MODEL="YOUR_AVAILABLE_TOOL_CALLING_MODEL"
export RECOVERY_LLM_API_KEY="YOUR_API_KEY"
recovery-lab run --agent llm --backend process --csv examples/data/samples.csv --fault after_commit --max-turns 16 --max-calls 24 --output outputs/llm-run.json
```

PowerShell：

```powershell
$env:RECOVERY_LLM_BASE_URL = "https://api.moonshot.cn/v1"
$env:RECOVERY_LLM_MODEL = "YOUR_AVAILABLE_TOOL_CALLING_MODEL"
$env:RECOVERY_LLM_API_KEY = "YOUR_API_KEY"
recovery-lab run --agent llm --backend process --csv examples/data/samples.csv --output outputs/llm-run.json
```

本地 vLLM 等服务可用 `http://127.0.0.1:8000/v1`，并由你配置与模型相符的 tool parser。`.env.example` 只是模板，不会自动加载。密钥不放命令行参数，不写入运行输出，worker 环境也不会继承模型密钥。

选择远程 API 即会向该服务发送任务和公开工具返回（可能含 CSV 数据），并可能收费；请只使用允许发送的数据。不要提交 `.env` 或含业务数据的运行产物。

模型使用 `finish` 工具返回结构化自评，随后独立 grader 检查真实产物。自然语言声称成功不会直接获得成功分。`agent_trace` 保存模型实际收到的消息、工具结果与提供商返回的 token usage（若有）；`trace` 则是不能送给模型的特权审计记录。

更多说明见 [真实执行与模型接入](docs/live_execution.md)。

也可不安装，用源码运行（Linux/macOS）：

```bash
PYTHONPATH=src python -m recovery_lab run
PYTHONPATH=src python -m unittest discover -s tests -v
```

CLI 返回码 0 表示命令运行完成，不表示任务成功。请检查 JSON 的 `grade` 和 `error`。目前不是发布门禁工具。

## What to inspect / 看什么

| 策略 | 提交成功但响应丢失时的行为 | 预期检查结果 |
|---|---|---|
| `blind-retry` | 无幂等键，直接再次提交 | 任务可能完成，但 `duplicate_jobs=1`，`safe_success=false` |
| `verify-retry` | 查询稳定请求键，需要重试时复用同一键 | 当前契约下 `safe_success=true` |
| `claim-only` | 不操作，直接声称完成 | `false_success=true` |

这是脚本对照的预期行为，不是 LLM benchmark 分数。`suite` 的多个 seed 只改变输入数据，不能被当成多个独立任务家族。

输出中的 `trace` 是**运行结束后的特权审计记录**，包含内部副作用和故障标签。它不属于模型观察，不能原样放回策略上下文或作为训练输入。未来训练适配应只选取公开 observation/action。

## Structure / 代码入口

```text
src/recovery_lab/
  types.py          # Task、公开工具协议、Outcome
  environment.py    # 服务状态、故障位置、ToolClient 边界、审计记录
  grading.py        # 独立正确性参考、终态与行为指标
  agents.py         # 三个脚本策略
  llm_agent.py      # HTTP 客户端、工具 schema、参数检查、模型循环
  process_environment.py # 后台进程、文件与生命周期
  worker.py         # 固定的独立 CSV worker
  csv_io.py         # 严格 CSV 输入/输出
  tasks.py          # 当前唯一任务家族的数据生成
  runner.py         # 单次运行与异常记录
  cli.py            # run / suite
examples/custom_agent.py
tests/test_recovery.py
docs/architecture.md
docs/roadmap.md
docs/evaluation.md
```

想改策略，从 `agents.py` 或 `examples/custom_agent.py` 开始；想加故障，先读 `docs/architecture.md`；想改奖励或评分，先读 `docs/evaluation.md`。

## Limitations / 必须保留的边界

- 默认 memory 后端同步执行；process 后端真实启动后台进程，但仅运行固定去重程序，不能由模型提交任意 Python 或 shell。
- 一次 episode 仅首次新提交可注入一次故障；作业注册查询立即一致，没有延迟注册或丢失的在途提交。因此当前恢复脚本不代表一般分布式系统中的 exactly-once 保证。
- `request_approval` 读取预设模拟决定，不会联系真实的人。
- `ToolClient` 是接口边界，Python 同进程封装不是安全隔离。未来运行不可信 Agent 需要独立进程/服务和访问控制。
- 模型循环有轮数/调用预算及单请求超时。worker 超时在查询/等待/快照时检查，runner 退出时回收进程；不是独立实时 watchdog。自定义 Python Agent 的无限循环仍无进程级隔离。
- 评分器与执行器使用不同实现，但仍需持续审计，不能以“独立”替代正确性证明。
- 所有测试都通过也不说明模型可靠，更不代表可以连接生产服务。

## Relationship to existing work

后续优先复用 [Verifiers](https://github.com/PrimeIntellect-ai/verifiers) 和 [prime-rl](https://github.com/PrimeIntellect-ai/prime-rl)；参考 [Harbor](https://github.com/harbor-framework/harbor)、[ToolSandbox](https://github.com/apple-aiml-research/ToolSandbox) 和 [tau2-bench](https://github.com/sierra-research/tau2-bench) 的设计。

这些只是参考链接，当前没有集成、从属或官方合作关系。实现任务和故障时需继续检查相关研究与许可证。

## Upload to your GitHub / 上传

解压后在 GitHub 新建空仓库，不要同时初始化 README；然后在本目录执行：

```bash
git init
git add .
git commit -m "Initialize offline agent recovery foundations"
git branch -M main
# 将下面地址替换为自己的仓库地址
git remote add origin https://github.com/YOUR_USERNAME/agent-recovery-lab.git
git push -u origin main
```

上传前运行测试，检查 `git diff --cached`。不要提交密钥、私人数据或 `outputs/`。这份源码包不包含 Git 历史，也没有替你创建或发布远程仓库。

## License

MIT，见 [LICENSE](LICENSE)。

