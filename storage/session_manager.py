import threading
from typing import Dict, Type, TypeVar, Generic, cast

from loguru import logger
from sqlalchemy.orm import Session

from storage.orm.base import get_session

TRepo = TypeVar("TRepo")


class SessionManager:
    def __init__(self, workspace_root: str = ""):
        self._write_lock = threading.RLock()
        self._repo_cache: Dict[Type, object] = {}
        self._cache_lock = threading.Lock()
        self._workspace_root = workspace_root
        logger.debug("SessionManager 初始化完成")

    def get_session(self) -> Session:
        return get_session()

    def get_repo(self, repo_class: Type[TRepo]) -> TRepo:
        with self._cache_lock:
            if repo_class not in self._repo_cache:
                session = self.get_session()

                from storage.repositories.media_repository import MediaRepository
                from storage.repositories.character_repository import CharacterRepository
                from storage.repositories.storyboard_repository import StoryboardRepository

                if repo_class in (MediaRepository, CharacterRepository, StoryboardRepository):
                    repo_instance = repo_class(session, self._workspace_root)
                else:
                    repo_instance = repo_class(session)

                self._repo_cache[repo_class] = repo_instance
                logger.debug(f"创建并缓存 Repository 实例：{repo_class.__name__}")

            return cast(TRepo, self._repo_cache[repo_class])

    def begin_write(self) -> None:
        self._write_lock.acquire()
        logger.debug(f"获取写锁：{threading.current_thread().name}")

    def commit_write(self) -> None:
        try:
            session = self.get_session()
            session.commit()
            logger.debug(f"提交写操作：{threading.current_thread().name}")
        finally:
            self._write_lock.release()

    def rollback_write(self) -> None:
        try:
            session = self.get_session()
            session.rollback()
            logger.warning(f"回滚写操作：{threading.current_thread().name}")
        finally:
            self._write_lock.release()

    def clear_cache(self) -> None:
        with self._cache_lock:
            self._repo_cache.clear()
            logger.debug("Repository 缓存已清空")
