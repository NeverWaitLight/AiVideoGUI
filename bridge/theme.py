"""全局主题常量，通过 setContextProperty 暴露给 QML。"""

import sys
from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtGui import QColor, QPalette, QGuiApplication


class Theme(QObject):
    """全局主题颜色/字体/尺寸常量。"""

    themeChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = "system"  # "light", "dark", "system"
        self._is_dark = self._detect_system_dark_mode()

        # 监听系统主题变化（通过定时器轮询 Windows Registry）
        if sys.platform == "win32":
            from PySide6.QtCore import QTimer
            self._theme_check_timer = QTimer(self)
            self._theme_check_timer.timeout.connect(self._check_system_theme_change)
            self._theme_check_timer.start(3000)  # 每 3 秒检查一次

    def _detect_system_dark_mode(self) -> bool:
        """检测系统是否使用暗色主题。"""
        if sys.platform == "win32":
            try:
                import winreg
                # 读取 Windows 注册表中的 AppsUseLightTheme 设置
                # 0 = 暗色模式, 1 = 亮色模式
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(
                    registry,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return value == 0  # 0 表示暗色模式
            except Exception:
                # 如果读取失败，回退到 QPalette 检测
                pass

        # 非 Windows 或注册表读取失败时使用 QPalette
        app = QGuiApplication.instance()
        if app:
            palette = app.palette()
            bg_color = palette.color(QPalette.ColorRole.Window)
            brightness = (bg_color.red() + bg_color.green() + bg_color.blue()) / 3
            return brightness < 128
        return False

    @Slot()
    def _check_system_theme_change(self):
        """定期检查系统主题变化（仅在 system 模式下）。"""
        if self._mode == "system":
            old_dark = self._is_dark
            self._is_dark = self._detect_system_dark_mode()
            if old_dark != self._is_dark:
                self.themeChanged.emit()

    @Property(str, notify=themeChanged)
    def mode(self):
        """主题模式：light, dark, system。"""
        return self._mode

    @mode.setter
    def mode(self, value: str):
        if value not in ("light", "dark", "system"):
            return
        if self._mode != value:
            self._mode = value
            if value == "system":
                self._is_dark = self._detect_system_dark_mode()
            else:
                self._is_dark = (value == "dark")
            self.themeChanged.emit()

    @Property(bool, notify=themeChanged)
    def isDark(self):
        """当前是否为暗色主题。"""
        return self._is_dark

    # 颜色 - 根据主题动态返回
    @Property(QColor, notify=themeChanged)
    def primary(self):
        return QColor("#4A90D9") if not self._is_dark else QColor("#5BA3E8")

    @Property(QColor, notify=themeChanged)
    def primaryHover(self):
        return QColor("#357ABD") if not self._is_dark else QColor("#4A90D9")

    @Property(QColor, notify=themeChanged)
    def bgSidebar(self):
        return QColor("#F5F5F5") if not self._is_dark else QColor("#1E1E1E")

    @Property(QColor, notify=themeChanged)
    def bgChat(self):
        return QColor("#FFFFFF") if not self._is_dark else QColor("#2D2D2D")

    @Property(QColor, notify=themeChanged)
    def bubbleUser(self):
        return QColor("#4A90D9") if not self._is_dark else QColor("#5BA3E8")

    @Property(QColor, notify=themeChanged)
    def bubbleAI(self):
        return QColor("#F0F0F0") if not self._is_dark else QColor("#3A3A3A")

    @Property(QColor, notify=themeChanged)
    def textUser(self):
        return QColor("#FFFFFF")

    @Property(QColor, notify=themeChanged)
    def textAI(self):
        return QColor("#333333") if not self._is_dark else QColor("#E0E0E0")

    @Property(QColor, notify=themeChanged)
    def textSecondary(self):
        return QColor("#888888") if not self._is_dark else QColor("#A0A0A0")

    @Property(QColor, notify=themeChanged)
    def border(self):
        return QColor("#E0E0E0") if not self._is_dark else QColor("#404040")

    @Property(QColor, notify=themeChanged)
    def danger(self):
        return QColor("#E74C3C") if not self._is_dark else QColor("#FF6B6B")

    @Property(QColor, notify=themeChanged)
    def success(self):
        return QColor("#27AE60") if not self._is_dark else QColor("#51CF66")

    @Property(QColor, notify=themeChanged)
    def warning(self):
        return QColor("#E67E22") if not self._is_dark else QColor("#FF922B")

    @Property(QColor, notify=themeChanged)
    def dangerHover(self):
        return QColor("#C0392B") if not self._is_dark else QColor("#E74C3C")

    @Property(QColor, notify=themeChanged)
    def bgHover(self):
        return QColor("#F8F8F8") if not self._is_dark else QColor("#3A3A3A")

    @Property(QColor, notify=themeChanged)
    def bgPlaceholder(self):
        return QColor("#E8E8E8") if not self._is_dark else QColor("#404040")

    @Property(QColor, notify=themeChanged)
    def bgSelected(self):
        return QColor("#F0F5FF") if not self._is_dark else QColor("#2B3A4F")

    @Property(QColor, notify=themeChanged)
    def bgTag(self):
        return QColor("#E3F2FD") if not self._is_dark else QColor("#1E3A5F")

    @Property(QColor, notify=themeChanged)
    def switchOff(self):
        return QColor("#D0D0D0") if not self._is_dark else QColor("#505050")

    @Property(QColor, notify=themeChanged)
    def disabled(self):
        return QColor("#CCCCCC") if not self._is_dark else QColor("#555555")

    # 字体大小
    @Property(int, constant=True)
    def fontSizeTiny(self): return 10

    @Property(int, constant=True)
    def fontSizeSmall(self): return 12

    @Property(int, constant=True)
    def fontSizeNormal(self): return 13

    @Property(int, constant=True)
    def fontSizeMedium(self): return 14

    @Property(int, constant=True)
    def fontSizeLarge(self): return 16

    @Property(int, constant=True)
    def fontSizeTitle(self): return 18

    # 尺寸
    @Property(int, constant=True)
    def tabBarWidth(self): return 60

    @Property(int, constant=True)
    def sidebarWidth(self): return 240

    @Property(int, constant=True)
    def headerHeight(self): return 56

    @Property(int, constant=True)
    def radiusSmall(self): return 4

    @Property(int, constant=True)
    def radiusMedium(self): return 6

    @Property(int, constant=True)
    def borderRadius(self): return 8

    @Property(int, constant=True)
    def cardRadius(self): return 10

    # 字体大小
    @Property(int, constant=True)
    def fontSizeTiny(self): return 10

    @Property(int, constant=True)
    def fontSizeSmall(self): return 12

    @Property(int, constant=True)
    def fontSizeNormal(self): return 13

    @Property(int, constant=True)
    def fontSizeMedium(self): return 14

    @Property(int, constant=True)
    def fontSizeLarge(self): return 16

    @Property(int, constant=True)
    def fontSizeTitle(self): return 18

    # 尺寸
    @Property(int, constant=True)
    def tabBarWidth(self): return 60

    @Property(int, constant=True)
    def sidebarWidth(self): return 240

    @Property(int, constant=True)
    def headerHeight(self): return 56

    @Property(int, constant=True)
    def radiusSmall(self): return 4

    @Property(int, constant=True)
    def radiusMedium(self): return 6

    @Property(int, constant=True)
    def borderRadius(self): return 8

    @Property(int, constant=True)
    def cardRadius(self): return 10
