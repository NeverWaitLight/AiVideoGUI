from __future__ import annotations

from datetime import datetime

from loguru import logger

from models.visual_style import VisualStyle
from storage.repositories.visual_style_repository import VisualStyleRepository
from storage.session_manager import SessionManager


class VisualStyleService:

    def __init__(self, session_manager: SessionManager):
        self._sm = session_manager

    def create_style(self, name: str, is_default: bool = False, sample_image_path: str = "") -> VisualStyle | None:
        style_repo = self._sm.get_repo(repo_class=VisualStyleRepository)

        if style_repo.exists_by_name(name):
            logger.warning(f"风格名称已存在：{name}")
            return None

        now_ts = int(datetime.now().timestamp() * 1000)
        style = VisualStyle(
            id=0,
            name=name,
            is_default=is_default,
            sample_image_path=sample_image_path,
            created_at=now_ts,
            updated_at=now_ts,
        )

        self._sm.begin_write()
        try:
            if is_default:
                style_repo.clear_all_defaults()

            saved_style = style_repo.save(style)
            self._sm.commit_write()
            return saved_style
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"创建风格失败: {e}")
            raise

    def list_styles(self) -> list[VisualStyle]:
        style_repo = self._sm.get_repo(repo_class=VisualStyleRepository)
        return style_repo.list_all()

    def get_style(self, style_id: int) -> VisualStyle | None:
        style_repo = self._sm.get_repo(repo_class=VisualStyleRepository)
        return style_repo.get_by_id(style_id)

    def get_default_style(self) -> VisualStyle | None:
        style_repo = self._sm.get_repo(repo_class=VisualStyleRepository)
        return style_repo.get_default_style()

    def update_style(
        self, style_id: int, name: str, is_default: bool, sample_image_path: str
    ) -> bool:
        style_repo = self._sm.get_repo(repo_class=VisualStyleRepository)

        if style_repo.exists_by_name(name=name, exclude_id=style_id):
            logger.warning(f"风格名称已存在：{name}")
            return False

        self._sm.begin_write()
        try:
            if is_default:
                style_repo.clear_all_defaults()

            style_repo.update_style(
                style_id=style_id,
                name=name,
                is_default=is_default,
                sample_image_path=sample_image_path,
            )
            self._sm.commit_write()
            return True
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"更新风格失败: {e}")
            raise

    def delete_style(self, style_id: int) -> None:
        style_repo = self._sm.get_repo(repo_class=VisualStyleRepository)

        self._sm.begin_write()
        try:
            style_repo.delete(style_id)
            self._sm.commit_write()
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"删除风格失败: {e}")
            raise
