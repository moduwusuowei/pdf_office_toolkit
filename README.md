# PDF 办公百宝箱 · PDF Office Toolkit

简体中文 | [English](README.en.md)

**离线、免安装、开源的 Windows PDF 批量处理工具：合并、拆分、水印、盖章、骑缝章、加密解密、压缩、转图片，全部在本机完成，文件不出电脑。**

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](pyproject.toml)

面向政企办公场景设计：合同归档、投标文件整理、扫描件处理、公文批量盖章，**不发起任何网络请求**。

## 功能总览

单窗口多面板，一次处理一批文件，后台线程运行可随时取消：

| 面板 | 功能 | 要点 |
|---|---|---|
| 合并 | 多文件合并 | 全部合并为一个；或按所在文件夹分别合并（输出 `{文件夹名}_合并.pdf`） |
| 拆分 | 一份拆多份 | 每 N 页一拆 / 按页码范围（如 `1-3,5`）/ 按空白页自动分段 |
| 水印 | 文字或图片水印 | 文字支持中文平铺/居中、角度字号不透明度可调；图片九宫格定位 |
| 盖章 | 印章叠加 | 页面预览上点击即可定位，所见即所得 |
| 骑缝章 | 印章跨页分条 | 自动裁掉印章透明边，纵向切条贴右边缘；面板内显示拼合示意 + 首末页预览 |
| 加密解密 | AES-256 | 加密后的文件再次添加时可输密码临时解密，后续直接处理 |
| 压缩 | 无损 / 光栅化 | 光栅化体积更小但文字变图片；输出 `xxx_min.pdf` 不覆盖源文件 |
| 转图片 | PNG / JPG | DPI 与质量可调；每文件输出到 `{文件名}_{格式}/` 子目录 |
| 图片转 PDF | 多图合成一份 | 按队列顺序排版；A4 / 原始尺寸、方向、页边距、质量可调，透明 PNG 自动铺白底 |

通用规则：

- **源文件永不修改**，所有输出写入你指定的输出目录
- 文件或文件夹可**直接拖进窗口**，加入当前面板的队列（PDF 面板收 PDF，图片面板收图片）
- 勾选运行条右侧「完成后打开输出目录」：批处理成功结束后自动弹出资源管理器
- 同名输出三种处理：**自动重命名**（`xxx(1).pdf`）/ **覆盖** / **跳过**（报告计入跳过数）
- 处理完成弹报告：✓ 成功 / ✗ 失败（含原因）/ ⊘ 跳过，底部有计数
- 界面中英双语，一键切换；输出目录、各面板参数在重启后保留
- 页码填写语法：`all`（默认全部）/ `last`（仅末页）/ `1,3,5`（指定页）
- 配色默认沿用当前蓝色主题，左下角「配色」可逐项改色并立即生效（见下文）

## 环境搭建

- Windows 10/11
- Python **≥ 3.10**（3.12 已验证）
- 无需管理员权限；不需要任何外部网络服务

```bash
cd D:\20261016\pdf_gui
pip install -e .
```

不装成包、只想跑源码：`pip install -r requirements.txt`（锁定验证过的版本）；开发环境用 `pip install -r requirements-dev.txt` 或 `pip install -e ".[dev]"`。

开发环境（含测试与打包工具）：

```bash
pip install -e ".[dev]"    # pytest / ruff / pyinstaller
```

## 运行用法

### 启动

```bash
python -m pdf_gui
```

或使用安装后的命令：`pdf-office-toolkit`。窗口 1150×720，左侧选功能面板，右侧从上到下依次是**文件队列 → 参数 → 输出目录 + 开始**。左侧底部是**切换语言**与**关于**；面板切换后状态保留，不会重复加载。

### 每个面板怎么用

1. **添加文件**：点「添加文件」多选、点「添加文件夹」导入整目录，或直接把文件/文件夹拖进窗口；「上移/下移」调整顺序（影响合并顺序）
2. **选参数**：各面板参数见下文说明；盖章/骑缝章有实时预览
3. **设输出目录**：点「选择」浏览；同名规则默认「自动重命名」
4. **点「开始」**：进度条实时推进，可点「取消」终止剩余任务

**合并**——两个单选：全部合并为一个（可改输出文件名）；按所在文件夹分别合并（适合「每个目录里的散页各自归档」）。

**拆分**——三选一：每份页数 N；页码范围 `1-3,5` 表示输出 2 份（1-3 页一份、第 5 页一份）；按空白页分段适合「扫描件封面/分隔页」场景。

**水印**——两个标签页：文字（默认平铺 45° 灰色，适合"机密"类标注）；图片（选 PNG/JPG，位置九选一）。「页码」留空表示全部页。

**盖章**——先添加 1 个 PDF 和印章 PNG，预览显示第 1 页，**在预览图上点击想要的位置**，拖动滑杆调大小/不透明度，实时生效。

**骑缝章**——加 PDF + 印章 PNG，调印章高度/垂直位置/最大条数后点「预览效果」：

- 印章 PNG 会**自动裁掉四周透明边**，再横向切成 N 条竖条
- 每页在同一垂直位置、贴右边缘画一条；页数超过「最大条数」时每 K 页共用一条
- 面板先显示**拼合示意**（所有竖条并排还原完整印章），再显示**第 1 页 / 最后一页**的实际效果
- 打印后按页序叠放，从右侧边缘看，竖条会拼合成完整印章

