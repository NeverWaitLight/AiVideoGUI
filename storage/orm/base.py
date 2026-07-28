"""SQLAlchemy ORM 基础设施。"""

from loguru import logger
from typing import Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

# 全局变量
engine: Optional[Engine] = None
SessionLocal: Optional[scoped_session] = None

class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""

    pass

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

    # 注册历史版本自动保存监听器
    from storage.orm.history_listener import setup_history_listeners
    setup_history_listeners()

    logger.info(f"数据库引擎初始化完成：{database_url}")
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

def ensure_columns() -> None:
    """
    为已有表补齐 ORM 中新增但数据库缺失的列。

    SQLite 的 create_all 不会修改已有表结构，此函数通过
    ALTER TABLE ADD COLUMN 自动补齐缺失列。

    Raises:
        RuntimeError: 如果引擎未初始化
    """
    if engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_engine()")

    insp = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in insp.get_table_names():
                continue
            existing = {c["name"] for c in insp.get_columns(table.name)}
            for column in table.columns:
                if column.name not in existing:
                    col_type = column.type.compile(engine.dialect)
                    default = column.default.arg if column.default is not None else "''"
                    if callable(default):
                        default = "''"
                    if isinstance(default, str) and not default.startswith("'"):
                        default = f"'{default}'"
                    stmt = f'ALTER TABLE {table.name} ADD COLUMN {column.name} {col_type} DEFAULT {default} NOT NULL'
                    conn.execute(text(stmt))
                    logger.info(f"补齐列：{table.name}.{column.name}")

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
