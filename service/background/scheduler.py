from __future__ import annotations

import time
from loguru import logger
from typing import Dict

from PySide6.QtCore import QObject, QThread, Signal

from .task_base import BackgroundTask, TaskExecutor, TaskType


class BackgroundTaskScheduler(QObject):

    task_started = Signal(str)
    task_finished = Signal(str)
    task_failed = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tasks: Dict[str, BackgroundTask] = {}
        self._worker: _SchedulerWorker | None = None

    def register_task(self, task: BackgroundTask) -> None:
        if task.name in self._tasks:
            raise ValueError(f"任务名称已存在：{task.name}")

        self._tasks[task.name] = task
        logger.info(f"注册后台任务：{task.name}（类型：{task.task_type.value}）")

    def start(self) -> None:
        if self._worker is not None:
            logger.warning("调度器已在运行")
            return

        self._worker = _SchedulerWorker(self._tasks, parent=self)
        self._worker.task_started.connect(self.task_started)
        self._worker.task_finished.connect(self.task_finished)
        self._worker.task_failed.connect(self.task_failed)
        self._worker.start()
        logger.info("后台任务调度器已启动")

    def shutdown(self) -> None:
        if self._worker is None:
            return

        self._worker.stop()
        self._worker.wait(5000)
        self._worker = None
        logger.info("后台任务调度器已停止")

    def trigger_task(self, task_name: str) -> bool:
        task = self._tasks.get(task_name)
        if task is None:
            logger.warning(f"任务不存在：{task_name}")
            return False

        if task.task_type != TaskType.ONE_TIME:
            logger.warning(f"任务 {task_name} 不是一次性任务，无法手动触发")
            return False

        task.enable()
        logger.info(f"触发一次性任务：{task_name}")
        return True

    def get_task_status(self, task_name: str) -> dict[str, any]:
        task = self._tasks.get(task_name)
        if task is None:
            return {"error": "任务不存在"}

        return {
            "name": task.name,
            "type": task.task_type.value,
            "enabled": task.enabled,
        }


class _SchedulerWorker(QThread):

    task_started = Signal(str)
    task_finished = Signal(str)
    task_failed = Signal(str, str)

    def __init__(self, tasks: Dict[str, BackgroundTask], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tasks = tasks
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True

    def _interruptible_sleep(self, seconds: float) -> bool:
        elapsed = 0.0
        while elapsed < seconds:
            if self._stopped:
                return True
            time.sleep(min(1.0, seconds - elapsed))
            elapsed += 1.0
        return False

    def run(self) -> None:
        logger.info("调度器工作线程进入主循环")

        while not self._stopped:
            try:
                for task_name, task in self._tasks.items():
                    if self._stopped:
                        break

                    if not task.enabled:
                        continue

                    if not task.should_continue():
                        if task.task_type == TaskType.ONE_TIME:
                            task.disable()
                            logger.info(f"一次性任务 {task_name} 已完成，自动禁用")
                        continue

                    self._execute_task(task)

                    if task.task_type == TaskType.PERIODIC:
                        interval = task.get_interval()
                        if interval > 0 and self._interruptible_sleep(interval):
                            break

                if self._interruptible_sleep(1.0):
                    break

            except Exception as e:
                logger.exception(f"调度器主循环异常：{e}")
                if self._interruptible_sleep(5.0):
                    break

        logger.info("调度器工作线程已退出")

    def _execute_task(self, task: BackgroundTask) -> None:
        try:
            self.task_started.emit(task.name)
            task.execute()
            self.task_finished.emit(task.name)

            if task.task_type == TaskType.ONE_TIME:
                task.disable()

        except Exception as e:
            logger.exception(f"任务 {task.name} 执行失败：{e}")
            self.task_failed.emit(task.name, str(e))

            if task.task_type == TaskType.ONE_TIME:
                task.disable()
