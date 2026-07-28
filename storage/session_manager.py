"""线程安全的 Session 和 Repository 管理器。

提供统一的数据库访问接口，管理 Session 生命周期和 Repository 实例缓存。
"""

import threading
from typing import Dict, Type, TypeVar, Generic, cast

from loguru import logger
from sqlalchemy.orm import Session

from storage.orm.base import get_session

# 泛型变量，表示任意 Repository 类型
TRepo = TypeVar("TRepo")


class SessionManager:
    """
    线程安全的 Session 和 Repository 管理器。

    职责：
    1. 提供当前线程的 Session 访问
    2. 缓存 Repository 实例（按类型，避免重复创建）
    3. 管理写操作锁（确保 SQLite 写入串行化）

    使用方式：
        session_mgr = SessionManager()

        # 读操作（无需加锁）
        conv_repo = session_mgr.get_repo(ConversationRepository)
        conversations = conv_repo.list_by_project(project_id)

        # 写操作（需要加锁）
        session_mgr.begin_write()
        try:
            conv_repo.save(conversation)
            session_mgr.commit_write()
        except Exception as e:
            session_mgr.rollback_write()
            raise
    """

    def __init__(self):
        """初始化 SessionManager。"""
        # 写操作锁（递归锁，允许同一线程多次获取）
        self._write_lock = threading.RLock()

        # Repository 实例缓存（按类型）
        # 键：Repository 类型，值：Repository 实例
        self._repo_cache: Dict[Type, object] = {}

        # 缓存锁（保护 _repo_cache 字典的并发访问）
        self._cache_lock = threading.Lock()

        logger.debug("SessionManager 初始化完成")

    def get_session(self) -> Session:
        """
        获取当前线程的 Session。

        内部调用 storage.orm.base.get_session()，该函数使用 scoped_session
        确保每个线程获取独立的 Session 实例。

        Returns:
            当前线程的 Session

        Raises:
            RuntimeError: 如果数据库引擎未初始化
        """
        return get_session()

    def get_repo(self, repo_class: Type[TRepo]) -> TRepo:
        """
        获取缓存的 Repository 实例（类型安全）。

        如果实例不存在，则创建并缓存。Repository 实例在创建时绑定到当前
        线程的 Session（通过 scoped_session 自动管理）。

        Args:
            repo_class: Repository 类（如 ConversationRepository）

        Returns:
            Repository 实例

        Example:
            conv_repo = session_mgr.get_repo(ConversationRepository)
            conversations = conv_repo.list_by_project(project_id)
        """
        with self._cache_lock:
            if repo_class not in self._repo_cache:
                # 创建 Repository 实例，传入当前线程的 Session
                session = self.get_session()
                repo_instance = repo_class(session)
                self._repo_cache[repo_class] = repo_instance
                logger.debug(f"创建并缓存 Repository 实例：{repo_class.__name__}")

            # cast 确保类型推断正确（从 object 转换为 TRepo）
            return cast(TRepo, self._repo_cache[repo_class])

    def begin_write(self) -> None:
        """
        开始写操作（获取写锁）。

        SQLite 在 WAL 模式下支持多读一写，但写操作必须串行化。
        调用此方法后，当前线程获取写锁，其他线程的写操作将阻塞。

        使用递归锁（RLock），允许同一线程多次调用 begin_write()。

        Example:
            session_mgr.begin_write()
            try:
                # 执行多个写操作
                conv_repo.save(conversation)
                msg_repo.save(message)
                session_mgr.commit_write()
            except Exception:
                session_mgr.rollback_write()
                raise
        """
        self._write_lock.acquire()
        logger.debug(f"获取写锁：{threading.current_thread().name}")

    def commit_write(self) -> None:
        """
        提交写操作并释放写锁。

        提交当前线程的 Session 事务，然后释放写锁，允许其他线程执行写操作。

        Raises:
            RuntimeError: 如果当前线程未持有写锁
        """
        try:
            session = self.get_session()
            session.commit()
            logger.debug(f"提交写操作：{threading.current_thread().name}")
        finally:
            self._write_lock.release()

    def rollback_write(self) -> None:
        """
        回滚写操作并释放写锁。

        回滚当前线程的 Session 事务，丢弃未提交的更改，然后释放写锁。

        Raises:
            RuntimeError: 如果当前线程未持有写锁
        """
        try:
            session = self.get_session()
            session.rollback()
            logger.warning(f"回滚写操作：{threading.current_thread().name}")
        finally:
            self._write_lock.release()

    def clear_cache(self) -> None:
        """
        清空 Repository 缓存。

        通常用于测试或需要强制重新创建 Repository 实例的场景。
        生产环境不应调用此方法。
        """
        with self._cache_lock:
            self._repo_cache.clear()
            logger.debug("Repository 缓存已清空")
