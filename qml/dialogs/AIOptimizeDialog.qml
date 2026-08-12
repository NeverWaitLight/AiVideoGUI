import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: aiOptimizeDialog
    modal: true
    width: 500
    height: 320
    anchors.centerIn: parent
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property string dialogTitle: "AI 优化"
    property string placeholderText: "请输入优化要求..."
    property string confirmButtonText: "开始优化"
    property bool isOptimizing: false

    signal optimizeRequested(string userInput)

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
                text: dialogTitle
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
                    enabled: !isOptimizing
                    onClicked: aiOptimizeDialog.close()
                }

                Button {
                    text: isOptimizing ? "生成中..." : confirmButtonText
                    highlighted: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 100
                    enabled: inputArea.text.trim().length > 0 && !isOptimizing
                    onClicked: {
                        if (inputArea.text.trim().length > 0) {
                            console.log("[AIOptimizeDialog] optimizeRequested:", inputArea.text.trim())
                            optimizeRequested(inputArea.text.trim())
                            aiOptimizeDialog.close()
                        }
                    }
                }
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        contentWidth: availableWidth
        clip: true

        TextArea {
            id: inputArea
            width: parent.width
            placeholderText: aiOptimizeDialog.placeholderText
            wrapMode: TextArea.Wrap
            font.pixelSize: Theme.fontSizeNormal
            selectByMouse: true
            enabled: !isOptimizing
        }
    }

    onOpened: {
        inputArea.text = ""
        isOptimizing = false
        inputArea.forceActiveFocus()
    }

    function show(title, placeholder, confirmText) {
        if (title) dialogTitle = title
        if (placeholder) placeholderText = placeholder
        if (confirmText) confirmButtonText = confirmText
        open()
    }

    function finishOptimizing() {
        isOptimizing = false
        close()
    }
}
