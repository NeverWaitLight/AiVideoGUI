import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: page
    property int projectId: -1
    property bool _dirty: false
    property string _loadedContent: ""
    property string _projectName: ""

    signal backClicked()
    signal nextStepClicked(string content)

    onProjectIdChanged: {
        if (projectId > 0) {
            var info = JSON.parse(bridge.projects.get_project_info(projectId))
            _projectName = info.name || ""
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
            aiOptimizeDialog.finishOptimizing()
            alertDialog.info("成功", "大纲优化完成")
        }

        function onOptimize_failed(error) {
            aiOptimizeDialog.finishOptimizing()
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
            projectName: _projectName
            title: "大纲"
            Layout.fillWidth: true
            onBackClicked: page.backClicked()

            Button {
                Layout.preferredWidth: 34
                Layout.preferredHeight: 34
                display: AbstractButton.IconOnly
                icon.source: "qrc:/resources/icons/save.svg"
                icon.width: 20
                icon.height: 20
                enabled: _dirty
                topPadding: 7
                bottomPadding: 7
                leftPadding: 7
                rightPadding: 7
                ToolTip.visible: hovered
                ToolTip.text: "保存"

                background: Rectangle {
                    anchors.fill: parent
                    radius: Theme.radiusSmall
                    color: parent.hovered
                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                        : "transparent"
                }

                onClicked: bridge.storyOutline.save(textArea.text)
            }

            Button {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                display: AbstractButton.IconOnly
                icon.source: "qrc:/resources/icons/auto_awesome.svg"
                icon.width: 20
                icon.height: 20
                icon.color: "white"
                enabled: !bridge.storyOutline.isOptimizing
                topPadding: 8
                bottomPadding: 8
                leftPadding: 8
                rightPadding: 8
                ToolTip.visible: hovered
                ToolTip.text: "Ai"

                background: Rectangle {
                    anchors.fill: parent
                    radius: parent.width / 2
                    color: parent.enabled ? (parent.pressed ? "#E65100" : (parent.hovered ? "#FB8C00" : "#FF9800")) : "#BDBDBD"
                }

                onClicked: {
                    aiOptimizeDialog.show("AI 优化大纲", "请输入优化要求...", "开始优化")
                }
            }

            Button {
                Layout.preferredWidth: 34
                Layout.preferredHeight: 34
                display: AbstractButton.IconOnly
                icon.source: "qrc:/resources/icons/arrow_forward.svg"
                icon.width: 20
                icon.height: 20
                enabled: textArea.text.trim().length > 0
                topPadding: 7
                bottomPadding: 7
                leftPadding: 7
                rightPadding: 7
                ToolTip.visible: hovered
                ToolTip.text: "下一步"

                background: Rectangle {
                    anchors.fill: parent
                    radius: Theme.radiusSmall
                    color: parent.hovered
                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                        : "transparent"
                }

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

    Shortcut {
        sequence: StandardKey.Save
        enabled: _dirty
        onActivated: {
            bridge.storyOutline.save(textArea.text)
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
