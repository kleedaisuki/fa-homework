# fa-homework

有限自动机课程 Notebook，附带学习打卡与 OpenRouter AI 助教。

## 快速开始（PowerShell）

```powershell
cd D:\Code\fa-homework
uv sync --locked
# If the current terminal has not inherited your saved Windows user variable:
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'User')
# Optional: use an exact model ID from https://openrouter.ai/models.
$env:OPENROUTER_MODEL = 'openrouter/auto'
uv run jupyter lab fa.ipynb
```

默认使用 `openrouter/auto` 自动路由，可通过 `OPENROUTER_MODEL` 指定模型。
OpenRouter 可能产生费用；密钥必须有对应权限与余额。**不再需要 Ollama。**
仅使用进程环境变量，不自动读取 `.env`；修改 Windows 用户变量后，重启终端/Jupyter，或在启动 Jupyter 前执行上述加载命令。
在 JupyterLab 中使用项目的 Python 内核；如使用 VS Code，请选择 `.venv` 环境。

依次运行 Notebook：学习打卡 → 课程内容 → 三道题的助教窗口。在输入框中输入思路并点击“发送”，回复会逐步显示。学习和对话日志写到 `projects/fa.log`，不纳入 Git。

## 项目结构

- `fa.ipynb`、`images/`：原始课程内容及配图。
- `projects/problem_ai_helper.py`：三道有限自动机思考题的助教，保留 `%run projects/problem_ai_helper.py 2.1` 等入口。
- `projects/openrouter_client.py`：共用 OpenRouter 流式客户端。
- `projects/code_ai_helper.py`：原有代码练习助教也已切换 OpenRouter；当前课程未提供其所需的 `code_problems.md`、`code_policies.md` 和练习源码，因此它不会出现在本 Notebook 中，也不能单独作为现成代码练习运行。
- `uv.lock`：可复现的依赖版本；`uv sync --locked` 同时安装运行和测试依赖。

## 验证

```powershell
uv run pytest -q
uv run ruff check .
```

测试通过本地 HTTP 服务验证真实流式请求、鉴权、错误处理，以及三道题从创建控件、点击发送、渲染回复到写日志的流程；不消耗真实 API 额度。
不要提交密钥、`.env`、个人学习日志或包含私密对话的 Notebook 输出。服务端错误只展示安全提示，不展示原始响应体。

## 接口资料

- [OpenRouter Chat Completions](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request)
- [OpenRouter Streaming](https://openrouter.ai/docs/api/reference/streaming)
- [uv projects: locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
