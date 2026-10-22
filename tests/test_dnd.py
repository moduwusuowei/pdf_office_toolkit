"""拖拽入队的路径解析与降级路径（不真开窗口、不真拖文件）。"""

import sys
import tkinter
import types

from pdf_gui.gui import dnd


def test_decode_keeps_str():
    assert dnd._decode("D:/文档/a.pdf") == "D:/文档/a.pdf"


def test_decode_utf8_bytes():
    assert dnd._decode("报告.pdf".encode()) == "报告.pdf"


def test_decode_ansi_bytes(monkeypatch):
    # 系统代码页不是中文时（如 cp1252）任何字节都能解出来，这里强制退回 gbk
    monkeypatch.setattr(dnd.locale, "getpreferredencoding", lambda *a: "ascii")
    assert dnd._decode("报告.pdf".encode("gbk")) == "报告.pdf"


def test_split_paths_handles_spaces_and_unicode():
    tcl = tkinter.Tcl()
    data = "{C:/My Files/a.pdf} D:/报告.pdf"
    assert dnd.split_paths(tcl, data) == ["C:/My Files/a.pdf", "D:/报告.pdf"]


def test_split_paths_falls_back_when_not_a_list():
    class Bad:
        def splitlist(self, data):
            raise ValueError("not a list")

    assert dnd.split_paths(Bad(), "C:/a.pdf") == ["C:/a.pdf"]


def test_enable_drop_without_tkinterdnd2(monkeypatch):
    monkeypatch.setitem(sys.modules, "tkinterdnd2", None)  # import 时抛 ImportError
    assert dnd.enable_drop(types.SimpleNamespace(), lambda paths: None) is False


def test_enable_drop_survives_tkdnd_load_failure(monkeypatch):
    fake = types.ModuleType("tkinterdnd2")

    class FakeTkinterDnD:
        class DnDWrapper:
            pass

        @staticmethod
        def _require(root):
            raise RuntimeError("Unable to load tkdnd library.")

    fake.DND_FILES = "DND_Files"
    fake.TkinterDnD = FakeTkinterDnD
    monkeypatch.setitem(sys.modules, "tkinterdnd2", fake)
    widget = types.SimpleNamespace(
        _w=".w", tk=None, nametowidget=None, _register=None)
    assert dnd.enable_drop(widget, lambda paths: None) is False
