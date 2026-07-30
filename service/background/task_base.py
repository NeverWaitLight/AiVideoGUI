"""后台任务抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from PySide6.QtCore import QObject, Signal


class TaskType(Enum):
    """任务类型枚举。"""
    PERIODIC = "periodic"  # 周期性任务（死循环 + 间隔时间）
    ONE_TIME = "one_time"  # 一次性任务（被业务逻辑触发，执行完成后停止）


class BackgroundTask(ABC):
    """后台任务抽象基类。

    所有后台任务必须继承此类并实现抽象方法。
    """

    def __init__(self, task_type: TaskType, name: str) -> None:
        """初始化后台任务。

        Args:
            task_type: 任务类型（周期性/一次性）
            name: 任务名称（用于日志和状态跟踪）
        """
        self._type = task_type
        self._name = name
        self._enabled = False  # 任务是否被启用

    @property
    def task_type(self) -> TaskType:
        """返回任务类型。"""
        return self._type

    @property
    def name(self) -> str:
        """返回任务名称。"""
        return self._name

    @property
    def enabled(self) -> bool:
        """返回任务是否被启用。"""
        return self._enabled

    def enable(self) -> None:
        """启用任务（一次性任务需要每次被业务逻辑手动启用）。"""
        self._enabled = True

    def disable(self) -> None:
        """禁用任务。"""
        self._enabled = False

    @abstractmethod
    def execute(self) -> None:
        """执行任务的具体逻辑（由子类实现）。

        注意：此方法在后台线程中执行，不要直接操作 UI。
        """
        pass

    @abstractmethod
    def should_continue(self) -> bool:
        """判断任务是否应该继续执行（周期性任务用于控制循环，一次性任务用于判断是否完成）。

        Returns:
            True 表示任务应该继续执行，False 表示任务应该停止
        """
        pass

    def get_interval(self) -> float:
        """返回周期性任务的执行间隔（秒）。

        一次性任务默认返回 0（立即执行）。

        Returns:
            执行间隔（秒）
        """
        return 0.0


class TaskExecutor(QObject):
    """任务执行器：包装任务执行逻辑，提供信号通信。"""

    # 信号：任务开始执行
    task_started = Signal(str)  # task_name

    # 信号：任务执行完成
    task_finished = Signal(str)  # task_name

    # 信号：任务执行失败
    task_failed = Signal(str, str)  # task_name, error_message

    def __init__(self, task: BackgroundTask, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._task = task

    @property
    def task(self) -> BackgroundTask:
        """返回关联的任务对象。"""
        return self._task

    def execute_safely(self) -> None:
        """安全地执行任务（捕获异常并通过信号通知）。"""
        try:
            self.task_started.emit(self._task.name)
            self._task.execute()
            self.task_finished.emit(self._task.name)
        except Exception as e:
            from loguru import logger
            logger.exception(f"任务 {self._task.name} 执行失败：{e}")
            self.task_failed.emit(self._task.name, str(e))
