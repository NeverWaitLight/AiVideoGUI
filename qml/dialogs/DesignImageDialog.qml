import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: designImageDialog
    modal: true
    width: 480
    height: 300
    anchors.centerIn: parent
    padding: 0

    signal generateRequested(string userInput)

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
                text: "AI 生成设计图"
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
                    onClicked: designImageDialog.close()
                }

                Button {
                    text: "生成"
                    highlighted: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 100
                    onClicked: {
                        generateRequested(inputArea.text.trim())
                        designImageDialog.close()
                    }
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        spacing: 8

        Label {
            text: "补充设计要求（可选）"
            font.pixelSize: Theme.fontSizeSmall
            color: Material.foreground
            opacity: 0.7
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: availableWidth
            clip: true

            TextArea {
                id: inputArea
                width: parent.width
                placeholderText: "例如：赛博朋克风格、Q版形象、穿运动装..."
                wrapMode: TextArea.Wrap
                font.pixelSize: Theme.fontSizeNormal
                selectByMouse: true
            }
        }
    }

    onOpened: {
        inputArea.text = ""
        inputArea.forceActiveFocus()
    }
}
