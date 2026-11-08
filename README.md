# Tarot JupyterLab

An English sidebar for JupyterLab 4. Draw one card, request a Socrates reading, and save the most recent result locally. Tarot readings are for entertainment and self-reflection.

## 用 wheel 本地演示

在独立的 Python 环境中执行。把命令里的文件名替换为实际下载的 wheel。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "jupyterlab==4.6.5" ".\tarot_jupyterlab-0.1.0-py3-none-any.whl"
$env:TAROT_DEMO_MODE = "1"
.\.venv\Scripts\python.exe -m jupyterlab
```

在浏览器的 JupyterLab 左侧打开 **Tarot**。输入一个示例问题，点击 **Draw a card → Generate reading → Save as latest**，确认覆盖提示。重启 JupyterLab 后用 **View latest** 查看保存结果。模拟解读会显示 **Demo reading (simulated)**。

## 接入课程 Socrates

退出 JupyterLab，用课程发给你们的地址、模型名和密钥设置以下变量，再重新启动。同一环境里设置 `TAROT_DEMO_MODE=0` 可关闭模拟模式。

| 环境变量 | 用途 |
| --- | --- |
| `SOCRATES_API_BASE` | 课程的 API 基础地址，由适配器附加 `/chat/completions`。 |
| `SOCRATES_MODEL` | 课程给出的模型名。 |
| `SOCRATES_API_KEY` | 课程密钥，只在本地配置。 |

真实解读会把问题、牌面和关键词发送给配置的课程服务。三项配置缺失时，后端会提示 AI 不可用，抽牌和保存仍可用。最近一条记录写在当前用户的 Jupyter 数据目录下的 `tarot-jupyterlab/latest.json`，可用 `jupyter --data-dir` 查看数据目录。每次确认保存会替换上一条。

## 从源码构建和测试

需要 Python、Node.js 和可下载依赖的网络。下面使用 Windows PowerShell。将开发环境的 Scripts 放在当前终端的 PATH 中后，`jlpm` 和 `jupyter-builder` 由 Python 开发依赖提供。

```powershell
python -m venv .venv
$env:Path = "$(Resolve-Path .\.venv\Scripts);$env:Path"
python -m pip install "jupyterlab==4.6.5" build "pytest>=8" "pytest-asyncio>=0.23"
python -m pytest
python -m build --wheel
```

wheel 生成在 `dist/`。用上面的本地演示步骤在另一个 Python 环境安装它。只检查或重建前端时，在 `frontend/` 执行 `jlpm install --immutable` 和 `jlpm build:prod`。Windows 之外使用相应虚拟环境的 `bin/` 目录和环境变量语法。

- [接口与技术学习指南](docs/learning.md)
- [两周分工和正式 PyPI 验收计划](Plan.md)
- [原始牌库字段说明](docs/card-set.md)
