import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: confirmDialog
    modal: true
    width: 360
    anchors.centerIn: parent
    standardButtons: Dialog.Ok | Dialog.Cancel
    title: "确认"

    property string confirmMessage: ""
    property bool dangerMode: false
    property var onConfirm: null

    Label {
        text: confirmMessage
        wrapMode: Text.Wrap
        width: parent.width
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
        confirmMessage = message
        dangerMode = false
        onConfirm = callback
        open()
    }
}
