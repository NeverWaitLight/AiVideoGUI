"""增强型后台任务调度器 - 支持任务崩溃自动重启和独立线程执行。"""

from __future__ import annotations

import asyncio
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from loguru import logger
from typing import Dict, Optional

from PySide6.QtCore import QObject, QThread, Signal

from .task_base import BackgroundTask, TaskType


class TaskState(Enum):
    """任务运行状态。"""
    IDLE = "idle"           # 空闲（未启动）
    RUNNING = "running"     # 运行中
    CRASHED = "crashed"     # 崩溃
    STOPPED = "stopped"     # 已停止


@dataclass
class TaskStatus:
    """任务状态信息。"""
    name: str
    type: TaskType
    state: TaskState
    thread_id: Optional[int] = None
    start_time: Optional[datetime] = None
    crash_count: int = 0
    last_error: Optional[str] = None


class BackgroundTaskScheduler(QObject):
    """增强型后台任务调度器。

    特性：
    1. 主调度器后台常驻，崩溃自动重启
    2. 每个任务在独立线程中执行
    3. 任务崩溃自动重启（周期性任务）
    4. 支持查询任务状态和健康检查
    """

    # 全局信号
    task_started = Signal(str)  # task_name
    task_finished = Signal(str)  # task_name
    task_failed = Signal(str, str)  # task_name, error_message
    task_crashed = Signal(str, str)  # task_name, error_message
    task_restarted = Signal(str, int)  # task_name, crash_count

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tasks: Dict[str, BackgroundTask] = {}
        self._task_workers: Dict[str, _TaskWorker] = {}
        self._task_status: Dict[str, TaskStatus] = {}
        self._supervisor: Optional[_SupervisorThread] = None
        self._stopped = False

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
        self._task_status[task.name] = TaskStatus(
            name=task.name,
            type=task.task_type,
            state=TaskState.IDLE,
        )
        logger.info(f"注册后台任务：{task.name}（类型：{task.task_type.value}）")

    def start(self) -> None:
        """启动调度器（应用启动时调用）。"""
        if self._supervisor is not None:
            logger.warning("调度器已在运行")
            return

        self._stopped = False
        self._supervisor = _SupervisorThread(self, parent=self)
        self._supervisor.start()
        logger.info("后台任务调度器已启动（守护模式）")

    def shutdown(self) -> None:
        """停止调度器（应用关闭时调用）。"""
        if self._supervisor is None:
            return

        logger.info("正在停止后台任务调度器...")
        self._stopped = True

        # 停止所有任务线程
        for task_name, worker in self._task_workers.items():
            logger.info(f"正在停止任务：{task_name}")
            worker.stop()

        # 等待所有任务线程退出
        for task_name, worker in self._task_workers.items():
            if worker.isRunning():
                worker.wait(3000)
                if worker.isRunning():
                    logger.warning(f"任务 {task_name} 未能在 3 秒内退出")

        # 停止监督线程
        self._supervisor.stop()
        self._supervisor.wait(5000)
        self._supervisor = None

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

    def get_task_status(self, task_name: str) -> Optional[TaskStatus]:
        """查询任务状态。"""
        return self._task_status.get(task_name)

    def get_all_status(self) -> Dict[str, TaskStatus]:
        """获取所有任务状态。"""
        return self._task_status.copy()

    # ========== 内部方法（由 Supervisor 调用） ==========

    def _start_task(self, task_name: str) -> None:
        """启动任务（在独立线程中执行）。"""
        task = self._tasks.get(task_name)
        if task is None:
            return

        # 如果任务已在运行，跳过
        if task_name in self._task_workers and self._task_workers[task_name].isRunning():
            return

        # 创建新的任务工作线程
        worker = _TaskWorker(task, self)
        worker.started_signal.connect(lambda: self._on_task_started(task_name))
        worker.finished_signal.connect(lambda: self._on_task_finished(task_name))
        worker.failed_signal.connect(lambda err: self._on_task_failed(task_name, err))
        worker.crashed_signal.connect(lambda err: self._on_task_crashed(task_name, err))
        worker.start()

        self._task_workers[task_name] = worker
        self._task_status[task_name].state = TaskState.RUNNING
        self._task_status[task_name].start_time = datetime.now()
        # PySide6 使用 currentThread() 而不是 currentThreadId()
        self._task_status[task_name].thread_id = id(worker)

    def _restart_task(self, task_name: str) -> None:
        """重启崩溃的任务。"""
        status = self._task_status.get(task_name)
        if status is None:
            return

        status.crash_count += 1
        logger.warning(f"重启崩溃任务：{task_name}（第 {status.crash_count} 次崩溃）")
        self.task_restarted.emit(task_name, status.crash_count)

        # 清理旧的 worker
        if task_name in self._task_workers:
            old_worker = self._task_workers[task_name]
            if old_worker.isRunning():
                old_worker.stop()
                old_worker.wait(2000)
            del self._task_workers[task_name]

        # 启动新的 worker
        self._start_task(task_name)

    def _on_task_started(self, task_name: str) -> None:
        """任务启动回调。"""
        self.task_started.emit(task_name)

    def _on_task_finished(self, task_name: str) -> None:
        """任务完成回调。"""
        status = self._task_status.get(task_name)
        if status:
            status.state = TaskState.IDLE
        self.task_finished.emit(task_name)

    def _on_task_failed(self, task_name: str, error: str) -> None:
        """任务失败回调。"""
        status = self._task_status.get(task_name)
        if status:
            status.state = TaskState.IDLE
            status.last_error = error
        self.task_failed.emit(task_name, error)

    def _on_task_crashed(self, task_name: str, error: str) -> None:
        """任务崩溃回调。"""
        status = self._task_status.get(task_name)
        if status:
            status.state = TaskState.CRASHED
            status.last_error = error
        self.task_crashed.emit(task_name, error)
        logger.error(f"任务崩溃：{task_name} - {error}")


