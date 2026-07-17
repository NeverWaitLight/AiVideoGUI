"""AI 视频生成 GUI 客户端入口。"""

import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AI 视频生成")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
