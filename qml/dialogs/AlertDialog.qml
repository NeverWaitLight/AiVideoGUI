import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: alertDialog
    modal: true
    standardButtons: Dialog.Ok
    width: 360
    anchors.centerIn: parent

    property string alertTitle: ""
    property string alertMessage: ""
    property string alertType: "info"  // info, warning, error

    title: alertTitle

    ColumnLayout {
        spacing: 12
        Label {
            text: alertMessage
            wrapMode: Text.Wrap
            Layout.fillWidth: true
            font.pixelSize: Theme.fontSizeMedium
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
