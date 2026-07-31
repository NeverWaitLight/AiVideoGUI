import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Pane {
    id: chatArea
    padding: 0

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            EmptyChatState {
                anchors.fill: parent
                anchors.margins: 32
                visible: messageList.count === 0
            }

            ListView {
                id: messageList
                anchors.fill: parent
                anchors.margins: 16
                model: bridge.conversations.messages
                clip: true
                spacing: 8
                visible: count > 0

                delegate: MessageBubble {
                    width: messageList.width
                    isUser: model.msgRole === "user"
                    messageText: model.content || ""
                    timeText: model.timestamp || ""
                    msgStatus: model.status || ""
                    localPath: model.localPath || ""
                    errorMessage: model.errorMessage || ""
                    msgId: model.msgId || ""
                }

                add: Transition {
                    NumberAnimation { properties: "y"; from: -50; duration: 200; easing.type: Easing.OutCubic }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
        }

        Pane {
            Layout.fillWidth: true
            Layout.margins: 16
            padding: 16

            ColumnLayout {
                anchors.fill: parent
                spacing: 12

                TextArea {
                    id: inputArea
                    Layout.fillWidth: true
                    Layout.maximumHeight: 120
                    placeholderText: "描述你想生成的视频..."
                    wrapMode: TextArea.Wrap
                    font.pixelSize: Theme.fontSizeMedium
                    Keys.onReturnPressed: {
                        if (!(event.modifiers & Qt.ShiftModifier)) {
                            sendMessage()
                            event.accepted = true
                        }
                    }

                    background: Rectangle {
                        radius: Theme.radiusMedium
                        color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.05)
                        border.width: 1
                        border.color: inputArea.activeFocus
                            ? Material.accent
                            : Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                    }
                }

                RowLayout {
                    spacing: 12

                    Button {
                        flat: true
                        text: "参数"
                        font.pixelSize: Theme.fontSizeNormal
                        icon.source: "qrc:/resources/icons/settings.svg"
                        icon.width: 16
                        icon.height: 16
                        display: AbstractButton.TextBesideIcon
                        onClicked: paramPopup.open()
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        text: "发送"
                        highlighted: true
                        enabled: inputArea.text.trim().length > 0
                        font.pixelSize: Theme.fontSizeMedium
                        icon.source: "qrc:/resources/icons/send.svg"
                        icon.width: 18
                        icon.height: 18
                        display: AbstractButton.TextBesideIcon
                        Layout.preferredWidth: 100
                        Layout.preferredHeight: 40
                        onClicked: sendMessage()
                    }
                }
            }
        }
    }

    Popup {
        id: paramPopup
        width: Math.min(parent.width * 0.8, 600)
        height: Math.min(parent.height * 0.5, 320)
        modal: true
        anchors.centerIn: parent
        padding: 0

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            Pane {
                Layout.fillWidth: true
                padding: 16

                RowLayout {
                    anchors.fill: parent

                    Label {
                        text: "生成参数"
                        font.pixelSize: Theme.fontSizeLarge
                        font.bold: true
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        flat: true
                        text: "关闭"
                        font.pixelSize: Theme.fontSizeNormal
                        onClicked: paramPopup.close()
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
            }

            ParameterPanel {
                id: paramPanel
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }
    }

    function sendMessage() {
        var text = inputArea.text.trim()
        if (!text) return
        bridge.conversations.send_message(
            text,
            paramPanel.provider,
            paramPanel.modelName,
            paramPanel.resolution,
            paramPanel.ratio,
            paramPanel.duration,
            paramPanel.promptExtend,
            paramPanel.watermark
        )
        inputArea.text = ""
    }
}
