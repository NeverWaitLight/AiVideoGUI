"""后台清理超时仍处于 pending/running 的生成任务。"""

from loguru import logger

from service.background.task_base import BackgroundTask, TaskType
from storage.repositories.generate_task_repository import GenerateTaskRepository


class StaleTaskCleanupTask(BackgroundTask):
    """周期性将超时未完成的 pending/running 任务标记为失败。"""

    def __init__(
        self,
        session_manager,
        config_manager,
        check_interval: float = 1800.0,
    ):
        super().__init__(TaskType.PERIODIC, "stale_task_cleanup")
        self._sm = session_manager
        self._config = config_manager
        self._check_interval = check_interval
        self.enable()

    def execute(self) -> None:
        try:
            hours = int(getattr(self._config.settings, "stale_task_timeout_hours", 4) or 4)
            hours = max(1, min(168, hours))
            older_than_ms = hours * 60 * 60 * 1000
            error_message = f"任务超时未完成（超过 {hours} 小时）"

            repo = self._sm.get_repo(repo_class=GenerateTaskRepository)
            self._sm.begin_write()
            try:
                n = repo.fail_stale_pending_or_running_tasks(older_than_ms, error_message)
                self._sm.commit_write()
            except Exception:
                self._sm.rollback_write()
                raise

            if n:
                logger.info(f"已将 {n} 个超时 pending/running 任务标记为失败")
            else:
                logger.debug("无超时 pending/running 任务需要清理")
        except Exception as e:
            logger.error(f"超时任务清理失败：{e}")

    def should_continue(self) -> bool:
        return True

    def get_interval(self) -> float:
        return self._check_interval
