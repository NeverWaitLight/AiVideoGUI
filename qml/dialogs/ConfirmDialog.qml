import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: confirmDialog
    modal: true
    width: 400
    anchors.centerIn: parent
    padding: 0
    contentWidth: 400
    contentHeight: Math.min(Math.max(messageLabel.implicitHeight + 16, 48), 280)

    property string confirmMessage: ""
    property bool dangerMode: false
    property var onConfirm: null

    title: ""

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
                text: confirmDialog.title
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
                    onClicked: confirmDialog.reject()
                }

                Button {
                    text: "确定"
                    highlighted: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 80
                    Material.accent: dangerMode ? Material.Red : Material.Blue
                    onClicked: confirmDialog.accept()
                }
            }
        }
    }

    ScrollView {
        id: messageScroll
        width: confirmDialog.availableWidth
        height: confirmDialog.availableHeight
        contentWidth: availableWidth
        clip: true
        leftPadding: 18
        rightPadding: 18
        topPadding: 8
        bottomPadding: 8

        Label {
            id: messageLabel
            width: 364
            text: confirmMessage
            wrapMode: Text.Wrap
            font.pixelSize: Theme.fontSizeNormal
        }
    }

    onAccepted: {
        if (onConfirm) onConfirm()
    }

    function confirmDelete(itemName, callback) {
        title = "确认删除"
        confirmMessage = "确定要删除「" + itemName + "」吗？此操作不可恢复。"
        dangerMode = true
        onConfirm = callback
        open()
    }

    function confirm(message, callback) {
        title = "确认"
        confirmMessage = message ? String(message) : "请确认是否继续？"
        dangerMode = false
        onConfirm = callback
        open()
    }
}
