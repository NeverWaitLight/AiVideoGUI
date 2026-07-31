import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: page
    property int projectId: -1
    property bool _dirty: false
    property string _loadedContent: ""

    signal backClicked()
    signal nextStepClicked(string content)

    onProjectIdChanged: {
        if (projectId > 0) {
            bridge.storyOutline.load(projectId)
        }
    }

    Connections {
        target: bridge.storyOutline

        function onLoaded(content) {
            textArea.text = content
            _loadedContent = content
            _dirty = false
        }

        function onSaved() {
            _dirty = false
            _loadedContent = textArea.text
            alertDialog.info("提示", "大纲已保存")
        }

        function onOptimize_finished(result) {
            textArea.text = result
            _dirty = true
            alertDialog.info("成功", "大纲优化完成")
        }

        function onOptimize_failed(error) {
            alertDialog.error("错误", "优化失败：" + error)
        }

        function onError(msg) {
            alertDialog.error("错误", msg)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Comp.PageHeader {
            title: "大纲"
            Layout.fillWidth: true
            onBackClicked: page.backClicked()

            Button {
                Layout.preferredHeight: 34
                text: "保存"
                highlighted: _dirty
                enabled: _dirty
                topPadding: 6
                bottomPadding: 6
                leftPadding: 12
                rightPadding: 12
                onClicked: bridge.storyOutline.save(textArea.text)
            }

            Button {
                Layout.preferredHeight: 34
                text: "AI优化"
                enabled: !bridge.storyOutline.isOptimizing
                topPadding: 6
                bottomPadding: 6
                leftPadding: 12
                rightPadding: 12
                onClicked: {
                    aiOptimizeDialog.show("AI 优化大纲", "请输入优化要求...", "开始优化")
                }
            }

            Button {
                Layout.preferredHeight: 34
                text: "→"
                highlighted: true
                enabled: textArea.text.trim().length > 0
                topPadding: 6
                bottomPadding: 6
                leftPadding: 12
                rightPadding: 12
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

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 16
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Layout.bottomMargin: 16
            clip: true

            TextArea {
                id: textArea
                placeholderText: "请输入项目大纲..."
                wrapMode: TextArea.Wrap
                font.pixelSize: Theme.fontSizeMedium
                padding: 0
                background: null
                onTextChanged: {
                    _dirty = (textArea.text !== _loadedContent)
                }
            }
        }
    }

    Dialogs.AlertDialog {
        id: alertDialog
    }

    Dialogs.ConfirmDialog {
        id: confirmDialog
    }

    Dialogs.AIOptimizeDialog {
        id: aiOptimizeDialog
        onOptimizeRequested: function(userInput) {
            bridge.storyOutline.optimize(userInput, textArea.text)
        }
    }
}
