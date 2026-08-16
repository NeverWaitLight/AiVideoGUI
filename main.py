import os
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication
from loguru import logger

from bridge.app_bridge import AppBridge
from bridge.theme import Theme
from di import ApplicationContainer
from storage.orm.base import init_engine
import resources_rc
from utils import paths
from utils.resources import copy_resources_to_workspace


def setup_logging():
    logger.remove()

    # 打包后无控制台环境下 sys.stderr 可能为 None，跳过控制台日志
    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
        )

    try:
        root = paths.workspace_root()
        if not root:
            if sys.stderr:
                print(f"[ERROR] workspace_root() returned None or empty string", file=sys.stderr)
                print(f"LOCALAPPDATA: {os.environ.get('LOCALAPPDATA')}", file=sys.stderr)
                print(f"HOME: {os.path.expanduser('~')}", file=sys.stderr)
            return

        log_dir = paths.logs_dir(root)
        if not log_dir:
            if sys.stderr:
                print(f"[ERROR] logs_dir() returned None or empty string", file=sys.stderr)
            return

        os.makedirs(log_dir, exist_ok=True)

        logger.add(
            os.path.join(log_dir, "app.log"),
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="5 MB",
            retention=5,
            enqueue=True,
            encoding="utf-8",
        )

        logger.add(
            os.path.join(log_dir, "error.log"),
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="5 MB",
            retention=5,
            enqueue=True,
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning(f"日志文件配置失败: {e}")


def _exception_hook(exc_type, exc_value, exc_tb):
    logger.opt(exception=(exc_type, exc_value, exc_tb)).critical("未捕获异常")
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def main():
    setup_logging()
    logger.info("应用启动")

    sys.excepthook = _exception_hook

    if sys.platform == "win32":
        from utils.windows_app_identity import ensure_windows_toast_identity

        ensure_windows_toast_identity()

    root = paths.workspace_root()
    data_dir = paths.data_dir(root)
    cache_dir = paths.cache_dir(root)
    ws_dir = paths.workspace_dir(root)
    resources_dir = paths.resources_dir(root)
    for d in (data_dir, cache_dir, ws_dir, resources_dir):
        os.makedirs(d, exist_ok=True)

    copy_resources_to_workspace(root)

    container = ApplicationContainer()
    container.config.workspace_root.from_value(root)
    container.config.config_path.from_value(os.path.join(data_dir, "config.json"))
    container.config.providers_catalog_path.from_value(
        os.path.join(resources_dir, "providers.json")
    )

    # 读取版本号
    import tomllib
    pyproject_path = os.path.join(os.path.dirname(__file__), "pyproject.toml")
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    app_version = pyproject_data.get("project", {}).get("version", "0.0.1")
    container.config.app_version.from_value(app_version)

    config_manager = container.config_manager()
    color_scheme = config_manager.settings.color_scheme or "System"

    if color_scheme == "Light":
        os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "Light"
    elif color_scheme == "Dark":
        os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "Dark"
    else:
        os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "System"

    logger.info(f"应用 Material 主题: {color_scheme}")

    app = QApplication(sys.argv)
    app.setApplicationName("AiVideoGUI")
    app.setApplicationVersion(app_version)
    app.setWindowIcon(QIcon(":/resources/logo.ico"))

    QQuickStyle.setStyle("Material")
    logger.info("应用样式: Material")

    db_path = os.path.join(data_dir, "ai-video-gui.db")
    database_url = f"sqlite:///{db_path}"
    init_engine(database_url, echo=False)

    # 数据库初始化和迁移
    from alembic.config import Config
    from alembic import command
    from sqlalchemy import create_engine, inspect
    from storage.orm.base import Base
    import logging

    logging.getLogger("alembic").setLevel(logging.WARNING)

    # 检查核心表是否存在（判断是否为全新安装）
    temp_engine = create_engine(database_url)
    inspector = inspect(temp_engine)
    existing_tables = inspector.get_table_names()

    # 核心表列表（projects 表是必须的）
    core_tables = ['projects', 'conversations', 'messages']
    has_core_tables = any(table in existing_tables for table in core_tables)

    if not has_core_tables:
        # 全新安装：直接创建所有表
        logger.info("检测到全新安装，初始化数据库...")
        Base.metadata.create_all(temp_engine)
        logger.info("数据库表创建完成")

        # 插入预设视觉风格数据（仅保留实际存在的 6 个风格）
        logger.info("初始化视觉风格数据...")
        from sqlalchemy import text
        preset_styles = [
            ("毛毡风格", 1, "resources/styles/felt.png"),
            ("3D卡通", 1, "resources/styles/3d_cartoon.png"),
            ("像素风格", 1, "resources/styles/pixel_art.png"),
            ("木偶动画", 1, "resources/styles/puppet_animation.png"),
            ("黏土风格", 1, "resources/styles/claymation.png"),
            ("黑白动画", 1, "resources/styles/black_and_white_animation.png"),
        ]
        with temp_engine.connect() as conn:
            for name, is_default, image_path in preset_styles:
                conn.execute(
                    text(
                        "INSERT INTO visual_styles (name, is_default, sample_image_path, created_at, updated_at) "
                        "VALUES (:name, :is_default, :image_path, strftime('%s', 'now') * 1000, strftime('%s', 'now') * 1000)"
                    ),
                    {"name": name, "is_default": is_default, "image_path": image_path}
                )
            conn.commit()
        logger.info(f"已插入 {len(preset_styles)} 个预设视觉风格")

        # 标记为最新版本（跳过所有迁移）
        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        command.stamp(alembic_cfg, "head")
        logger.info("数据库版本已标记为最新")
    else:
        # 已有数据库：正常运行迁移
        logger.info("检测到现有数据库，执行迁移...")
        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        try:
            command.upgrade(alembic_cfg, "head")
            logger.info("数据库迁移完成")
        except Exception as e:
            logger.error(f"数据库迁移失败: {e}")
            raise

    temp_engine.dispose()

    engine = QQmlApplicationEngine()
    bridge = AppBridge(container, parent=engine)
    theme = Theme(parent=engine)

    warnings_list = []
    def on_warnings(qml_warnings):
        for w in qml_warnings:
            msg = f"{w.url().toString()}:{w.line()} - {w.description()}"
            warnings_list.append(msg)
            logger.error(f"QML: {msg}")

    engine.warnings.connect(on_warnings)

    engine.rootContext().setContextProperty("bridge", bridge)
    engine.rootContext().setContextProperty("Theme", theme)

    qml_dir = os.path.join(os.path.dirname(__file__), "qml")
    main_qml = os.path.join(qml_dir, "main.qml")
    engine.load(QUrl.fromLocalFile(main_qml))

    if not engine.rootObjects():
        logger.error("QML 加载失败")
        if not warnings_list:
            logger.error("未捕获到具体错误信息")
        sys.exit(-1)

    logger.info("QML 引擎就绪")

    scheduler = container.background_scheduler()

    video_polling_task = container.video_polling_task()
    video_polling_task.set_config_manager(config_manager)
    video_polling_task.set_media_service(container.media_service())
    scheduler.register_task(video_polling_task)

    update_check_task = container.update_check_task()
    update_check_task.signal_emitter.update_found.connect(bridge.update.update_available)
    scheduler.register_task(update_check_task)

    scheduler.start()
    logger.info("后台任务调度器已启动（延迟 3 秒）")

    def on_about_to_quit():
        logger.info("应用即将退出，清理资源...")
        scheduler.shutdown()
        logger.info("资源清理完成")

    app.aboutToQuit.connect(on_about_to_quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
