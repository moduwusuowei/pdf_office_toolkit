# PDF Office Toolkit

[简体中文](README.md) | English

**An offline, install-free, open-source Windows batch PDF tool — merge, split, watermark, stamp, paging seal, encrypt/decrypt, compress, and export images, all processed locally so your files never leave your machine.**

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](pyproject.toml)

Built for office work in government and enterprises: archiving contracts, organizing bid documents, processing scans, and stamping official documents in batches — **with zero network requests**.

## Features

A single window with multiple panels. Process a whole batch at once; work runs on a background thread and can be cancelled anytime.

| Panel | What it does | Notes |
|---|---|---|
| Merge | Combine multiple PDFs | Merge all into one, or per folder (`{folder}_merged.pdf`) |
| Split | Split one PDF into many | Every N pages / by ranges (`1-3,5`) / at blank pages |
| Watermark | Text or image watermark | Chinese text tiling/center, angle/size/opacity; 9-grid image position |
| Stamp | Overlay a seal image | Click on the page preview to place it — WYSIWYG |
| Paging seal | Seal across page edges | Transparent margins auto-cropped; strips on the right edge; assembled preview + first/last page |
| Encrypt / Decrypt | AES-256 | Open an encrypted PDF later and enter its password once per session |
| Compress | Lossless / rasterize | Rasterize is smaller but turns text into images; outputs `xxx_min.pdf` |
| To images | PNG / JPG | Adjustable DPI/quality; per-file subfolder `{name}_{fmt}/` |

General behavior:

- **Source files are never modified**; all output goes to the folder you choose
- On conflict: **auto-rename** (`xxx(1).pdf`) / **overwrite** / **skip** (counted in the report)
- A report pops up at the end: ✓ done / ✗ failed (with reason) / ⊘ skipped
- Chinese/English UI with one-click switching; output folder and panel parameters persist
- Page syntax: `all` (default) / `last` / `1,3,5`
- Defaults to the current blue theme; use **Theme** at the bottom-left to recolor and apply instantly (see below)

## Requirements

- Windows 10/11
- Python **≥ 3.10** (3.12 tested)
- No admin rights, no external services

```bash
cd D:\20261016\pdf_gui
pip install -e .
```

For development (tests and packaging):

```bash
pip install -e ".[dev]"    # pytest / ruff / pyinstaller
```

## Usage

### Start

```bash
python -m pdf_gui
```

Or use the installed command: `pdf-office-toolkit`. The window is 1150×720: pick a panel on the left; on the right, from top to bottom, you get **file queue → parameters → output folder + Start**. Language switch and About sit at the bottom-left. Panels are cached, so switching back is instant.

### Common workflow

1. **Add files** with “Add Files” (multi-select) or “Add Folder”; reorder with Move Up/Down (affects merge order)
2. **Set parameters** (see below); Stamp and Paging seal have live previews
3. **Choose an output folder**; the default conflict rule is “Auto rename”
4. **Click Start**; the progress bar advances, and Cancel stops the remaining jobs

**Merge** — merge everything into one file (editable name), or merge separately per source folder.

**Split** — every N pages; by ranges (`1-3,5` produces two files: pages 1-3 and page 5); or split at blank pages.

**Watermark** — text tab (default tiled 45° gray, good for “Confidential” marks) or image tab (PNG/JPG, 9 positions). Leave Pages blank for all pages.

**Stamp** — add one PDF and one seal PNG, click on the preview to place the seal, then adjust size/opacity with the sliders.

**Paging seal** — add a PDF and a seal PNG, set seal height / vertical position / max strips, then click Preview:

- The seal PNG is **auto-cropped to its visible content** before being sliced into N vertical strips
- Each page gets one strip at the same vertical position, flush to the right edge; if pages exceed “max strips”, every K pages share a strip
- The panel first shows an **assembled view** (all strips side by side = the original seal), then the **first and last page** as printed
- Stack the printouts in page order and look at the right edge: the strips join into a complete seal

**Encrypt / Decrypt** — choose a mode; passwords are masked. The owner password is optional (defaults to the user password). Encrypted files added to any panel prompt for the password and are decrypted into `%TEMP%\pdf_office_toolkit` for the session.

**Compress** — lossless keeps structure and compresses content streams; rasterize re-renders pages (small DPI + low quality = smallest, best for pure scans).

**To images** — PNG/JPG, DPI (150 ≈ screen, 300 ≈ print), JPG quality; output to `output folder/{name}_png/`.

### Settings files

| File | Contents |
|---|---|
| `~\.pdf_office_toolkit.json` | Language / output folder / conflict rule / merge filename |
| `~\.pdf_office_toolkit_theme.json` | UI colors (auto-created on first run) |

Both fall back to defaults if corrupted; delete them to reset.

### Custom colors

Defaults match the current CustomTkinter blue theme. Click **Theme** at the bottom-left to open the color editor: pick a color per swatch and hit **Save & apply** — changes take effect immediately and are written to `~\.pdf_office_toolkit_theme.json`.

You can also edit that file directly (the About dialog has a button to open it); hand edits need a restart. Color values can be:

- a single color used in both light and dark mode, e.g. `"#2563EB"` or `"gray50"`
- a two-element array `[light, dark]` following the system appearance

Keys:

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

Invalid values are ignored and fall back to defaults. Delete the file to restore defaults.

## Build a portable Windows folder (optional)

Bundle the app with its runtime so it runs on machines without Python:

```powershell
.\build_win.ps1
# dist\pdf-office-toolkit\              (double-click pdf-office-toolkit.exe)
# dist\pdf-office-toolkit-windows-x64.zip
```

## Development

```bash
python -m pytest -q    # 102 tests (core engine + i18n/settings/workers/meta/theme)
ruff check .           # lint
```

Layout:

```
src/pdf_gui/
├── core/        # PDF engine: pure functions, no GUI dependencies, TaskResult
├── gui/         # i18n / theme / settings / widgets / panels (8 panels)
├── workers.py   # BatchWorker thread + event protocol
└── app.py       # main window (panel cache, navigation, About)
tests/           # pytest + manual_checklist.md for GUI smoke checks
docs/            # articles: WeChat, blog, release notes, paging-seal internals
```

Conventions: core changes need pytest coverage; all GUI text goes through the bilingual `gui/i18n.py`; GUI smoke tests follow `tests/manual_checklist.md`. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Articles

- [WeChat article (Chinese)](docs/wechat-article.md)
- [Technical blog (Chinese)](docs/blog-article.md)
- [v0.1.0 release notes (Chinese)](docs/release-notes-v0.1.0.md)
- [How the paging seal works (Chinese)](docs/paging-seal-implementation.md)
- [Docs index](docs/README.md)

## Privacy

- No network requests, no data upload
- Source files are never modified or deleted
- Temporary decrypted copies live only in the system temp directory

## License

[Apache-2.0](LICENSE)

Author: 魔都吴所谓 · Repository: https://github.com/moduwusuowei/pdf-office-toolkit

Version, copyright, and repository URL are configured in `src/pdf_gui/gui/app_meta.json` and shown in the About dialog.

Dependencies are all permissively licensed: pypdf (BSD), reportlab (BSD), Pillow (MIT-CMU), pypdfium2 (Apache-2.0/BSD), customtkinter (MIT).
