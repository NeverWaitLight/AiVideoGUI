import threading
from typing import Dict, Type, TypeVar, Generic, cast

from loguru import logger
from sqlalchemy.orm import Session

from storage.orm.base import get_session

TRepo = TypeVar("TRepo")


class SessionManager:
    def __init__(self, workspace_root: str = ""):
        self._write_lock = threading.RLock()
        self._workspace_root = workspace_root
        logger.debug("SessionManager 初始化完成")

    def get_session(self) -> Session:
        return get_session()

    def get_repo(self, repo_class: Type[TRepo]) -> TRepo:
        # 不缓存 Repository，每次都创建新实例
        # 因为 scoped_session 会自动为每个线程返回独立的 Session
        session = self.get_session()

        from storage.repositories.media_repository import MediaRepository
        from storage.repositories.character_repository import CharacterRepository
        from storage.repositories.storyboard_repository import StoryboardRepository

        if repo_class in (MediaRepository, CharacterRepository, StoryboardRepository):
            repo_instance = repo_class(session, self._workspace_root)
        else:
            repo_instance = repo_class(session)

        logger.debug(f"创建 Repository 实例：{repo_class.__name__}（线程：{threading.current_thread().name}）")
        return cast(TRepo, repo_instance)

    def begin_write(self) -> None:
        self._write_lock.acquire()
        logger.debug(f"获取写锁：{threading.current_thread().name}")

    def commit_write(self) -> None:
        try:
            session = self.get_session()
            session.commit()
            logger.debug(f"提交写操作：{threading.current_thread().name}")
        except Exception:
            try:
                self.get_session().rollback()
            except Exception:
                pass
            raise
        finally:
            self._write_lock.release()

    def rollback_write(self) -> None:
        try:
            session = self.get_session()
            session.rollback()
            logger.warning(f"回滚写操作：{threading.current_thread().name}")
        finally:
            self._write_lock.release()
