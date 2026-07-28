import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: page
    property int projectId: -1
    property bool _dirty: false
    property var _chatMessages: []

    signal backClicked()
    signal nextStepClicked(string content)

    // Load outline when projectId changes
    onProjectIdChanged: {
        if (projectId > 0) {
            bridge.storyOutline.load(projectId)
            _chatMessages = []
            chatModel.clear()
        }
    }

    // Bridge connections
    Connections {
        target: bridge.storyOutline

        function onLoaded(content) {
            textArea.text = content
            _dirty = false
        }

        function onSaved() {
            _dirty = false
            alertDialog.info("提示", "大纲已保存")
        }

        function onOptimize_finished(result) {
            // 移除"正在思考中…"的占位气泡
            if (chatModel.count > 0) {
                var lastIdx = chatModel.count - 1
                if (chatModel.get(lastIdx).role === "assistant") {
                    chatModel.remove(lastIdx)
                }
            }
            textArea.text = result
            _dirty = true
            _addChatBubble("assistant", "已根据你的要求优化大纲，内容已更新到编辑器。")
        }

        function onOptimize_failed(error) {
            // 移除"正在思考中…"的占位气泡
            if (chatModel.count > 0) {
                var lastIdx = chatModel.count - 1
                if (chatModel.get(lastIdx).role === "assistant") {
                    chatModel.remove(lastIdx)
                }
            }
            _addChatBubble("assistant", "优化失败：" + error)
        }

        function onError(msg) {
            alertDialog.error("错误", msg)
        }
    }

    // Chat message model
    ListModel {
        id: chatModel
    }

    function _addChatBubble(role, text) {
        chatModel.append({ role: role, text: text })
        chatView.positionViewAtEnd()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ── 顶部导航栏 ──
        Comp.PageHeader {
            title: "故事大纲"
            Layout.fillWidth: true
            onBackClicked: page.backClicked()

            Button {
                text: "历史版本"
                icon.name: "document-open-recent"
                flat: true
                onClicked: {
                    bridge.storyOutline.load_history()
                    historyDialog.open()
                }
            }

            Button {
                text: "保存"
                highlighted: _dirty
                enabled: _dirty
                onClicked: bridge.storyOutline.save(textArea.text)
            }

            Button {
                text: "生成剧本 →"
                highlighted: true
                enabled: textArea.text.trim().length > 0
                onClicked: {
                    if (_dirty) {
                        confirmDialog.confirm(
                            "检测到大纲内容有变化，是否先保存大纲再继续？",
                            function() {
                                bridge.storyOutline.save(textArea.text)
                                page.nextStepClicked(textArea.text.trim())
                            }
                        )
                    } else {
                        page.nextStepClicked(textArea.text.trim())
                    }
                }
            }
        }

        // ── 主内容区 ──
        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            handle: Rectangle {
                implicitWidth: 1
                color: Theme.border
            }

            // 左侧：大纲编辑区
            Item {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 400

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 12

                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true

                        background: Rectangle {
                            radius: Theme.borderRadius
                            color: "#FFFFFF"
                            border.color: textArea.activeFocus ? Theme.primary : Theme.border
                            border.width: 1
                        }

                        TextArea {
                            id: textArea
                            placeholderText: "请输入项目大纲..."
                            wrapMode: TextArea.Wrap
                            font.pixelSize: Theme.fontSizeMedium
                            padding: 12
                            color: Theme.textAI
                            background: Item {}
                            onTextChanged: {
                                if (text !== bridge.storyOutline.content) {
                                    _dirty = true
                                }
                            }
                        }
                    }
                }
            }

            // 右侧：AI 对话面板
            Rectangle {
                SplitView.preferredWidth: 340
                SplitView.minimumWidth: 260
                color: "#F7F7F7"

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    // 面板标题
                    Rectangle {
                        Layout.fillWidth: true
                        height: 44
                        color: "#FFFFFF"

                        Label {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 16
                            text: "AI 助手"
                            font.pixelSize: Theme.fontSizeMedium
                            font.bold: true
                            color: Theme.textAI
                        }

                        Rectangle {
                            anchors.bottom: parent.bottom
                            width: parent.width
                            height: 1
                            color: Theme.border
                        }
                    }

                    // 消息列表
                    ListView {
                        id: chatView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 6
                        topMargin: 8
                        bottomMargin: 8
                        model: chatModel

                        delegate: Item {
                            width: ListView.view.width
                            height: bubbleRow.height + 8

                            Row {
                                id: bubbleRow
                                width: parent.width - 24
                                anchors.horizontalCenter: parent.horizontalCenter
                                spacing: 0
                                layoutDirection: model.role === "user" ? Qt.RightToLeft : Qt.LeftToRight

                                Rectangle {
                                    id: bubble
                                    width: Math.min(bubbleText.implicitWidth + 20, chatView.width - 60)
                                    height: bubbleText.implicitHeight + 16
                                    radius: 10
                                    color: model.role === "user" ? "#DCF8C6" : "#FFFFFF"

                                    Text {
                                        id: bubbleText
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        text: model.text
                                        wrapMode: Text.Wrap
                                        font.pixelSize: Theme.fontSizeSmall
                                        color: "#333333"
                                        textFormat: Text.PlainText
                                    }
                                }
                            }
                        }

                        // 空状态提示
                        Label {
                            visible: chatModel.count === 0
                            anchors.centerIn: parent
                            text: "在下方输入你的修改要求，\nAI 将帮你优化大纲"
                            color: Theme.textSecondary
                            font.pixelSize: Theme.fontSizeSmall
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }

                    // 输入区域
                    Rectangle {
                        Layout.fillWidth: true
                        height: 60
                        color: "#FAFAFA"

                        Rectangle {
                            anchors.top: parent.top
                            width: parent.width
                            height: 1
                            color: Theme.border
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            ScrollView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true

                                background: Rectangle {
                                    radius: 6
                                    color: "#FFFFFF"
                                    border.color: chatInput.activeFocus ? Theme.primary : Theme.border
                                }

                                TextArea {
                                    id: chatInput
                                    placeholderText: "描述你想修改的内容…"
                                    wrapMode: TextArea.Wrap
                                    font.pixelSize: Theme.fontSizeSmall
                                    padding: 6
                                    background: Item {}
                                    Keys.onReturnPressed: function(event) {
                                        if (!(event.modifiers & Qt.ShiftModifier)) {
                                            event.accepted = true
                                            _sendChat()
                                        }
                                    }
                                }
                            }

                            Button {
                                text: "发送"
                                highlighted: true
                                enabled: chatInput.text.trim().length > 0 && !bridge.storyOutline.isOptimizing
                                Layout.preferredHeight: 40
                                onClicked: _sendChat()
                            }
                        }
                    }
                }
            }
        }
    }

    // ── 对话框 ──

    Dialogs.AlertDialog {
        id: alertDialog
    }

    Dialogs.ConfirmDialog {
        id: confirmDialog
    }

    Dialogs.HistoryDialog {
        id: historyDialog
        model: bridge.storyOutline.historyModel
        onRestoreRequested: function(historyId) {
            confirmDialog.confirm(
                "确定要恢复到此历史版本吗？当前内容将被保存为新的历史版本。",
                function() {
                    bridge.storyOutline.restore_history(historyId)
                }
            )
        }
    }

    // ── 内部函数 ──

    function _sendChat() {
        var text = chatInput.text.trim()
        if (!text) return

        _addChatBubble("user", text)
        chatInput.text = ""

        if (!textArea.text.trim()) {
            _addChatBubble("assistant", "请先在左侧编辑器中输入大纲内容，再使用 AI 优化。")
            return
        }

        _addChatBubble("assistant", "正在思考中…")
        bridge.storyOutline.optimize(text, textArea.text)
    }
}
