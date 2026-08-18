import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: closeChoiceDialog
    modal: true
    width: 420
    anchors.centerIn: parent
    padding: 0
    contentWidth: 420
    contentHeight: Math.min(Math.max(messageLabel.implicitHeight + 16, 48), 280)
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    title: "关闭窗口"

    background: Rectangle {
        color: Material.dialogColor
        radius: Theme.radiusMedium
    }

    header: Item {
        implicitHeight: 56

        Rectangle {
            anchors.fill: parent
            color: "transparent"

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
            }

            Label {
                anchors.left: parent.left
                anchors.leftMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                text: closeChoiceDialog.title
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
            }
        }
    }

    footer: Item {
        implicitHeight: 64

        Rectangle {
            anchors.fill: parent
            color: "transparent"

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
            }

            RowLayout {
                anchors.right: parent.right
                anchors.rightMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                spacing: 12

                Button {
                    text: "取消"
                    flat: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 80
                    onClicked: closeChoiceDialog.reject()
                }

                Button {
                    text: "退出"
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 80
                    Material.accent: Material.Red
                    highlighted: true
                    onClicked: {
                        bridge.settings.set_close_window_action("quit")
                        closeChoiceDialog.close()
                        bridge.quit_application()
                    }
                }

                Button {
                    text: "最小化到托盘"
                    highlighted: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 120
                    onClicked: {
                        bridge.settings.set_close_window_action("minimize")
                        closeChoiceDialog.close()
                        bridge.hide_to_tray()
                    }
                }
            }
        }
    }

    ScrollView {
        width: closeChoiceDialog.availableWidth
        height: closeChoiceDialog.availableHeight
        contentWidth: availableWidth
        clip: true
        leftPadding: 18
        rightPadding: 18
        topPadding: 8
        bottomPadding: 8

        Label {
            id: messageLabel
            width: 384
            text: "关闭窗口时希望如何处理？下次将按本次选择直接执行，不再询问。"
            wrapMode: Text.Wrap
            font.pixelSize: Theme.fontSizeNormal
        }
    }
}
