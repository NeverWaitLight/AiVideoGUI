from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.orm.base import Base
from storage.orm.project_entity import ProjectEntity, GenerateTaskEntity
from storage.orm.media_entity import MediaFileEntity
from storage.orm.story_outline_entity import StoryOutlineEntity, StoryOutlineHistoryEntity
from storage.orm.screenplay_entity import ScreenplayEntity, ScreenplayHistoryEntity
from storage.orm.storyboard_entity import StoryboardEntity, StoryboardHistoryEntity
from storage.orm.storyboard_take_entity import StoryboardTakeEntity
from storage.orm.character_entity import CharacterEntity, CharacterHistoryEntity
from storage.orm.visual_style_entity import VisualStyleEntity
from storage.orm.oss_cache_entity import OSSFileCacheEntity

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})

    # 如果配置中没有设置 URL，使用默认的应用数据库路径
    if "sqlalchemy.url" not in configuration or not configuration["sqlalchemy.url"]:
        import os
        workspace_root = os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "ai-video-gui")
        db_path = os.path.join(workspace_root, "data", "ai-video-gui.db")
        configuration["sqlalchemy.url"] = f"sqlite:///{db_path}"

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
