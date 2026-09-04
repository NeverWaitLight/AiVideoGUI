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
    property string _preOptimizeContent: ""
    property string _pendingResult: ""
    property bool _aiWaiting: false
    property bool _waitingFirstChunk: false
    property bool _streamFinished: false

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

    function _scrollEditorToBottom() {
        var flickable = editScrollView.contentItem
        if (flickable && flickable.contentHeight !== undefined)
            flickable.contentY = Math.max(0, flickable.contentHeight - flickable.height)
    }

    function _syncTypedContent() {
        _content = textArea.text
        _dirty = (_content !== _loadedContent)
        _scrollEditorToBottom()
    }

    function _tryCompleteOutlineStream() {
        if (!_streamFinished)
            return
        if (typewriter.active)
            return
        _setContent(_pendingResult, true)
        _finishStreaming(true)
        _streamFinished = false
    }

    function _restorePreOptimize() {
        typewriter.stop()
        _aiWaiting = false
        _waitingFirstChunk = false
        _streamFinished = false
        _setContent(_preOptimizeContent, _preOptimizeContent !== _loadedContent)
    }

    function _finishStreaming(success) {
        _aiWaiting = false
        _waitingFirstChunk = false
        textArea.readOnly = false
        if (success)
            previewArea.text = _content
        aiOptimizeDialog.finishOptimizing()
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
            if (_streamFinished || typewriter.active || _waitingFirstChunk)
                return
            _loadedContent = _content
            _dirty = false
        }

        function onOptimize_started() {
            _previewMode = false
            _preOptimizeContent = textArea.text
            _pendingResult = ""
            _aiWaiting = true
            _waitingFirstChunk = true
            _streamFinished = false
            typewriter.stop()
            textArea.readOnly = true
        }

        function onOptimize_chunk(delta) {
            if (_waitingFirstChunk) {
                _waitingFirstChunk = false
                _aiWaiting = false
                typewriter.beginReplace()
            }
            typewriter.feed(delta)
        }

        function onOptimize_finished(result) {
            _previewMode = false
            _pendingResult = result
            _streamFinished = true
            _loadedContent = result
            bridge.storyOutline.save(result)
            _tryCompleteOutlineStream()
        }

        function onOptimize_failed(error) {
            _restorePreOptimize()
            _finishStreaming(false)
            alertDialog.error("错误", "优化失败：" + error)
        }

        function onBridge_error(msg) {
            if (_aiWaiting || _waitingFirstChunk || typewriter.active || _streamFinished)
                _restorePreOptimize()
            _finishStreaming(false)
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
                icon.source: bridge.storyOutline.isOptimizing ? "" : "qrc:/resources/icons/auto_awesome.svg"
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
                    color: bridge.storyOutline.isOptimizing
                        ? "#FF9800"
                        : (parent.enabled ? (parent.pressed ? "#E65100" : (parent.hovered ? "#FB8C00" : "#FF9800")) : "#BDBDBD")
                }

                BusyIndicator {
                    anchors.centerIn: parent
                    width: 24
                    height: 24
                    visible: bridge.storyOutline.isOptimizing
                    running: bridge.storyOutline.isOptimizing
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

            Item {
                ScrollView {
                    id: editScrollView
                    anchors.fill: parent
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
                            if (_previewMode || textArea.readOnly)
                                return
                            _content = text
                            _dirty = (_content !== _loadedContent)
                        }
                    }
                }

                Comp.EditorWaitingOverlay {
                    anchors.fill: parent
                    visible: page._aiWaiting
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

    Comp.TypewriterController {
        id: typewriter
        target: textArea
        onTextUpdated: page._syncTypedContent()
        onDrained: page._tryCompleteOutlineStream()
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
