"""SQLAlchemy ORM 基础设施。"""

import logging
from typing import Optional

from sqlalchemy import BigInteger, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker


@compiles(BigInteger, "sqlite")
def _compile_bigint_sqlite(type_, compiler, **kw):
    """SQLite 只对 INTEGER PRIMARY KEY 自动递增 ROWID，BIGINT 不行。"""
    return "INTEGER"

logger = logging.getLogger(__name__)

# 全局变量
engine: Optional[Engine] = None
SessionLocal: Optional[scoped_session] = None


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""

    pass


@event.listens_for(Base, "before_insert", propagate=True)
def before_insert_listener(mapper, connection, target):
    """
    插入前自动填充时间戳字段。

    为所有具有 created_at 和 updated_at 字段的实体自动填充当前毫秒时间戳。
    只在字段为 None 或 0 时填充，避免覆盖显式设置的值。

    Args:
        mapper: SQLAlchemy mapper 对象
        connection: 数据库连接
        target: 被插入的实体对象
    """
    from utils.time_utils import now_ms

    now = now_ms()
    if hasattr(target, "created_at"):
        created_at_value = getattr(target, "created_at", None)
        if created_at_value is None or created_at_value == 0:
            target.created_at = now
    if hasattr(target, "updated_at"):
        updated_at_value = getattr(target, "updated_at", None)
        if updated_at_value is None or updated_at_value == 0:
            target.updated_at = now


@event.listens_for(Base, "before_update", propagate=True)
def before_update_listener(mapper, connection, target):
    """
    更新前自动更新 updated_at 字段。

    为所有具有 updated_at 字段的实体自动更新为当前毫秒时间戳。

    Args:
        mapper: SQLAlchemy mapper 对象
        connection: 数据库连接
        target: 被更新的实体对象
    """
    from utils.time_utils import now_ms

    if hasattr(target, "updated_at"):
        target.updated_at = now_ms()


def init_engine(database_url: str, echo: bool = False, **kwargs) -> Engine:
    """
    初始化数据库引擎（应用启动时调用一次）。

    Args:
        database_url: 数据库连接 URL（如 "sqlite:///path/to/db.db"）
        echo: 是否打印 SQL 语句（开发环境可设为 True）
        **kwargs: 传递给 create_engine 的其他参数

    Returns:
        创建的 Engine 实例
    """
    global engine, SessionLocal

    engine = create_engine(
        database_url,
        # SQLite 特定配置
        connect_args={"check_same_thread": False},  # 支持多线程（PyQt6 需要）
        pool_pre_ping=True,  # 自动检测断连
        echo=echo,  # 是否打印 SQL 日志
        **kwargs,
    )

    # 创建线程安全的 Session 工厂
    SessionLocal = scoped_session(
        sessionmaker(
            bind=engine,
            expire_on_commit=False,  # commit 后对象不失效，避免访问属性时重新查询
            autoflush=False,  # 手动控制 flush 时机
        )
    )

    logger.info("数据库引擎初始化完成：%s", database_url)
    return engine


def get_session() -> Session:
    """
    获取当前线程的 Session。

    使用 scoped_session，每个线程自动获取独立的 Session 实例。

    Returns:
        当前线程的 Session

    Raises:
        RuntimeError: 如果引擎未初始化
    """
    if SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用 init_engine()")
    return SessionLocal()


def close_session() -> None:
    """
    关闭当前线程的 Session。

    通常在线程结束时调用，释放数据库连接。
    """
    if SessionLocal:
        SessionLocal.remove()


def create_all_tables() -> None:
    """
    创建所有表（如果不存在）。

    注意：生产环境应使用 Alembic 迁移管理表结构。

    Raises:
        RuntimeError: 如果引擎未初始化
    """
    if engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_engine()")
    Base.metadata.create_all(engine)
    logger.info("数据库表创建完成")


def drop_all_tables() -> None:
    """
    删除所有表（危险操作，仅用于测试）。

    Raises:
        RuntimeError: 如果引擎未初始化
    """
    if engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_engine()")
    Base.metadata.drop_all(engine)
    logger.warning("所有数据库表已删除")
