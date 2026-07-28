import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Popup {
    id: alertDialog
    modal: true
    dim: true
    width: 360
    height: contentCol.implicitHeight
    anchors.centerIn: parent
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    padding: 0

    property string alertTitle: ""
    property string alertMessage: ""
    property string alertType: "info"  // info, warning, error

    Overlay.modal: Rectangle {
        color: "#40000000"
    }

    background: Rectangle {
        radius: Theme.cardRadius
        color: "#FFFFFF"
        border.color: Theme.border
        border.width: 1
    }

    contentItem: Item {
        ColumnLayout {
            id: contentCol
            anchors.fill: parent
            spacing: 0

            Label {
                text: alertTitle
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                color: {
                    if (alertType === "error") return Theme.danger
                    if (alertType === "warning") return Theme.warning
                    return Theme.textAI
                }
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24
                Layout.topMargin: 20
                Layout.bottomMargin: 12
            }

            Label {
                text: alertMessage
                wrapMode: Text.Wrap
                font.pixelSize: Theme.fontSizeMedium
                color: Theme.textSecondary
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24
                Layout.bottomMargin: 24
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.border
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24
                Layout.topMargin: 16
                Layout.bottomMargin: 20
                spacing: 12

                Item { Layout.fillWidth: true }

                Button {
                    text: "知道了"
                    Layout.preferredWidth: 88
                    Layout.preferredHeight: 36
                    onClicked: alertDialog.close()

                    background: Rectangle {
                        radius: Theme.borderRadius
                        color: parent.hovered ? Theme.primaryHover : Theme.primary
                    }

                    contentItem: Label {
                        text: parent.text
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: Theme.fontSizeMedium
                        color: "#FFFFFF"
                    }
                }
            }
        }
    }

    function info(title, message) {
        alertType = "info"
        alertTitle = title
        alertMessage = message
        open()
    }

    function warning(title, message) {
        alertType = "warning"
        alertTitle = title
        alertMessage = message
        open()
    }

    function error(title, message) {
        alertType = "error"
        alertTitle = title
        alertMessage = message
        open()
    }
}
