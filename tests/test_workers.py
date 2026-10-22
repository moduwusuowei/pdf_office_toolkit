import queue
from pathlib import Path

from pdf_gui.core import TaskResult
from pdf_gui.workers import BatchWorker, Job, resolve_conflict


def _drain(q):
    out = []
    while not q.empty():
        out.append(q.get_nowait())
    return out


def _ok_job(**kw):
    kw["progress_cb"](1, 2, "m1")
    kw["progress_cb"](2, 2, "m2")
    return TaskResult(True, [Path("out.pdf")], None)


def test_resolve_conflict_rename(tmp_path):
    p = tmp_path / "a.pdf"
    p.write_text("x", encoding="utf-8")
    assert resolve_conflict(p, "rename") == tmp_path / "a(1).pdf"


def test_resolve_conflict_overwrite(tmp_path):
    p = tmp_path / "a.pdf"
    p.write_text("x", encoding="utf-8")
    assert resolve_conflict(p, "overwrite") == p


def test_resolve_conflict_skip_existing(tmp_path):
    p = tmp_path / "a.pdf"
    p.write_text("x", encoding="utf-8")
    assert resolve_conflict(p, "skip") is None


def test_resolve_conflict_skip_missing(tmp_path):
    p = tmp_path / "a.pdf"
    assert resolve_conflict(p, "skip") == p


def test_resolve_conflict_rename_fills_gaps(tmp_path):
    (tmp_path / "a.pdf").write_text("x", encoding="utf-8")
    (tmp_path / "a(1).pdf").write_text("x", encoding="utf-8")
    assert resolve_conflict(tmp_path / "a.pdf", "rename") == tmp_path / "a(2).pdf"


def test_worker_emits_full_protocol():
    q = queue.Queue()
    BatchWorker([Job(_ok_job, label="job-a")], q).run()
    events = _drain(q)
    kinds = [e[0] for e in events]
    assert kinds == ["job_start", "job_progress", "job_progress", "job_done", "finish"]
    assert events[0] == ("job_start", 0, "job-a")
    assert events[1] == ("job_progress", 0, 1, 2, "m1")
    assert events[3] == ("job_done", 0, "job-a", "ok", None, [Path("out.pdf")])
    assert events[4][:4] == ("finish", 1, 0, 0)
    assert events[4][4] == []


def test_worker_func_exception_counts_fail():
    def boom(**kw):
        raise ValueError("炸了")

    q = queue.Queue()
    BatchWorker([Job(boom, label="b")], q).run()
    events = _drain(q)
    done = events[1]
    assert done[0] == "job_done" and done[3] == "fail"
    assert "炸了" in done[4]
    assert events[2][:4] == ("finish", 0, 1, 0)
    assert events[2][4] == [("b", done[4])]


def test_worker_cancel_skips_remaining():
    holder = {}

    def second(**kw):
        holder["w"].cancel()
        return TaskResult(False, [], "出错")

    def third(**kw):
        raise AssertionError("已取消后不应执行")

    q = queue.Queue()
    w = BatchWorker(
        [Job(_ok_job, label="a"), Job(second, label="b"), Job(third, label="c")], q)
    holder["w"] = w
    w.run()
    events = _drain(q)
    dones = [e for e in events if e[0] == "job_done"]
    assert [d[3] for d in dones] == ["ok", "fail", "cancelled"]
    assert dones[2][4] is None  # cancelled 任务无 error
    finish = events[-1]
    assert finish[0] == "finish"
    assert finish[1:4] == (1, 1, 1)
    assert finish[4] == [("b", "出错")]


def test_worker_stops_when_core_reports_cancelled():
    def cancels(**kw):
        assert callable(kw["cancel_cb"])
        return TaskResult(False, [], "已取消", cancelled=True)

    def never(**kw):
        raise AssertionError("任务已取消，不应继续执行")

    q = queue.Queue()
    BatchWorker([Job(cancels, label="a"), Job(never, label="b")], q).run()
    events = _drain(q)
    dones = [e for e in events if e[0] == "job_done"]
    assert len(dones) == 1 and dones[0][3] == "cancelled"
    assert events[-1][:4] == ("finish", 0, 0, 1)
