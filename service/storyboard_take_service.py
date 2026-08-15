import time

from loguru import logger

from models.enums import TakeStatus
from models.storyboard_take import StoryboardTake
from storage.session_manager import SessionManager
from storage.repositories.generate_task_repository import GenerateTaskRepository
from storage.repositories.storyboard_take_repository import StoryboardTakeRepository


class StoryboardTakeService:

    def __init__(self, session_mgr: SessionManager) -> None:
        self._session_mgr = session_mgr

    def list_by_storyboard(self, storyboard_id: int) -> list[StoryboardTake]:
        repo = self._session_mgr.get_repo(repo_class=StoryboardTakeRepository)
        return repo.list_by_storyboard(storyboard_id)

    def get_max_number(self, storyboard_id: int) -> int:
        repo = self._session_mgr.get_repo(repo_class=StoryboardTakeRepository)
        return repo.get_max_number(storyboard_id)

    def create_take(
        self,
        storyboard_id: int,
        media_file_id: str = "",
        generate_task_id: int = 0,
        comment: str = "",
        number: int | None = None,
    ) -> StoryboardTake:
        repo = self._session_mgr.get_repo(repo_class=StoryboardTakeRepository)

        now_ms = int(time.time() * 1000)
        if number is None:
            number = repo.get_next_number(storyboard_id)

        take = StoryboardTake(
            storyboard_id=storyboard_id,
            number=number,
            media_file_id=media_file_id or "",
            generate_task_id=generate_task_id,
            status=TakeStatus.CANDIDATE,
            comment=comment,
            created_at=now_ms,
            updated_at=now_ms,
        )

        self._session_mgr.begin_write()
        try:
            created = repo.create(dto=take)
            self._session_mgr.commit_write()
            logger.info(
                f"创建拍摄记录：storyboard_id={storyboard_id}, number={number}, "
                f"generate_task_id={generate_task_id}, media_file_id={media_file_id or ''}"
            )
            return created
        except Exception:
            self._session_mgr.rollback_write()
            raise

    def bind_media_by_provider_task_id(self, provider_task_id: str, media_file_id: str) -> bool:
        """视频完成后，按 provider_task_id 找到 take 并回填 media_file_id。"""
        task_repo = self._session_mgr.get_repo(repo_class=GenerateTaskRepository)
        task = task_repo.get_by_provider_task_id(provider_task_id)
        if not task:
            logger.warning(f"绑定媒体失败：找不到 generate_task provider_task_id={provider_task_id}")
            return False

        take_repo = self._session_mgr.get_repo(repo_class=StoryboardTakeRepository)
        take = take_repo.get_by_generate_task_id(task["id"])
        if not take:
            logger.warning(f"绑定媒体失败：找不到 take generate_task_id={task['id']}")
            return False

        self._session_mgr.begin_write()
        try:
            take.media_file_id = media_file_id
            take.updated_at = int(time.time() * 1000)
            take_repo.update(dto=take)
            self._session_mgr.commit_write()
            logger.info(
                f"回填拍摄媒体：take_id={take.id}, generate_task_id={task['id']}, media_file_id={media_file_id}"
            )
            return True
        except Exception:
            self._session_mgr.rollback_write()
            raise

    def update_status(self, take_id: int, status: TakeStatus) -> None:
        repo = self._session_mgr.get_repo(repo_class=StoryboardTakeRepository)

        self._session_mgr.begin_write()
        try:
            take = repo.get_by_id(take_id)
            if not take:
                raise ValueError(f"拍摄记录不存在：{take_id}")

            take.status = status
            take.updated_at = int(time.time() * 1000)
            repo.update(dto=take)
            self._session_mgr.commit_write()
            logger.info(f"更新拍摄记录状态：take_id={take_id}, status={status.value}")
        except Exception:
            self._session_mgr.rollback_write()
            raise

    def delete_take(self, take_id: int) -> None:
        repo = self._session_mgr.get_repo(repo_class=StoryboardTakeRepository)

        self._session_mgr.begin_write()
        try:
            repo.delete(take_id)
            self._session_mgr.commit_write()
            logger.info(f"删除拍摄记录：take_id={take_id}")
        except Exception:
            self._session_mgr.rollback_write()
            raise

    def list_selected_by_project(self, project_id: int) -> list[StoryboardTake]:
        repo = self._session_mgr.get_repo(repo_class=StoryboardTakeRepository)
        return repo.list_selected_by_project(project_id)
