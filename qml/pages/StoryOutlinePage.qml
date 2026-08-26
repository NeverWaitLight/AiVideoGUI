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
    property bool _previewMode: false
    property string _content: ""

    signal backClicked()
    signal nextStepClicked(string content)

    function _setContent(value, markDirty) {
        _content = value
        if (textArea.text !== value)
            textArea.text = value
        if (previewArea.text !== value)
            previewArea.text = value
        if (markDirty)
            _dirty = (_content !== _loadedContent)
        else
            _dirty = false
    }

    onProjectIdChanged: {
        if (projectId > 0) {
            var info = JSON.parse(bridge.projects.get_project_info(projectId))
            _projectName = info.name || ""
            bridge.storyOutline.load(projectId)
        }
    }

    Connections {
        target: bridge.projects
        function onProject_updated(pid) {
            if (pid === projectId && projectId > 0) {
                var info = JSON.parse(bridge.projects.get_project_info(projectId))
                _projectName = info.name || ""
            }
        }
    }

    Connections {
        target: bridge.storyOutline

        function onLoaded(content) {
            _loadedContent = content
            _setContent(content, false)
            _previewMode = false
        }

        function onSaved() {
            _loadedContent = _content
            _dirty = false
        }

        function onOptimize_finished(result) {
            _setContent(result, true)
            _previewMode = false
            aiOptimizeDialog.finishOptimizing()
        }

        function onOptimize_failed(error) {
            aiOptimizeDialog.finishOptimizing()
            alertDialog.error("错误", "优化失败：" + error)
        }

        function onBridge_error(msg) {
            aiOptimizeDialog.finishOptimizing()
            var safeMsg = msg ? String(msg) : "未知错误"
            alertDialog.error("错误", safeMsg)
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
                icon.source: _previewMode
                    ? "qrc:/resources/icons/edit.svg"
                    : "qrc:/resources/icons/visibility.svg"
                icon.width: 20
                icon.height: 20
                topPadding: 7
                bottomPadding: 7
                leftPadding: 7
                rightPadding: 7
                ToolTip.visible: hovered
                ToolTip.text: _previewMode ? "编辑" : "预览"

                background: Rectangle {
                    anchors.fill: parent
                    radius: Theme.radiusSmall
                    color: parent.hovered
                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                        : "transparent"
                }

                onClicked: {
                    if (!_previewMode) {
                        _content = textArea.text
                        previewArea.text = _content
                        _previewMode = true
                    } else {
                        _previewMode = false
                        if (textArea.text !== _content)
                            textArea.text = _content
                    }
                }
            }

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

                onClicked: {
                    if (!_previewMode)
                        _content = textArea.text
                    bridge.storyOutline.save(_content)
                }
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
                enabled: _content.trim().length > 0 || textArea.text.trim().length > 0
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
                    if (!_previewMode)
                        _content = textArea.text
                    if (_dirty) {
                        confirmDialog.confirm(
                            "检测到大纲内容有变化，是否先保存大纲再继续？",
                            function() {
                                bridge.storyOutline.save(_content)
                                page.nextStepClicked(_content.trim())
                            }
                        )
                    } else {
                        page.nextStepClicked(_content.trim())
                    }
                }
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 16
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Layout.bottomMargin: 16
            currentIndex: _previewMode ? 1 : 0

            ScrollView {
                clip: true

                TextArea {
                    id: textArea
                    textFormat: TextEdit.PlainText
                    placeholderText: "请输入项目大纲（支持 Markdown，点预览查看效果）..."
                    wrapMode: TextArea.Wrap
                    font.pixelSize: Theme.fontSizeMedium
                    padding: 0
                    background: null
                    onTextChanged: {
                        if (_previewMode)
                            return
                        _content = text
                        _dirty = (_content !== _loadedContent)
                    }
                }
            }

            ScrollView {
                clip: true

                TextArea {
                    id: previewArea
                    textFormat: TextEdit.MarkdownText
                    readOnly: true
                    wrapMode: TextArea.Wrap
                    font.pixelSize: Theme.fontSizeMedium
                    padding: 0
                    background: null
                    selectByMouse: true
                }
            }
        }
    }

    Shortcut {
        sequences: [StandardKey.Save]
        enabled: _dirty
        onActivated: {
            if (!_previewMode)
                _content = textArea.text
            bridge.storyOutline.save(_content)
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
            if (!_previewMode)
                _content = textArea.text
            bridge.storyOutline.optimize(userInput, _content)
        }
    }
}
