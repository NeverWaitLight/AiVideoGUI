import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: confirmDialog
    modal: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    title: "确认"
    width: 360
    anchors.centerIn: parent

    property string confirmMessage: ""
    property var onConfirm: null

    Label {
        text: confirmMessage
        wrapMode: Text.Wrap
        width: parent.width
        font.pixelSize: Theme.fontSizeMedium
    }

    onAccepted: {
        if (onConfirm) onConfirm()
    }

    function confirmDelete(itemName, callback) {
        confirmMessage = "确定要删除「" + itemName + "」吗？此操作不可恢复。"
        onConfirm = callback
        open()
    }

    function confirm(message, callback) {
        confirmMessage = message
        onConfirm = callback
        open()
    }
}
