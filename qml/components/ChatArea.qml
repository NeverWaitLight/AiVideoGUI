import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Pane {
    id: chatArea

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // 消息列表
        ListView {
            id: messageList
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: bridge.conversations.messages
            clip: true
            spacing: 4
            anchors.leftMargin: 12
            anchors.rightMargin: 12

            delegate: MessageBubble {
                width: messageList.width - 24
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

        // 参数面板
        ParameterPanel {
            id: paramPanel
            Layout.fillWidth: true
        }

        // 输入区域
        Pane {
            Layout.fillWidth: true
            Layout.preferredHeight: inputArea.implicitHeight + 24
            padding: 12

            RowLayout {
                anchors.fill: parent
                spacing: 12

                TextArea {
                    id: inputArea
                    Layout.fillWidth: true
                    placeholderText: "描述你想生成的视频..."
                    wrapMode: TextArea.Wrap
                    font.pixelSize: Theme.fontSizeMedium
                    Keys.onReturnPressed: {
                        if (!event.modifiers & Qt.ShiftModifier) {
                            sendMessage()
                            event.accepted = true
                        }
                    }
                }

                Button {
                    id: sendBtn
                    text: "发送"
                    Layout.preferredWidth: 80
                    Layout.preferredHeight: 40
                    enabled: inputArea.text.trim().length > 0
                    highlighted: true
                    font.pixelSize: Theme.fontSizeMedium
                    icon.source: "qrc:/resources/icons/send.svg"
                    icon.width: 18
                    icon.height: 18
                    display: AbstractButton.TextBesideIcon
                    onClicked: sendMessage()
                }
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
