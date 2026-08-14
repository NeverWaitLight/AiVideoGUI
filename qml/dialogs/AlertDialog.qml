import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: alertDialog
    modal: true
    width: 400
    anchors.centerIn: parent
    padding: 0
    contentWidth: 400
    contentHeight: Math.min(Math.max(messageLabel.implicitHeight + 16, 48), 280)

    property string alertMessage: ""
    property string alertType: "info"

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
                text: alertDialog.title
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
                    text: "确定"
                    highlighted: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 80
                    onClicked: alertDialog.accept()
                }
            }
        }
    }

    ScrollView {
        id: messageScroll
        width: alertDialog.availableWidth
        height: alertDialog.availableHeight
        contentWidth: availableWidth
        clip: true
        leftPadding: 18
        rightPadding: 18
        topPadding: 8
        bottomPadding: 8

        Label {
            id: messageLabel
            width: 364
            text: alertMessage
            wrapMode: Text.Wrap
            font.pixelSize: Theme.fontSizeNormal
        }
    }

    function info(title, message) {
        alertType = "info"
        alertDialog.title = title
        alertMessage = message || "(无提示信息)"
        open()
    }

    function warning(title, message) {
        alertType = "warning"
        alertDialog.title = title
        alertMessage = message || "(无提示信息)"
        open()
    }

    function error(title, message) {
        alertType = "error"
        alertDialog.title = title
        alertMessage = message || "(无提示信息)"
        open()
    }
}
