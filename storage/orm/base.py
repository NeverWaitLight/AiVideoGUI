from loguru import logger
from typing import Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

engine: Optional[Engine] = None
SessionLocal: Optional[scoped_session] = None

class Base(DeclarativeBase):
    pass

def init_engine(database_url: str, echo: bool = False, **kwargs) -> Engine:
    global engine, SessionLocal

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        echo=echo,
        **kwargs,
    )

    SessionLocal = scoped_session(
        sessionmaker(
            bind=engine,
            expire_on_commit=False,
            autoflush=False,
        )
    )

    from storage.orm.history_listener import setup_history_listeners
    setup_history_listeners()

    logger.info(f"数据库引擎初始化完成：{database_url}")
    return engine

def get_session() -> Session:
    if SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用 init_engine()")
    return SessionLocal()

def close_session() -> None:
    if SessionLocal:
        SessionLocal.remove()

def create_all_tables() -> None:
    if engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_engine()")
    Base.metadata.create_all(engine)
    logger.info("数据库表创建完成")

def ensure_columns() -> None:
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
    if engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_engine()")
    Base.metadata.drop_all(engine)
    logger.warning("所有数据库表已删除")
