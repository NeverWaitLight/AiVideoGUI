import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: alertDialog
    modal: true
    width: 360
    anchors.centerIn: parent
    standardButtons: Dialog.Ok
    title: "提示"

    property string alertMessage: ""
    property string alertType: "info"

    Label {
        text: alertMessage
        wrapMode: Text.Wrap
        width: parent.width
    }

    function info(title, message) {
        alertType = "info"
        alertDialog.title = title
        alertMessage = message
        open()
    }

    function warning(title, message) {
        alertType = "warning"
        alertDialog.title = title
        alertMessage = message
        open()
    }

    function error(title, message) {
        alertType = "error"
        alertDialog.title = title
        alertMessage = message
        open()
    }
}
