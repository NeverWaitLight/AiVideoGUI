import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

// AI 对话面板 - 可在侧边栏显示的窄版聊天界面
Control {
    id: aiChatPanel
    padding: 0

    background: Rectangle {
        color: "transparent"
    }

    contentItem: ColumnLayout {
        spacing: 0

        // 标题栏
        Pane {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            padding: 5

            background: Rectangle {
                color: "transparent"
                border.width: 0
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 1
                    color: "white"
                }
            }

            RowLayout {
                anchors.fill: parent
                spacing: 8

                Label {
                    text: "AI"
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

        // 底部固定输入区（带边框的容器）
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 180
            Layout.leftMargin: 4
            Layout.rightMargin: 4
            Layout.topMargin: 4
            Layout.bottomMargin: 4
            color: "transparent"
            border.width: 0
            radius: 0

            // 顶部白色边框
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: "white"
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 0

                // 用户输入内容区域（占 2/3 高度）
                TextArea {
                    id: inputArea
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: parent.height * 2 / 3
                    placeholderText: ""
                    wrapMode: TextArea.Wrap
                    font.pixelSize: Theme.fontSizeSmall
                    topPadding: 6
                    Keys.onReturnPressed: function(event) {
                        if (!(event.modifiers & Qt.ShiftModifier)) {
                            sendMessage()
                            event.accepted = true
                        }
                    }

                    background: Rectangle {
                        color: "transparent"
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                }

                // 用户输入操作栏（占 1/3 高度）
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: parent.height / 3
                    Layout.minimumHeight: 40
                    color: "transparent"

                    RowLayout {
                        anchors.fill: parent
                        spacing: 8

                    // 对话模型选择下拉框
                    ComboBox {
                        id: modelSelector
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 36
                        font.pixelSize: Theme.fontSizeSmall
                        model: ["GPT-4", "Claude", "通义千问"]
                        currentIndex: 0
                    }

                    Item { Layout.fillWidth: true }

                    // 用户设置按钮
                    Button {
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 36
                        flat: true
                        display: AbstractButton.IconOnly
                        icon.source: "qrc:/resources/icons/settings.svg"
                        icon.width: 16
                        icon.height: 16
                        padding: 0
                        leftPadding: 0
                        rightPadding: 0
                        topPadding: 0
                        bottomPadding: 0
                        onClicked: paramPopup.open()

                        background: Rectangle {
                            radius: Theme.radiusSmall
                            color: parent.hovered
                                ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                                : "transparent"
                        }
                    }

                    // 发送按钮
                    Button {
                        Layout.preferredWidth: 80
                        Layout.preferredHeight: 36
                        text: "发送"
                        highlighted: true
                        enabled: inputArea.text.trim().length > 0
                        font.pixelSize: Theme.fontSizeSmall
                        padding: 0
                        leftPadding: 0
                        rightPadding: 0
                        topPadding: 0
                        bottomPadding: 0
                        onClicked: sendMessage()

                        background: Rectangle {
                            radius: Theme.radiusSmall
                            color: parent.enabled
                                ? (parent.hovered ? Qt.darker(Material.accent, 1.1) : Material.accent)
                                : Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                        }
                    }
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
