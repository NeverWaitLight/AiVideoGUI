"""AI 视频生成 GUI 客户端入口。"""

import os
import sys

from loguru import logger
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def setup_logging():
    """配置 loguru 日志系统。"""
    # 移除默认的控制台 handler
    logger.remove()

    # 1. 控制台输出（开发时使用，彩色）
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # 2. 文件日志（生产环境，实现 CLAUDE.md 要求的 5MB × 5 文件）
    try:
        log_dir = os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "ai-video-gui", "logs")
        os.makedirs(log_dir, exist_ok=True)

        logger.add(
            os.path.join(log_dir, "app.log"),
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="5 MB",  # 单文件 5MB 后轮换
            retention=5,  # 保留最新 5 个备份
            enqueue=True,  # 多线程安全（关键！适配 QThread）
            encoding="utf-8",
        )

        # 3. 错误级别单独记录（方便快速排查）
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
        # 如果文件日志配置失败，至少保证控制台日志可用
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

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
