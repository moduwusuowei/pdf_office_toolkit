"""打开输出目录：只在目标非法时返回 False，成功路径不在这里真开资源管理器。"""

from pdf_gui.gui.shell import open_folder


def test_refuses_existing_file(tmp_path):
    target = tmp_path / "not_a_dir.txt"
    target.write_text("x", encoding="utf-8")
    assert open_folder(target) is False


def test_refuses_unwritable_parent(tmp_path):
    blocked = tmp_path / "file"
    blocked.write_text("x", encoding="utf-8")
    assert open_folder(blocked / "sub") is False
