"""AI 视频生成 GUI 客户端入口。"""

import os
import sys

from loguru import logger
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl

from di import ApplicationContainer
from bridge.app_bridge import AppBridge
from bridge.theme import Theme
from storage.orm.base import init_engine, create_all_tables, ensure_columns
from utils import paths


def setup_logging():
    """配置 loguru 日志系统。"""
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
    """全局未捕获异常钩子，确保异常信息写入 stderr。"""
    logger.opt(exception=(exc_type, exc_value, exc_tb)).critical("未捕获异常")
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def main():
    setup_logging()
    logger.info("应用启动")

    sys.excepthook = _exception_hook

    app = QApplication(sys.argv)
    app.setApplicationName("AI 视频生成")

    # 使用 Basic 样式，支持自定义 background
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

    # 初始化目录
    root = paths.workspace_root()
    data_dir = paths.data_dir(root)
    cache_dir = paths.cache_dir(root)
    ws_dir = paths.workspace_dir(root)
    chat_dir = paths.chat_dir(root)
    for d in (data_dir, cache_dir, ws_dir, chat_dir):
        os.makedirs(d, exist_ok=True)

    # 初始化数据库
    db_path = os.path.join(data_dir, "ai-video-gui.db")
    database_url = f"sqlite:///{db_path}"
    init_engine(database_url, echo=False)
    create_all_tables()
    ensure_columns()

    # 初始化 DI 容器
    container = ApplicationContainer()
    container.config.workspace_root.from_value(root)
    container.config.config_path.from_value(os.path.join(data_dir, "config.json"))

    # 创建 Bridge（手动传入容器实例）
    bridge = AppBridge(container)
    theme = Theme()

    # 加载 QML
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.rootContext().setContextProperty("Theme", theme)

    qml_dir = os.path.join(os.path.dirname(__file__), "qml")
    main_qml = os.path.join(qml_dir, "main.qml")
    engine.load(QUrl.fromLocalFile(main_qml))

    if not engine.rootObjects():
        logger.error("QML 加载失败")
        sys.exit(-1)

    logger.info("QML 引擎就绪")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
