from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from models.enums import TakeStatus
from storage.repositories.generate_task_repository import GenerateTaskRepository
from storage.session_manager import SessionManager

if TYPE_CHECKING:
    from models.media_file import MediaFile
    from models.storyboard import Storyboard
    from service.media_service import MediaService
    from service.storyboard_take_service import StoryboardTakeService


class PrevShotFrameService:

    def __init__(
        self,
        session_manager: SessionManager,
        take_service: "StoryboardTakeService",
        media_service: "MediaService",
    ) -> None:
        self._sm = session_manager
        self._take_service = take_service
        self._media_service = media_service

    @staticmethod
    def should_use_prev_frame(
        prev_shot: "Storyboard | None",
        current_shot: "Storyboard | None",
        cross_scene: bool,
    ) -> bool:
        if prev_shot is None or current_shot is None:
            return False
        if cross_scene:
            return True
        return prev_shot.scene_id == current_shot.scene_id

    def find_prev_shot_media(self, prev_shot_id: int) -> "MediaFile | None":
        takes = self._take_service.list_by_storyboard(prev_shot_id)
        if not takes:
            return None

        for take in takes:
            if take.status == TakeStatus.SELECTED and take.media_file_id:
                media = self._media_service.get_file_by_id(take.media_file_id)
                if media:
                    return media

        takes_with_media = [t for t in takes if t.media_file_id]
        if not takes_with_media:
            return None

        takes_with_media.sort(key=lambda t: t.number, reverse=True)
        return self._media_service.get_file_by_id(takes_with_media[0].media_file_id)

    def find_prev_pending_provider_task_id(self, prev_shot_id: int) -> str | None:
        takes = self._take_service.list_by_storyboard(prev_shot_id)
        if not takes:
            return None

        task_repo = self._sm.get_repo(GenerateTaskRepository)
        pending_takes = [t for t in takes if not t.media_file_id and t.generate_task_id]
        if not pending_takes:
            return None

        pending_takes.sort(key=lambda t: t.number, reverse=True)
        for take in pending_takes:
            task_info = task_repo.get_task_info(take.generate_task_id)
            if task_info is None:
                continue
            completed, _status = task_info
            if completed:
                continue
            task = task_repo.get_by_id(take.generate_task_id)
            if task and task.get("provider_task_id"):
                return task["provider_task_id"]
        return None

    def get_provider_task_outcome(self, provider_task_id: str) -> tuple[bool, bool] | None:
        task_repo = self._sm.get_repo(GenerateTaskRepository)
        task = task_repo.get_by_provider_task_id(provider_task_id)
        if not task:
            return None
        if not task["completed"]:
            return False, False
        success = (task.get("status") or "") != "failed"
        return True, success

    def resolve_last_frame_path(
        self,
        prev_shot: "Storyboard | None",
        current_shot: "Storyboard | None",
        cross_scene: bool,
    ) -> str | None:
        if not self.should_use_prev_frame(prev_shot, current_shot, cross_scene):
            return None

        media = self.find_prev_shot_media(prev_shot.id)
        if not media:
            return None

        last_frame = self._media_service.ensure_last_frame(media.id)
        if last_frame:
            logger.info(
                "上一镜尾帧已就绪 storyboard_id=%s path=%s",
                prev_shot.id,
                last_frame,
            )
            return last_frame
        return None
