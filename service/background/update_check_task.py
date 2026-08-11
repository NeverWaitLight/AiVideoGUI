"""后台更新检查任务"""

from loguru import logger
from PySide6.QtCore import QObject, Signal

from service.background.task_base import BackgroundTask, TaskType


class UpdateCheckTask(BackgroundTask):
    """后台更新检查任务（改造为 BackgroundTask）"""

    def __init__(self, update_service, check_interval: float = 3600.0):
        super().__init__(TaskType.PERIODIC, "update_check")
        self._update_service = update_service
        self._check_interval = check_interval
        self._first_run = True
        self._signal_emitter = _SignalEmitter()

    @property
    def signal_emitter(self) -> QObject:
        return self._signal_emitter

    def execute(self) -> None:
        """执行更新检查"""
        try:
            if self._first_run:
                logger.info("开始后台更新检查")
                self._first_run = False

            update_info = self._update_service.check_update()

            if update_info:
                logger.info(f"发现新版本：{update_info['version']}")
                self._signal_emitter.update_found.emit(
                    update_info["version"],
                    update_info["download_url"],
                    update_info["release_notes"],
                    update_info["html_url"]
                )
            else:
                logger.debug("当前已是最新版本或版本已被忽略")

        except Exception as e:
            logger.error(f"后台更新检查失败：{e}")

    def should_continue(self) -> bool:
        """持续运行"""
        return True

    def get_interval(self) -> float:
        """返回检查间隔（秒）"""
        return self._check_interval


class _SignalEmitter(QObject):
    """信号发射器（线程安全）"""

    update_found = Signal(str, str, str, str)  # version, download_url, release_notes, html_url
