"""全局布局和尺寸常量，通过 setContextProperty 暴露给 QML。"""

from PySide6.QtCore import QObject, Property


class Theme(QObject):
    """全局字体/尺寸/布局常量（不包含颜色样式）。"""

    def __init__(self, parent=None):
        super().__init__(parent)

    # 字体大小
    @Property(int, constant=True)
    def fontSizeTiny(self):
        return 10

    @Property(int, constant=True)
    def fontSizeSmall(self):
        return 12

    @Property(int, constant=True)
    def fontSizeNormal(self):
        return 13

    @Property(int, constant=True)
    def fontSizeMedium(self):
        return 14

    @Property(int, constant=True)
    def fontSizeLarge(self):
        return 16

    @Property(int, constant=True)
    def fontSizeTitle(self):
        return 18

    # 布局尺寸
    @Property(int, constant=True)
    def tabBarWidth(self):
        return 60

    @Property(int, constant=True)
    def sidebarWidth(self):
        return 240

    @Property(int, constant=True)
    def headerHeight(self):
        return 56

    # 圆角尺寸
    @Property(int, constant=True)
    def radiusSmall(self):
        return 4

    @Property(int, constant=True)
    def radiusMedium(self):
        return 6

    @Property(int, constant=True)
    def borderRadius(self):
        return 8

    @Property(int, constant=True)
    def cardRadius(self):
        return 10
