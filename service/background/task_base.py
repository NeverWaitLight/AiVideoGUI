from __future__ import annotations

import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from PySide6.QtCore import QObject, Signal


class TaskType(Enum):
    PERIODIC = "periodic"
    ONE_TIME = "one_time"


class BackgroundTask(ABC):

    def __init__(self, task_type: TaskType, name: str) -> None:
        self._type = task_type
        self._name = name
        self._enabled = False
        self._sleep_checker: Any = None

    @property
    def task_type(self) -> TaskType:
        return self._type

    @property
    def name(self) -> str:
        return self._name

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def set_sleep_checker(self, checker: Any) -> None:
        self._sleep_checker = checker

    def interruptible_sleep(self, seconds: float) -> bool:
        if self._sleep_checker is not None:
            elapsed = 0.0
            while elapsed < seconds:
                if self._sleep_checker():
                    return True
                time.sleep(min(0.5, seconds - elapsed))
                elapsed += 0.5
            return False
        time.sleep(seconds)
        return False

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def should_continue(self) -> bool:
        pass

    def get_interval(self) -> float:
        return 0.0


class TaskExecutor(QObject):

    task_started = Signal(str)

    task_finished = Signal(str)

    task_failed = Signal(str, str)

    def __init__(self, task: BackgroundTask, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._task = task

    @property
    def task(self) -> BackgroundTask:
        return self._task

    def execute_safely(self) -> None:
        try:
            self.task_started.emit(self._task.name)
            self._task.execute()
            self.task_finished.emit(self._task.name)
        except Exception as e:
            from loguru import logger
            logger.exception(f"任务 {self._task.name} 执行失败：{e}")
            self.task_failed.emit(self._task.name, str(e))
