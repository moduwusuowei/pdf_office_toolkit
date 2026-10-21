"""文件队列控件：添加/排序/移除 PDF，逐个校验；加密文件提示输密码并临时解密。"""

import tempfile
import tkinter as tk
import uuid
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from pypdf import PdfReader

from ...core import decrypt_pdf
from ..i18n import t

TEMP_DIR = Path(tempfile.gettempdir()) / "pdf_office_toolkit"


class FileQueue(ctk.CTkFrame):
    def __init__(self, master, *, max_files=0, ask_password, on_change=None,
                 state=None):
        super().__init__(master)
        # state 存在时队列随面板重建保留（切换语言/配色不会清空用户添加的文件）
        self._state = state
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
        for p in filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")]):
            self._add(Path(p))

    def _pick_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            for p in sorted(Path(folder).glob("*.pdf")):
                self._add(p)

    def _add(self, path: Path):
        if self.max_files and len(self.items) >= self.max_files:
            self.items.clear()  # 单文件面板：新文件替换旧文件
        self.items.append(self._validate(path))
        self._refresh()

    def _validate(self, path: Path) -> dict:
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
