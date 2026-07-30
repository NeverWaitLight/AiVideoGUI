"""AI 视频生成 GUI 客户端入口。"""

import os
import sys

# 启用 QML 可视化调试工具（开发模式）
# 取消注释以下行来启用不同的可视化模式：
# os.environ["QSG_VISUALIZE"] = "overdraw"  # 显示重绘区域
# os.environ["QSG_VISUALIZE"] = "batches"   # 显示批次边界
# os.environ["QSG_VISUALIZE"] = "clip"      # 显示裁剪区域
# os.environ["QML_IMPORT_TRACE"] = "1"      # 跟踪 QML 导入
# os.environ["QT_LOGGING_RULES"] = "qt.qml.binding.removal.info=true"  # 绑定调试

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

# 导入编译后的 Qt 资源
import resources_rc  # noqa: F401


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

    # 初始化目录（在创建 QApplication 之前）
    root = paths.workspace_root()
    data_dir = paths.data_dir(root)
    cache_dir = paths.cache_dir(root)
    ws_dir = paths.workspace_dir(root)
    chat_dir = paths.chat_dir(root)
    for d in (data_dir, cache_dir, ws_dir, chat_dir):
        os.makedirs(d, exist_ok=True)

    # 初始化 DI 容器并读取配置（在创建 QApplication 之前）
    container = ApplicationContainer()
    container.config.workspace_root.from_value(root)
    container.config.config_path.from_value(os.path.join(data_dir, "config.json"))
    config_manager = container.config_manager()
    color_scheme = config_manager.settings.color_scheme or "System"

    # 设置 Material 主题环境变量（必须在 QApplication 创建之前）
    if color_scheme == "Light":
        os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "Light"
    elif color_scheme == "Dark":
        os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "Dark"
    else:  # System
        os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "System"

    logger.info(f"应用 Material 主题: {color_scheme}")

    # 创建 QApplication 并设置 Material 样式
    app = QApplication(sys.argv)
    app.setApplicationName("AI Video GUI")
    app.setWindowIcon(QIcon(":/resources/logo.ico"))

    QQuickStyle.setStyle("Material")
    logger.info("应用样式: Material")

    # 初始化数据库
    db_path = os.path.join(data_dir, "ai-video-gui.db")
    database_url = f"sqlite:///{db_path}"
    init_engine(database_url, echo=False)
    create_all_tables()
    ensure_columns()

    # 创建 Bridge（手动传入容器实例）
    bridge = AppBridge(container)
    theme = Theme()

    # 加载 QML
    engine = QQmlApplicationEngine()

    # 连接警告信号来捕获 QML 错误
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

    # 启动后台任务调度器
    scheduler = container.background_scheduler()

    # 注册视频任务轮询任务（周期性任务）
    video_polling_task = container.video_polling_task()
    video_polling_task.set_config_manager(config_manager)
    video_polling_task.set_media_service(container.media_service())
    scheduler.register_task(video_polling_task)

    # 注册项目封面生成任务（一次性任务）
    project_cover_task = container.project_cover_task()
    scheduler.register_task(project_cover_task)

    # 启动调度器
    scheduler.start()
    logger.info("后台任务调度器已启动")

    # 应用启动时自动触发一次封面生成任务
    scheduler.trigger_task("project_cover_generation")
    logger.info("已触发启动时封面生成任务")

    # 连接应用退出信号，确保清理资源
    def on_about_to_quit():
        logger.info("应用即将退出，清理资源...")
        chat_service = container.chat_service()
        chat_service.cleanup()
        scheduler.shutdown()
        logger.info("资源清理完成")

    app.aboutToQuit.connect(on_about_to_quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