**加密解密**——单选加密或解密，密码框不回显；加密时所有者密码可留空（与用户密码一致）。加密后的文件再次添加到任何面板时会弹密码框，输对后本会话内直接处理（临时解密文件在 `%TEMP%\pdf_office_toolkit`）。

**压缩**——无损保结构压内容流；光栅化重渲染整页（选小 DPI + 低质量体积最小，适合纯扫描件）。

**转图片**——PNG 或 JPG、渲染 DPI（150≈屏显，300≈打印）、JPG 质量；输出到 `输出目录/文件名_png/`。

**图片转 PDF**——把队列里的图片按顺序合成一份 PDF（PNG / JPG / BMP / WEBP / TIFF）：页面选 A4（可设方向、页边距）或原始尺寸；图片等比缩放居中，透明 PNG 自动铺白底，手机照片按 EXIF 方向自动摆正。

**完成后打开输出目录**——运行条右下角勾选一次即可（设置会记住，重启仍生效）；批处理有成功产物时，结束后自动打开输出目录。结果报告里也有「打开输出目录」按钮。

### 设置文件

| 文件 | 内容 |
|---|---|
| `~\.pdf_office_toolkit.json` | 语言 / 输出目录 / 同名规则 / 合并文件名 / 完成后打开输出目录 |
| `~\.pdf_office_toolkit_theme.json` | 界面配色（首次运行自动生成） |

两个文件都支持损坏后自动回退默认值，删除即重置。

### 自定义配色

默认配色与当前界面一致（CustomTkinter 蓝色主题）。左下角点「配色」即可打开配色面板：逐项点色块选颜色，**保存后立即生效**，同时写入 `~\.pdf_office_toolkit_theme.json`。

只改「主色」时，悬停色（按钮悬停、下拉框右侧箭头按钮，如「同名时」那个下拉）会按主色自动推一个更深的颜色跟着变；如果你单独调过「主色悬停」，则保持你选的颜色。

也可以直接编辑这个文件（「关于」里有打开按钮），手改后需重启程序。颜色值可以写：

- 单个颜色：明暗模式通用，如 `"#2563EB"` 或 `"gray50"`
- 两元素数组：`[浅色, 深色]`，跟随系统明暗模式

可用的键：

```json
{
  "window_bg": ["gray92", "gray14"],
  "card_bg": ["gray86", "gray17"],
  "accent": ["#3B8ED0", "#1F6AA5"],
  "accent_hover": ["#36719F", "#144870"],
  "button_text": ["#DCE4EE", "#DCE4EE"],
  "text": ["gray10", "#DCE4EE"],
  "muted_text": ["gray", "gray"],
  "entry_bg": ["#F9F9FA", "#343638"],
  "border": ["#979DA2", "#565B5E"],
  "progress_track": ["#939BA2", "#4A4D50"]
}
```

非法颜色值会被忽略并回退默认，不会影响启动。删掉配置文件则恢复默认配色。

## 本地构建绿色版（可选）

把程序连同运行时打包成一个免安装文件夹，拷到无 Python 的机器也能跑：

```powershell
.\build_win.ps1
# 产出 dist\pdf-office-toolkit\（双击 pdf-office-toolkit.exe 运行）
#      dist\pdf-office-toolkit-windows-x64.zip（分发用压缩包）
```

需要带安装向导的 `setup.exe`（安装进度、开始菜单、卸载项）时，用 `.\build_installer.ps1`，需要先装 Inno Setup 6。完整步骤、静默安装参数和公司电脑不放行 exe 时的 GitHub Actions 方案见 [docs/build-installer.md](docs/build-installer.md)。

想要**单个 exe、不携带 `_internal` 目录**时，用 `.\build_onefile.ps1`（PyInstaller `--onefile`），产物 `dist\pdf-office-toolkit-onefile.exe`。代价是每次启动先解压到临时目录，冷启动慢 1～3 秒，杀软误报概率也略高；日常分发仍推荐 onedir + zip/安装包。

## 开发

```bash
python -m pytest -q    # 128 个测试（core 引擎 + i18n/settings/theme/workers/meta/dnd）
ruff check .           # lint
```

项目结构：

```
src/pdf_gui/
├── core/        # PDF 引擎：纯函数、零 GUI 依赖，统一 TaskResult 返回
├── gui/         # i18n / theme / settings / dnd / widgets / panels（9 个面板）
├── workers.py   # BatchWorker 后台线程与事件协议
└── app.py       # 主窗口（面板缓存、导航、关于）
tests/           # pytest + manual_checklist.md（GUI 手测清单）
docs/            # 公众号 / 博客 / 发布公告 / 骑缝章原理等分享文章
```

约定：core 改动必须带 pytest 用例；GUI 文案一律走 `gui/i18n.py` 双语字典；手测按 `tests/manual_checklist.md`。贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。



## 隐私说明

- 不发起任何网络请求、不上传任何数据
- 源文件永不被修改、永不被删除
- 加密文件临时解密只发生在系统临时目录，供当前会话使用

## 许可

[Apache-2.0](LICENSE)

作者：魔都吴所谓 · 仓库：https://github.com/moduwusuowei/pdf_office_toolkit

版本号 / 版权 / 仓库地址统一配置在 `src/pdf_gui/gui/app_meta.json`，主窗口「关于」中可见。

依赖栈均为宽松许可：pypdf（BSD）、reportlab（BSD）、Pillow（MIT-CMU）、pypdfium2（Apache-2.0/BSD）、customtkinter（MIT）、tkinterdnd2（拖拽，Tcl 层 tkdnd，MIT）。
