"""AI 视频生成 GUI 客户端入口。"""

import logging
import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def _exception_hook(exc_type, exc_value, exc_tb):
    """全局未捕获异常钩子，确保异常信息写入 stderr。"""
    logging.getLogger().critical("未捕获异常", exc_info=(exc_type, exc_value, exc_tb))
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    sys.excepthook = _exception_hook

    app = QApplication(sys.argv)
    app.setApplicationName("AI 视频生成")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
