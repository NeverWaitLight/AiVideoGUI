"""后台任务调度器：管理所有后台任务的生命周期。"""

from __future__ import annotations

import time
from loguru import logger
from typing import Dict

from PySide6.QtCore import QObject, QThread, Signal

from .task_base import BackgroundTask, TaskExecutor, TaskType


class BackgroundTaskScheduler(QObject):
    """后台任务调度器：管理所有后台任务的生命周期。

    支持两种任务类型：
    1. 周期性任务 - 按固定间隔循环执行，直到应用关闭
    2. 一次性任务 - 被业务逻辑触发后执行一次，完成后自动停止
    """

    # 全局信号（转发所有任务的信号）
    task_started = Signal(str)  # task_name
    task_finished = Signal(str)  # task_name
    task_failed = Signal(str, str)  # task_name, error_message

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tasks: Dict[str, BackgroundTask] = {}  # task_name -> task
        self._worker: _SchedulerWorker | None = None

    def register_task(self, task: BackgroundTask) -> None:
        """注册后台任务。

        Args:
            task: 后台任务实例

        Raises:
            ValueError: 如果任务名称已存在
        """
        if task.name in self._tasks:
            raise ValueError(f"任务名称已存在：{task.name}")

        self._tasks[task.name] = task
        logger.info(f"注册后台任务：{task.name}（类型：{task.task_type.value}）")

    def start(self) -> None:
        """启动调度器（应用启动时调用）。"""
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
        """停止调度器（应用关闭时调用）。"""
        if self._worker is None:
            return

        self._worker.stop()
        self._worker.wait(5000)
        self._worker = None
        logger.info("后台任务调度器已停止")

    def trigger_task(self, task_name: str) -> bool:
        """触发一次性任务执行。

        Args:
            task_name: 任务名称

        Returns:
            True 表示触发成功，False 表示任务不存在或不是一次性任务
        """
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
        """查询任务状态。

        Args:
            task_name: 任务名称

        Returns:
            任务状态字典（包含 name, type, enabled 等信息）
        """
        task = self._tasks.get(task_name)
        if task is None:
            return {"error": "任务不存在"}

        return {
            "name": task.name,
            "type": task.task_type.value,
            "enabled": task.enabled,
        }


class _SchedulerWorker(QThread):
    """调度器工作线程：循环检查并执行任务。"""

    task_started = Signal(str)
    task_finished = Signal(str)
    task_failed = Signal(str, str)

    def __init__(self, tasks: Dict[str, BackgroundTask], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tasks = tasks
        self._stopped = False

    def stop(self) -> None:
        """停止工作线程。"""
        self._stopped = True

    def _interruptible_sleep(self, seconds: float) -> bool:
        """可中断 sleep，每秒检查 _stopped 标志。

        Returns:
            True 表示被中断，False 表示正常完成
        """
        elapsed = 0.0
        while elapsed < seconds:
            if self._stopped:
                return True
            time.sleep(min(1.0, seconds - elapsed))
            elapsed += 1.0
        return False

    def run(self) -> None:
        """主循环：检查并执行所有已启用的任务。"""
        logger.info("调度器工作线程进入主循环")

        while not self._stopped:
            try:
                # 遍历所有任务
                for task_name, task in self._tasks.items():
                    if self._stopped:
                        break

                    # 跳过未启用的任务
                    if not task.enabled:
                        continue

                    # 检查任务是否应该继续执行
                    if not task.should_continue():
                        if task.task_type == TaskType.ONE_TIME:
                            # 一次性任务完成后自动禁用
                            task.disable()
                            logger.info(f"一次性任务 {task_name} 已完成，自动禁用")
                        continue

                    # 执行任务
                    self._execute_task(task)

                    # 周期性任务：等待间隔时间
                    if task.task_type == TaskType.PERIODIC:
                        interval = task.get_interval()
                        if interval > 0 and self._interruptible_sleep(interval):
                            break

                # 主循环轮询间隔（1秒）
                if self._interruptible_sleep(1.0):
                    break

            except Exception as e:
                logger.exception(f"调度器主循环异常：{e}")
                if self._interruptible_sleep(5.0):
                    break

        logger.info("调度器工作线程已退出")

    def _execute_task(self, task: BackgroundTask) -> None:
        """执行单个任务（捕获异常）。"""
        try:
            self.task_started.emit(task.name)
            task.execute()
            self.task_finished.emit(task.name)

            # 一次性任务执行后自动禁用
            if task.task_type == TaskType.ONE_TIME:
                task.disable()

        except Exception as e:
            logger.exception(f"任务 {task.name} 执行失败：{e}")
            self.task_failed.emit(task.name, str(e))

            # 一次性任务失败后也禁用
            if task.task_type == TaskType.ONE_TIME:
                task.disable()
