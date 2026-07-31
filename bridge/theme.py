from PySide6.QtCore import QObject, Property


class Theme(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

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

    @Property(int, constant=True)
    def tabBarWidth(self):
        return 52

    @Property(int, constant=True)
    def titleBarHeight(self):
        return 54

    @Property(int, constant=True)
    def rightBarWidth(self):
        return 52

    @Property(int, constant=True)
    def bottomBarHeight(self):
        return 39

    @Property(int, constant=True)
    def sidebarWidth(self):
        return 240

    @Property(int, constant=True)
    def headerHeight(self):
        return 44

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
