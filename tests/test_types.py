from pdf_gui.core.types import TaskResult


def test_task_result_defaults():
    r = TaskResult(ok=True)
    assert r.outputs == []
    assert r.error is None


def test_task_result_failure():
    r = TaskResult(ok=False, error="boom")
    assert not r.ok
    assert r.error == "boom"
