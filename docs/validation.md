# Foundation validation

此记录仅描述基础源码的本地检查，不是模型实验结果。

2026-10-18，Python 3.12.14：

- `PYTHONPATH=src python -m unittest discover -s tests -v`：23 项测试通过。
- 通过 `pip wheel --no-build-isolation --no-deps .` 构建 wheel。
- 将 wheel 安装到独立目录，从仓库外运行 `python -m recovery_lab suite --seeds 3`：27 个脚本 episode 完成。
- 脚本对照符合预期：verify-retry 在已支持三种条件下安全完成；blind-retry 在 after_commit 下重复提交；claim-only 被识别为虚报。

GitHub Actions 配置包含 Python 3.11/3.12/3.13，但尚未在远程 GitHub 实际运行。没有声称完成平台兼容性测试。

修改代码后应重新运行测试，此记录不会自动更新。
