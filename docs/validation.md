# Foundation validation

此记录仅描述基础源码的本地检查，不是模型实验结果。

2026-10-18，Python 3.12.14：

- `PYTHONPATH=src python -m unittest discover -s tests -v`：23 项测试通过。
- 通过 `pip wheel --no-build-isolation --no-deps .` 构建 wheel。
- 将 wheel 安装到独立目录，从仓库外运行 `python -m recovery_lab suite --seeds 3`：27 个脚本 episode 完成。
- 脚本对照符合预期：verify-retry 在已支持三种条件下安全完成；blind-retry 在 after_commit 下重复提交；claim-only 被识别为虚报。

GitHub Actions 配置包含 Python 3.11/3.12/3.13，但尚未在远程 GitHub 实际运行。没有声称完成平台兼容性测试。

修改代码后应重新运行测试，此记录不会自动更新。

## 0.0.2.dev0: CSV workers and model protocol adapter

2026-10-18，Python 3.12.14：

- 全部 43 项 unittest 通过（包括原有 23 项）。
- 真实 CSV worker 覆盖三种提交条件、重复提交、worker 失败日志、原输入保护、发布文件篡改检测、进程回收与合作式超时。
- 本地模拟 Chat Completions HTTP 服务与真实 CSV worker 完成端到端工具调用：提交超时、查询、等待、校验、发布、结构化结束、独立评分。
- 模型接口测试覆盖非法参数、未知工具、轮数/调用预算、虚报成功、混合 finish 批次和配置检查。
- 构建并安装 0.0.2.dev0 wheel，从仓库外运行 process CLI；after_commit 情况下安全完成，实际 published CSV 的三行内容与预期一致。
- API key 未出现在测试运行结果，特权故障标签未进入 HTTP 模型输入。

没有真实提供商凭据或本地模型服务参与本次验证。因此只声明协议与执行路径测试通过，不声明某个真实模型/提供商已兼容，也不报告模型成功率。
