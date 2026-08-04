import os
import sys

from loguru import logger
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQuickControls2 import QQuickStyle

from di import ApplicationContainer
from bridge.app_bridge import AppBridge
from bridge.theme import Theme
from storage.orm.base import init_engine, create_all_tables, ensure_columns
from utils import paths

import resources_rc


def setup_logging():
    logger.remove()

    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    try:
        log_dir = os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "ai-video-gui", "logs")
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

    root = paths.workspace_root()
    data_dir = paths.data_dir(root)
    cache_dir = paths.cache_dir(root)
    ws_dir = paths.workspace_dir(root)
    for d in (data_dir, cache_dir, ws_dir):
        os.makedirs(d, exist_ok=True)

    container = ApplicationContainer()
    container.config.workspace_root.from_value(root)
    container.config.config_path.from_value(os.path.join(data_dir, "config.json"))
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
    app.setApplicationName("AI Video GUI")
    app.setWindowIcon(QIcon(":/resources/logo.ico"))

    QQuickStyle.setStyle("Material")
    logger.info("应用样式: Material")

    db_path = os.path.join(data_dir, "ai-video-gui.db")
    database_url = f"sqlite:///{db_path}"
    init_engine(database_url, echo=False)
    create_all_tables()
    ensure_columns()

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

    scheduler.start()
    logger.info("后台任务调度器已启动")

    def on_about_to_quit():
        logger.info("应用即将退出，清理资源...")
        scheduler.shutdown()
        logger.info("资源清理完成")

    app.aboutToQuit.connect(on_about_to_quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
