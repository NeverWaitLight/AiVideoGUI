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
        anchors.fill: parent
        anchors.leftMargin: 18
        anchors.rightMargin: 18
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        contentWidth: availableWidth
        clip: true

        Label {
            width: parent.parent.width - 36
            text: alertMessage
            wrapMode: Text.Wrap
            font.pixelSize: Theme.fontSizeNormal
        }
    }

    function info(title, message) {
        alertType = "info"
        alertDialog.title = title
        alertMessage = message || "(无提示信息)"
        console.log("[AlertDialog] info:", title, alertMessage)
        open()
    }

    function warning(title, message) {
        alertType = "warning"
        alertDialog.title = title
        alertMessage = message || "(无提示信息)"
        console.log("[AlertDialog] warning:", title, alertMessage)
        open()
    }

    function error(title, message) {
        alertType = "error"
        alertDialog.title = title
        alertMessage = message || "(无提示信息)"
        console.log("[AlertDialog] error:", title, alertMessage)
        open()
    }
}
