"""core 层统一返回类型。"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# 进度回调：(已完成数, 总数, 消息)
ProgressCB = Callable[[int, int, str], None]
# 取消回调：返回 True 表示应尽快停止；长任务应在每页/每组之间检查
CancelCB = Callable[[], bool]


@dataclass
class TaskResult:
    ok: bool
    outputs: list[Path] = field(default_factory=list)
    error: str | None = None
    cancelled: bool = False
