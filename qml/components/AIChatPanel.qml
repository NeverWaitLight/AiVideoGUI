import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

// AI 对话面板 - 可在侧边栏显示的窄版聊天界面
Control {
    id: aiChatPanel
    padding: 4

    background: Rectangle {
        radius: Theme.borderRadius
        color: Material.background
        border.width: 1
        border.color: "#d0d0d0"  // 浅灰色边框
    }

    contentItem: ColumnLayout {
        spacing: 0

        // 标题栏
        Pane {
            Layout.fillWidth: true
            padding: 8

            RowLayout {
                anchors.fill: parent
                spacing: 8

                Label {
                    text: "AI 助手"
                    font.pixelSize: Theme.fontSizeMedium
                    font.bold: true
                }

                Item { Layout.fillWidth: true }

                Button {
                    Layout.preferredWidth: 28
                    Layout.preferredHeight: 28
                    flat: true
                    display: AbstractButton.IconOnly
                    icon.source: "qrc:/resources/icons/close.svg"
                    icon.width: 16
                    icon.height: 16
                    onClicked: aiChatPanel.visible = false

                    background: Rectangle {
                        radius: 2
                        color: parent.hovered
                            ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                            : "transparent"
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
        }

        // 消息列表或空白状态（占据除输入区外的所有空间）
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            // 空白状态（messageList.count === 0 时显示）
            EmptyChatState {
                anchors.fill: parent
                anchors.margins: 16
                visible: messageList.count === 0
            }

            // 消息列表（messageList.count > 0 时显示）
            ListView {
                id: messageList
                anchors.fill: parent
                anchors.margins: 8
                model: bridge.conversations.messages
                clip: true
                spacing: 4
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

        // 底部固定输入区（卡片样式）
        Pane {
            Layout.fillWidth: true
            padding: 12

            ColumnLayout {
                anchors.fill: parent
                spacing: 8

                // 多行输入框
                TextArea {
                    id: inputArea
                    Layout.fillWidth: true
                    Layout.maximumHeight: 120
                    placeholderText: "描述你想生成的视频..."
                    wrapMode: TextArea.Wrap
                    font.pixelSize: Theme.fontSizeSmall
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

                // 功能按钮行
                RowLayout {
                    spacing: 8

                    Button {
                        flat: true
                        text: "参数"
                        font.pixelSize: Theme.fontSizeSmall
                        icon.source: "qrc:/resources/icons/settings.svg"
                        icon.width: 14
                        icon.height: 14
                        display: AbstractButton.TextBesideIcon
                        onClicked: paramPopup.open()
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        text: "发送"
                        highlighted: true
                        enabled: inputArea.text.trim().length > 0
                        font.pixelSize: Theme.fontSizeSmall
                        icon.source: "qrc:/resources/icons/send.svg"
                        icon.width: 14
                        icon.height: 14
                        display: AbstractButton.TextBesideIcon
                        onClicked: sendMessage()
                    }
                }
            }
        }
    }

    // 参数弹出面板
    Popup {
        id: paramPopup
        width: parent.width * 0.95
        height: Math.min(parent.height * 0.6, 280)
        modal: true
        anchors.centerIn: parent
        padding: 0

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            // 标题栏
            Pane {
                Layout.fillWidth: true
                padding: 12

                RowLayout {
                    anchors.fill: parent

                    Label {
                        text: "生成参数"
                        font.pixelSize: Theme.fontSizeMedium
                        font.bold: true
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        flat: true
                        text: "关闭"
                        font.pixelSize: Theme.fontSizeSmall
                        onClicked: paramPopup.close()
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
            }

            // 参数面板内容
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
