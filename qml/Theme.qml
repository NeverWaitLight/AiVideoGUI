pragma Singleton
import QtQuick 2.15

QtObject {
    // 颜色
    readonly property color primary: "#4A90D9"
    readonly property color primaryHover: "#357ABD"
    readonly property color bgSidebar: "#F5F5F5"
    readonly property color bgChat: "#FFFFFF"
    readonly property color bubbleUser: "#4A90D9"
    readonly property color bubbleAI: "#F0F0F0"
    readonly property color textUser: "#FFFFFF"
    readonly property color textAI: "#333333"
    readonly property color textSecondary: "#888888"
    readonly property color border: "#E0E0E0"
    readonly property color danger: "#E74C3C"
    readonly property color success: "#27AE60"
    readonly property color warning: "#E67E22"

    // 字体
    readonly property int fontSizeSmall: 12
    readonly property int fontSizeNormal: 13
    readonly property int fontSizeMedium: 14
    readonly property int fontSizeLarge: 16
    readonly property int fontSizeTitle: 18

    // 尺寸
    readonly property int tabBarWidth: 60
    readonly property int sidebarWidth: 240
    readonly property int headerHeight: 56
    readonly property int borderRadius: 8
    readonly property int cardRadius: 10
}
