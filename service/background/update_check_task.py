"""后台更新检查任务"""

from PySide6.QtCore import QThread, Signal
from loguru import logger


class UpdateCheckTask(QThread):
    """后台更新检查任务"""

    update_found = Signal(str, str, str, str)  # version, download_url, release_notes, html_url

    def __init__(self, update_service):
        super().__init__()
        self._update_service = update_service
        self._check_interval = 3600  # 每小时检查一次

    def run(self):
        """执行更新检查（启动后延迟 5 秒，避免影响应用启动速度）"""
        try:
            # 延迟 5 秒，避免阻塞应用启动
            self.msleep(5000)

            logger.info("开始后台更新检查")
            update_info = self._update_service.check_update()

            if update_info:
                logger.info(f"发现新版本：{update_info['version']}")
                self.update_found.emit(
                    update_info["version"],
                    update_info["download_url"],
                    update_info["release_notes"],
                    update_info["html_url"]
                )
            else:
                logger.info("当前已是最新版本或版本已被忽略")

        except Exception as e:
            logger.error(f"后台更新检查失败：{e}")
