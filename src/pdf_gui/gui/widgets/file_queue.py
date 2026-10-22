"""文件队列控件：添加/排序/移除文件，逐个校验；PDF 加密时提示输密码并临时解密。

kind="image" 时接受常见图片格式（供图片转 PDF 面板使用），不涉及密码。"""

import tempfile
import tkinter as tk
import uuid
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image
from pypdf import PdfReader

from ...core import SUPPORTED_SUFFIXES, decrypt_pdf
from ..i18n import t

TEMP_DIR = Path(tempfile.gettempdir()) / "pdf_office_toolkit"

IMAGE_FILE_TYPES = [("图片", " ".join(f"*{s}" for s in sorted(SUPPORTED_SUFFIXES)))]


class FileQueue(ctk.CTkFrame):
    def __init__(self, master, *, max_files=0, ask_password, on_change=None,
                 state=None, kind="pdf"):
        super().__init__(master)
        # state 存在时队列随面板重建保留（切换语言/配色不会清空用户添加的文件）
        self._state = state
        self.kind = kind               # "pdf" 或 "image"
        self.max_files = max_files     # 0 = 不限；1 = 单文件（添加新文件时替换旧的）
        self.items: list[dict] = self._restore()   # [{path, display, ok}]
        self.ask_password = ask_password
        self.on_change = on_change
        self.grid_columnconfigure(0, weight=1)
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(bar, text=t("add_files"), width=96,
                      command=self._pick_files).pack(side="left", padx=(0, 4))
        ctk.CTkButton(bar, text=t("add_folder"), width=96,
                      command=self._pick_folder).pack(side="left", padx=4)
        ctk.CTkButton(bar, text=t("move_up"), width=64,
                      command=lambda: self._move(-1)).pack(side="left", padx=4)
        ctk.CTkButton(bar, text=t("move_down"), width=64,
                      command=lambda: self._move(1)).pack(side="left", padx=4)
        ctk.CTkButton(bar, text=t("remove_sel"), width=96,
                      command=self._remove).pack(side="left", padx=4)
        self.listbox = tk.Listbox(self, height=6, selectmode="extended")
        self.listbox.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self._refresh()

    # ---- 对外接口 ----
    def paths(self) -> list[Path]:
        """只返回校验通过的文件路径。"""
        return [it["path"] for it in self.items if it["ok"]]

    # ---- 状态 ----
    def _restore(self) -> list[dict]:
        """从面板状态恢复队列；文件已不存在的条目直接丢弃。"""
        if not self._state:
            return []
        items = []
        for it in self._state.get("queue") or []:
            try:
                path = Path(it["path"])
            except (KeyError, TypeError):
                continue
            if not path.exists():
                continue
            items.append({
                "path": path,
                "display": it.get("display", path.name),
                "ok": bool(it.get("ok", True)),
            })
        return items[:self.max_files] if self.max_files else items

    def _persist(self) -> None:
        if self._state is not None:
            self._state["queue"] = [dict(it) for it in self.items]

    # ---- 添加 ----
    def _pick_files(self):
        filetypes = ([("PDF", "*.pdf")] if self.kind == "pdf"
                     else IMAGE_FILE_TYPES)
        for p in filedialog.askopenfilenames(filetypes=filetypes):
            self._add(Path(p))

    def _pick_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self._pick_folder_path(Path(folder))

    def add_paths(self, paths) -> int:
        """外部拖入/批量添加；返回实际加入的数量（目录会展开）。"""
        added = 0
        for p in paths:
            p = Path(p)
            if p.is_dir():
                before = len(self.items)
                self._pick_folder_path(p)
                added += len(self.items) - before
                continue
            if self._accepts(p):
                self._add(p)
                added += 1
        return added

    def _pick_folder_path(self, folder: Path):
        suffix_ok = (lambda p: p.suffix.lower() == ".pdf") if self.kind == "pdf" \
            else (lambda p: p.suffix.lower() in SUPPORTED_SUFFIXES)
        for p in sorted(folder.iterdir()):
            if p.is_file() and suffix_ok(p):
                self._add(p)

    def _accepts(self, path: Path) -> bool:
        if self.kind == "pdf":
            return path.suffix.lower() == ".pdf"
        return path.suffix.lower() in SUPPORTED_SUFFIXES

    def _add(self, path: Path):
        if self.max_files and len(self.items) >= self.max_files:
            self.items.clear()  # 单文件面板：新文件替换旧文件
        self.items.append(self._validate(path))
        self._refresh()

    def _validate(self, path: Path) -> dict:
        if self.kind == "image":
            try:
                with Image.open(path) as im:
                    im.verify()
                return {"path": path, "display": path.name, "ok": True}
            except Exception:
                return {"path": path,
                        "display": f"{path.name}（{t('bad_image')}）", "ok": False}
        try:
            reader = PdfReader(path)
            if reader.is_encrypted:
                pw = self.ask_password(path.name)
                if not pw:
                    return {"path": path, "display": f"{path.name}（{t('wrong_password')}）",
                            "ok": False}
                TEMP_DIR.mkdir(parents=True, exist_ok=True)
                tmp = TEMP_DIR / f"{path.stem}_{uuid.uuid4().hex[:8]}.pdf"
                result = decrypt_pdf(path, tmp, pw)
                if not result.ok:
                    return {"path": path, "display": f"{path.name}（{t('wrong_password')}）",
                            "ok": False}
                return {"path": result.outputs[0],
                        "display": f"{path.name}（{t('decrypted_note')}）", "ok": True}
            return {"path": path, "display": path.name, "ok": True}
        except Exception:
            return {"path": path, "display": f"{path.name}（{t('bad_file')}）", "ok": False}

    # ---- 排序/移除 ----
    def _move(self, delta: int):
        sel = list(self.listbox.curselection())
        if not sel:
            return
        i = sel[0]
        j = i + delta
        if 0 <= j < len(self.items):
            self.items[i], self.items[j] = self.items[j], self.items[i]
            self._refresh()
            self.listbox.selection_set(j)

    def _remove(self):
        for i in reversed(self.listbox.curselection()):
            del self.items[i]
        self._refresh()

    def _refresh(self):
        self.listbox.delete(0, "end")
        for it in self.items:
            self.listbox.insert("end", it["display"])
            if not it["ok"]:
                self.listbox.itemconfig(self.listbox.size() - 1, fg="red")
        if not self.items:
            self.listbox.insert("end", t("queue_empty"))
            self.listbox.itemconfig(self.listbox.size() - 1, fg="gray")
        self._persist()
        if self.on_change:
            self.on_change()
