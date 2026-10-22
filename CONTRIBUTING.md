# 贡献指南 / Contributing

感谢关注本项目！Thanks for your interest!

## 环境 / Setup

Windows + Python ≥ 3.10：

```bash
git clone https://github.com/moduwusuowei/pdf-office-toolkit.git
cd pdf-office-toolkit
pip install -e ".[dev]"
python -m pdf_gui
```

## 提交前 / Before You Commit

```bash
ruff check .
python -m pytest -q
```

- 引擎层（`src/pdf_gui/core/`）保持纯函数、零 GUI 依赖，改动必须有对应 pytest 用例。
- GUI 层（`src/pdf_gui/gui/`）改动请附截图或录屏，并过一遍 `tests/manual_checklist.md` 的相关小节。
- 界面文案新增一律走 `gui/i18n.py`，中英两份字典都要加（键校验测试会拦漏）。
- 版本号 / 版权 / 仓库地址改 `src/pdf_gui/gui/app_meta.json`（`pyproject.toml` 的 version 同步改）。
- 依赖改动要同时改 `pyproject.toml`、`requirements.txt`、`requirements-dev.txt`。后两者带中文注释，必须保存为 **UTF-8 with BOM**——pip 在中文 Windows 上按本地代码页读文件，无 BOM 会直接 `UnicodeDecodeError`。
- 拖拽请继续用 `gui/dnd.py` 的 tkinterdnd2 方案，不要改回 ctypes 子类化窗口过程（Python 3.12+ 会在拖放时因 GIL 检查直接崩溃）。

## Issue / PR 约定

- Bug 请用模板并附：系统版本、程序版本（zip 名或 tag）、复现步骤、报错截图。
- PR 请描述动机与验证方式；一个 PR 一件事。
- 提交信息用中文或英文皆可，格式 `type: 摘要`（feat/fix/docs/build/ci/chore）。

## 行为准则 / Code of Conduct

保持友善、对事不对人。Be kind and focus on the work.