class _SupervisorThread(QThread):
    """监督线程：监控所有任务的健康状态，崩溃自动重启。"""

    def __init__(self, scheduler: BackgroundTaskScheduler, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._scheduler = scheduler
        self._stopped = False

    def stop(self) -> None:
        """停止监督线程。"""
        self._stopped = True

    def run(self) -> None:
        """主循环：监控任务状态，启动/重启任务。"""
        logger.info("监督线程进入主循环")

        while not self._stopped:
            try:
                # 遍历所有已注册的任务
                for task_name, task in self._scheduler._tasks.items():
                    if self._stopped:
                        break

                    # 跳过未启用的任务
                    if not task.enabled:
                        continue

                    status = self._scheduler._task_status.get(task_name)
                    if status is None:
                        continue

                    # 周期性任务：如果崩溃，自动重启
                    if task.task_type == TaskType.PERIODIC:
                        if status.state == TaskState.CRASHED:
                            self._scheduler._restart_task(task_name)
                        elif status.state == TaskState.IDLE:
                            # 首次启动
                            self._scheduler._start_task(task_name)

                    # 一次性任务：仅在启用且空闲时启动
                    elif task.task_type == TaskType.ONE_TIME:
                        if status.state == TaskState.IDLE:
                            self._scheduler._start_task(task_name)

                # 监督循环间隔（2 秒检查一次）
                time.sleep(2)

            except Exception as e:
                logger.exception(f"监督线程异常：{e}")
                time.sleep(5)

        logger.info("监督线程已退出")


class _TaskWorker(QThread):
    """任务工作线程：在独立线程中执行任务。"""

    started_signal = Signal()
    finished_signal = Signal()
    failed_signal = Signal(str)  # error_message
    crashed_signal = Signal(str)  # error_message

    def __init__(self, task: BackgroundTask, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._task = task
        self._stopped = False

    def stop(self) -> None:
        """停止任务线程。"""
        self._stopped = True

    def run(self) -> None:
        """执行任务。"""
        try:
            self.started_signal.emit()
            logger.debug(f"任务线程启动：{self._task.name} (Worker ID: {id(self)})")

            # 周期性任务：循环执行
            if self._task.task_type == TaskType.PERIODIC:
                while not self._stopped and self._task.should_continue():
                    try:
                        self._task.execute()
                    except Exception as e:
                        logger.exception(f"任务 {self._task.name} 执行异常：{e}")
                        self.failed_signal.emit(str(e))

                    # 等待间隔时间
                    interval = self._task.get_interval()
                    if interval > 0:
                        self._interruptible_sleep(interval)

                self.finished_signal.emit()

            # 一次性任务：执行一次
            elif self._task.task_type == TaskType.ONE_TIME:
                self._task.execute()
                self._task.disable()  # 执行完成后禁用
                self.finished_signal.emit()

        except Exception as e:
            # 任务崩溃（未捕获的异常）
            error_msg = f"{e}\n{traceback.format_exc()}"
            logger.exception(f"任务 {self._task.name} 崩溃：{e}")
            self.crashed_signal.emit(error_msg)

    def _interruptible_sleep(self, seconds: float) -> None:
        """可中断 sleep。"""
        elapsed = 0.0
        while elapsed < seconds and not self._stopped:
            time.sleep(min(1.0, seconds - elapsed))
            elapsed += 1.0
