"""全局主题常量，通过 setContextProperty 暴露给 QML。"""

from PySide6.QtCore import QObject, Property
from PySide6.QtGui import QColor


class Theme(QObject):
    """全局主题颜色/字体/尺寸常量。"""

    # 颜色
    @Property(QColor, constant=True)
    def primary(self): return QColor("#4A90D9")

    @Property(QColor, constant=True)
    def primaryHover(self): return QColor("#357ABD")

    @Property(QColor, constant=True)
    def bgSidebar(self): return QColor("#F5F5F5")

    @Property(QColor, constant=True)
    def bgChat(self): return QColor("#FFFFFF")

    @Property(QColor, constant=True)
    def bubbleUser(self): return QColor("#4A90D9")

    @Property(QColor, constant=True)
    def bubbleAI(self): return QColor("#F0F0F0")

    @Property(QColor, constant=True)
    def textUser(self): return QColor("#FFFFFF")

    @Property(QColor, constant=True)
    def textAI(self): return QColor("#333333")

    @Property(QColor, constant=True)
    def textSecondary(self): return QColor("#888888")

    @Property(QColor, constant=True)
    def border(self): return QColor("#E0E0E0")

    @Property(QColor, constant=True)
    def danger(self): return QColor("#E74C3C")

    @Property(QColor, constant=True)
    def success(self): return QColor("#27AE60")

    @Property(QColor, constant=True)
    def warning(self): return QColor("#E67E22")

    # 字体大小
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
    def borderRadius(self): return 8

    @Property(int, constant=True)
    def cardRadius(self): return 10
