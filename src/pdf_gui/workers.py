"""后台批处理：Job 队列逐个在线程里执行 core 任务，经事件队列回报 UI。

不 import 任何 GUI 库，保证可 pytest。"""

import queue
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .core import TaskResult


@dataclass
class Job:
    func: Callable[..., TaskResult]
    kwargs: dict[str, Any] = field(default_factory=dict)
    label: str = ""


def resolve_conflict(path, rule: str):
    """按重名规则返回可写路径；rule=skip 且已存在时返回 None。"""
    path = Path(path)
    if rule == "overwrite" or not path.exists():
        return path
    if rule == "skip":
        return None
    # rename：同目录下 xxx(1).pdf、xxx(2).pdf …
    stem, suffix = path.stem, path.suffix
    i = 1
    while True:
        cand = path.with_name(f"{stem}({i}){suffix}")
        if not cand.exists():
            return cand
        i += 1


class BatchWorker(threading.Thread):
    """逐个执行 jobs；事件经 events 队列回 UI（见模块 docstring 的协议）。"""

    def __init__(self, jobs: list[Job], events: "queue.Queue[tuple]"):
        super().__init__(daemon=True)
        self.jobs = jobs
        self.events = events
        self.cancelled = threading.Event()

    def cancel(self) -> None:
        self.cancelled.set()

    def run(self) -> None:
        ok_count = fail_count = cancelled_count = 0
        errors: list[tuple[str, str | None]] = []
        for i, job in enumerate(self.jobs):
            if self.cancelled.is_set():
                cancelled_count += 1
                self.events.put(("job_done", i, job.label, "cancelled", None, []))
                continue
            self.events.put(("job_start", i, job.label))

            def progress(done, total, msg, _i=i):
                self.events.put(("job_progress", _i, done, total, msg))

            try:
                result = job.func(progress_cb=progress,
                                  cancel_cb=self.cancelled.is_set, **job.kwargs)
            except Exception as e:  # core 个别入口（如 split_every_n n<1）抛 ValueError
                result = TaskResult(False, [], str(e))
            if result.cancelled:
                cancelled_count += 1
                self.events.put(
                    ("job_done", i, job.label, "cancelled", None, result.outputs))
                break       # 用户已取消：不再开始后续任务
            if result.ok:
                ok_count += 1
                self.events.put(
                    ("job_done", i, job.label, "ok", None, result.outputs))
            else:
                fail_count += 1
                errors.append((job.label, result.error))
                self.events.put(
                    ("job_done", i, job.label, "fail", result.error, []))
        self.events.put(("finish", ok_count, fail_count, cancelled_count, errors))
