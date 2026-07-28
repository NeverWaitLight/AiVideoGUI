import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Popup {
    id: confirmDialog
    modal: true
    dim: true
    width: 360
    height: contentCol.implicitHeight
    anchors.centerIn: parent
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    padding: 0

    property string confirmTitle: "确认"
    property string confirmMessage: ""
    property string confirmText: "确定"
    property string cancelText: "取消"
    property bool dangerMode: false
    property var onConfirm: null

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
                text: confirmTitle
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                color: Theme.textAI
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24
                Layout.topMargin: 20
                Layout.bottomMargin: 12
            }

            Label {
                text: confirmMessage
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
                    text: confirmDialog.cancelText
                    Layout.preferredWidth: 88
                    Layout.preferredHeight: 36
                    onClicked: confirmDialog.close()

                    background: Rectangle {
                        radius: Theme.borderRadius
                        color: parent.hovered ? "#F0F0F0" : "#FFFFFF"
                        border.color: Theme.border
                        border.width: 1
                    }

                    contentItem: Label {
                        text: parent.text
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: Theme.fontSizeMedium
                        color: Theme.textAI
                    }
                }

                Button {
                    text: confirmDialog.confirmText
                    Layout.preferredWidth: 88
                    Layout.preferredHeight: 36
                    onClicked: {
                        if (onConfirm) onConfirm()
                        confirmDialog.close()
                    }

                    background: Rectangle {
                        radius: Theme.borderRadius
                        color: {
                            var base = confirmDialog.dangerMode ? Theme.danger : Theme.primary
                            return parent.hovered
                                ? (confirmDialog.dangerMode ? "#C0392B" : Theme.primaryHover)
                                : base
                        }
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

    function confirmDelete(itemName, callback) {
        confirmTitle = "确认删除"
        confirmMessage = "确定要删除「" + itemName + "」吗？此操作不可恢复。"
        confirmText = "删除"
        dangerMode = true
        onConfirm = callback
        open()
    }

    function confirm(message, callback) {
        confirmTitle = "确认"
        confirmMessage = message
        confirmText = "确定"
        dangerMode = false
        onConfirm = callback
        open()
    }
}
