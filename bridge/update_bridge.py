"""更新检查桥接层"""

from PySide6.QtCore import QObject, Slot, Signal, QThread
from service.update_service import UpdateService


class DownloadWorker(QThread):
    """下载更新的后台线程"""

    progress = Signal(int, int)  # downloaded, total
    finished = Signal(str)  # installer_path
    failed = Signal(str)  # error_message

    def __init__(self, update_service: UpdateService, download_url: str):
        super().__init__()
        self._update_service = update_service
        self._download_url = download_url

    def run(self):
        try:
            installer_path = self._update_service.download_update(
                self._download_url,
                progress_callback=lambda downloaded, total: self.progress.emit(downloaded, total)
            )
            if installer_path:
                self.finished.emit(installer_path)
            else:
                self.failed.emit("下载失败，请检查网络连接")
        except Exception as e:
            error_msg = str(e) or f"{type(e).__name__}（无详细信息）"
            self.failed.emit(error_msg)


class UpdateBridge(QObject):
    """更新检查桥接对象"""

    update_available = Signal(str, str, str, str)  # version, download_url, release_notes, html_url
    download_progress = Signal(int, int)  # downloaded, total
    download_finished = Signal(str)  # installer_path
    download_failed = Signal(str)  # error_message

    def __init__(self, update_service: UpdateService):
        super().__init__()
        self._update_service = update_service
        self._download_worker = None

    @Slot()
    def check_update(self):
        """检查更新（在后台线程调用）"""
        try:
            update_info = self._update_service.check_update()
            if update_info:
                self.update_available.emit(
                    update_info["version"],
                    update_info["download_url"],
                    update_info["release_notes"],
                    update_info["html_url"]
                )
        except Exception:
            pass

    @Slot(str)
    def download_update(self, download_url: str):
        """下载更新"""
        if self._download_worker and self._download_worker.isRunning():
            return

        self._download_worker = DownloadWorker(self._update_service, download_url)
        self._download_worker.progress.connect(self.download_progress.emit)
        self._download_worker.finished.connect(self.download_finished.emit)
        self._download_worker.failed.connect(self.download_failed.emit)
        self._download_worker.start()

    @Slot(str, result=bool)
    def install_update(self, installer_path: str) -> bool:
        """启动安装程序"""
        return self._update_service.install_update(installer_path)
