import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

Item {
    id: titleBar
    implicitHeight: Theme.titleBarHeight

    property bool isMaximized: false
    property var appWindow: null
    property string title: ""

    Rectangle {
        anchors.fill: parent
        color: Material.background

        RowLayout {
            anchors.fill: parent
            spacing: 0

            // ── 拖拽区域（标题栏主体） ──
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                Label {
                    anchors.left: parent.left
                    anchors.leftMargin: 12
                    anchors.verticalCenter: parent.verticalCenter
                    text: titleBar.title
                    font.pixelSize: Theme.fontSizeSmall
                    color: Material.foreground
                }

                MouseArea {
                    anchors.fill: parent
                    property point pressPos

                    onPressed: {
                        pressPos = Qt.point(mouseX, mouseY)
                    }

                    onPositionChanged: {
                        var delta = Qt.point(mouseX - pressPos.x, mouseY - pressPos.y)
                        if (titleBar.appWindow && !titleBar.isMaximized) {
                            titleBar.appWindow.x += delta.x
                            titleBar.appWindow.y += delta.y
                        }
                    }

                    onDoubleClicked: {
                        bridge.toggle_maximize()
                        titleBar.isMaximized = !titleBar.isMaximized
                    }
                }
            }

            // ── 窗口控制按钮 ──

            WindowButton {
                id: minBtn
                Layout.preferredWidth: 46
                Layout.fillHeight: true

                Rectangle {
                    anchors.centerIn: parent
                    width: 10
                    height: 1
                    color: minBtn.hovered ? "#ffffff" : Material.foreground
                }

                onClicked: bridge.minimize_window()
            }

            WindowButton {
                id: maxBtn
                Layout.preferredWidth: 46
                Layout.fillHeight: true

                Rectangle {
                    visible: !titleBar.isMaximized
                    anchors.centerIn: parent
                    width: 10
                    height: 10
                    color: "transparent"
                    border.width: 1
                    border.color: maxBtn.hovered ? "#ffffff" : Material.foreground
                }

                Item {
                    visible: titleBar.isMaximized
                    anchors.centerIn: parent
                    width: 12
                    height: 12

                    Rectangle {
                        x: 0; y: 2
                        width: 9; height: 9
                        color: "transparent"
                        border.width: 1
                        border.color: maxBtn.hovered ? "#ffffff" : Material.foreground
                    }
                    Rectangle {
                        x: 3; y: 0
                        width: 9; height: 9
                        color: Material.background
                        border.width: 1
                        border.color: maxBtn.hovered ? "#ffffff" : Material.foreground
                    }
                }

                onClicked: {
                    bridge.toggle_maximize()
                    titleBar.isMaximized = !titleBar.isMaximized
                }
            }

            WindowButton {
                id: closeBtn
                Layout.preferredWidth: 46
                Layout.fillHeight: true
                isClose: true

                Canvas {
                    anchors.centerIn: parent
                    width: 10
                    height: 10
                    property color strokeColor: closeBtn.hovered ? "#ffffff" : Material.foreground

                    onStrokeColorChanged: requestPaint()

                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        ctx.strokeStyle = strokeColor
                        ctx.lineWidth = 1.2
                        ctx.beginPath()
                        ctx.moveTo(0, 0)
                        ctx.lineTo(width, height)
                        ctx.moveTo(width, 0)
                        ctx.lineTo(0, height)
                        ctx.stroke()
                    }
                }

                onClicked: bridge.close_window()
            }
        }
    }

    // 底部分割线已移除

    // ── 按钮组件 ──
    component WindowButton: Button {
        property bool isClose: false

        flat: true
        padding: 0

        background: Rectangle {
            color: {
                if (!parent.hovered) return "transparent"
                return parent.isClose ? "#e81123" : Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
            }
            Behavior on color { ColorAnimation { duration: 80 } }
        }
    }
}
