import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs as QtDialogs
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: page
    property int projectId: -1
    property bool _showDetail: false
    property int _editingShotId: -1
    property bool _multiSelect: false
    property var _selectedIds: []
    property string _projectName: ""
    property bool _exporting: false
    property var generatingDesignShotIds: []
    property var generatingVideoShotIds: []

    signal backClicked()
    signal navigateToMediaLibrary(int projectId)

    Shortcut {
        sequence: "Escape"
        enabled: _multiSelect
        onActivated: {
            _multiSelect = false
            _selectedIds = []
        }
    }

    onProjectIdChanged: {
        if (projectId > 0) {
            var info = JSON.parse(bridge.projects.get_project_info(projectId))
            _projectName = info.name || ""
            bridge.storyboard.load_for_project(projectId)
            _showDetail = false
            _multiSelect = false
            _selectedIds = []
        }
    }

    function openShotDetail(shotId) {
        if (shotId > 0) {
            _editingShotId = shotId
            _showDetail = true
            _multiSelect = false
            _selectedIds = []
        }
    }

    Connections {
        target: bridge.storyboard
        function onShot_saved() {
        }
        function onShot_deleted() {
            _showDetail = false
            _editingShotId = -1
        }
        function onStoryboard_generated(shotCount) {
            aiOptimizeDialog.finishOptimizing()
        }
        function onStoryboard_optimized(shotCount) {
            aiOptimizeDialog.finishOptimizing()
        }
        function onStoryboard_generation_failed(error) {
            aiOptimizeDialog.finishOptimizing()
            var msg = error ? String(error) : "未知错误"
            alertDialog.error("错误", "生成分镜失败：" + msg)
        }
        function onDesign_image_ready(shotId, path) {
        }
        function onDesign_image_started(shotId) {
            var ids = page.generatingDesignShotIds.slice()
            if (ids.indexOf(shotId) === -1) {
                ids.push(shotId)
                page.generatingDesignShotIds = ids
            }
        }
        function onDesign_image_finished(shotId) {
            var ids = page.generatingDesignShotIds.slice()
            var index = ids.indexOf(shotId)
            if (index !== -1) {
                ids.splice(index, 1)
                page.generatingDesignShotIds = ids
            }
        }
        function onDesign_image_failed(error) {
            var msg = error ? String(error) : "未知错误"
            alertDialog.error("错误", "设计图生成失败：" + msg)
        }
        function onVideo_generation_started(shotId) {
            var ids = page.generatingVideoShotIds.slice()
            if (ids.indexOf(shotId) === -1) {
                ids.push(shotId)
                page.generatingVideoShotIds = ids
            }
        }
        function onVideo_generation_finished(shotId) {
            var ids = page.generatingVideoShotIds.slice()
            var index = ids.indexOf(shotId)
            if (index !== -1) {
                ids.splice(index, 1)
                page.generatingVideoShotIds = ids
            }
        }
        function onVideo_generation_failed(shotId, error) {
            var ids = page.generatingVideoShotIds.slice()
            var index = ids.indexOf(shotId)
            if (index !== -1) {
                ids.splice(index, 1)
                page.generatingVideoShotIds = ids
            }
            var msg = error ? String(error) : "未知错误"
            alertDialog.error("错误", "视频生成失败：" + msg)
        }
        function onBatch_progress(current, total, message) {
        }
        function onBatch_done(successCount, total) {
        }
        function onBridge_error(msg) {
            aiOptimizeDialog.finishOptimizing()
            var safeMsg = msg ? String(msg) : "未知错误"
            alertDialog.error("错误", safeMsg)
        }
    }

    Connections {
        target: bridge.media
        function onExport_progress(percent, message) {
            if (!page._exporting) return
            exportMessage.text = message + " (" + percent + "%)"
        }
        function onExport_finished(outputPath) {
            if (!page._exporting) return
            page._exporting = false
            exportOverlay.visible = false
            alertDialog.info("导出成功", "视频已保存到：\n" + outputPath)
        }
        function onExport_failed(error) {
            if (!page._exporting) return
            page._exporting = false
            exportOverlay.visible = false
            alertDialog.error("导出失败", error)
        }
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: _showDetail ? 1 : 0

        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Comp.PageHeader {
                    projectName: _projectName
                    title: "分镜"
                    titleSuffix: "共" + bridge.storyboard.model.count + "镜"
                    Layout.fillWidth: true
                    onBackClicked: page.backClicked()

                    Button {
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 34
                        flat: true
                        display: AbstractButton.IconOnly
                        icon.source: "qrc:/resources/icons/movie_creation.svg"
                        icon.width: 20
                        icon.height: 20
                        topPadding: 7
                        bottomPadding: 7
                        leftPadding: 7
                        rightPadding: 7
                        ToolTip.visible: hovered
                        ToolTip.text: "导出样片"
                        onClicked: {
                            var projectInfo = JSON.parse(bridge.projects.get_project_info(page.projectId))
                            if (projectInfo && projectInfo.name) {
                                saveDialog.currentFile = "file:///" + projectInfo.name + ".mp4"
                            }
                            saveDialog.open()
                        }

                        background: Rectangle {
                            anchors.fill: parent
                            radius: Theme.radiusSmall
                            color: parent.hovered
                                ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                                : "transparent"
                        }
                    }

                    Button {
                        visible: _multiSelect && _selectedIds.length > 0
                        Layout.preferredHeight: 34
                        text: "虚拟拍摄"
                        highlighted: true
                        enabled: bridge.storyboard.model.count > 0
                        topPadding: 6
                        bottomPadding: 6
                        leftPadding: 12
                        rightPadding: 12
                        onClicked: {
                            var selectedIdsCopy = _selectedIds.slice()
                            videoGenerateDialog.show(page.projectId, selectedIdsCopy, function(promptExtendEnabled, useStoryboardDesign, useCharacterDesign, negativePrompt, usePrevShotLastFrame, crossScenePrevFrame) {
                                bridge.storyboard.batch_generate_videos(
                                    page.projectId,
                                    JSON.stringify(selectedIdsCopy),
                                    promptExtendEnabled,
                                    useStoryboardDesign,
                                    useCharacterDesign,
                                    negativePrompt,
                                    usePrevShotLastFrame,
                                    crossScenePrevFrame
                                )
                            })
                        }
                    }

                    Button {
                        visible: _multiSelect && _selectedIds.length > 0
                        Layout.preferredHeight: 34
                        text: "设计场景"
                        enabled: bridge.storyboard.model.count > 0
                        topPadding: 6
                        bottomPadding: 6
                        leftPadding: 12
                        rightPadding: 12
                        onClicked: {
                            var selectedIdsCopy = _selectedIds.slice()
                            confirmDialog.confirm(
                                "确定要为选中的 " + selectedIdsCopy.length + " 个分镜生成设计图吗？",
                                function() {
                                    bridge.storyboard.batch_generate_design_images(page.projectId, JSON.stringify(selectedIdsCopy))
                                }
                            )
                        }
                    }

                    Button {
                        visible: _multiSelect && _selectedIds.length > 0
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 34
                        display: AbstractButton.IconOnly
                        icon.source: "qrc:/resources/icons/delete.svg"
                        icon.width: 20
                        icon.height: 20
                        topPadding: 7
                        bottomPadding: 7
                        leftPadding: 7
                        rightPadding: 7
                        ToolTip.visible: hovered
                        ToolTip.text: "删除选中"

                        background: Rectangle {
                            anchors.fill: parent
                            radius: Theme.radiusSmall
                            color: parent.hovered
                                ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                                : "transparent"
                        }

                        onClicked: confirmDialog.confirm(
                            "确定要删除选中的 " + _selectedIds.length + " 个分镜吗？",
                            function() {
                                for (var i = 0; i < _selectedIds.length; i++)
                                    bridge.storyboard.delete_shot(_selectedIds[i])
                                _selectedIds = []
                                _multiSelect = false
                            }
                        )
                    }

                    Button {
                        visible: _multiSelect
                        Layout.preferredHeight: 34
                        text: "全选"
                        topPadding: 6
                        bottomPadding: 6
                        leftPadding: 12
                        rightPadding: 12
                        onClicked: {
                            var ids = []
                            var m = bridge.storyboard.model
                            for (var i = 0; i < m.count; i++)
                                ids.push(m.data(m.index(i, 0), 257))
                            _selectedIds = _selectedIds.length === ids.length ? [] : ids
                        }
                    }

                    Button {
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 34
                        display: AbstractButton.IconOnly
                        icon.source: _multiSelect ? "qrc:/resources/icons/close.svg" : "qrc:/resources/icons/checklist.svg"
                        icon.width: 20
                        icon.height: 20
                        topPadding: 7
                        bottomPadding: 7
                        leftPadding: 7
                        rightPadding: 7
                        ToolTip.visible: hovered
                        ToolTip.text: _multiSelect ? "取消" : "多选"

                        background: Rectangle {
                            anchors.fill: parent
                            radius: Theme.radiusSmall
                            color: parent.hovered
                                ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                                : "transparent"
                        }

                        onClicked: {
                            if (_multiSelect) {
                                _multiSelect = false
                                _selectedIds = []
                            } else {
                                _multiSelect = true
                            }
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
                        enabled: !bridge.storyboard.isOptimizing
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
                            aiOptimizeDialog.show("AI 优化分镜", "请输入优化要求（如增减镜头、调整景别、修改画面描述等）...", "开始优化")
                        }
                    }

                    Button {
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 34
                        display: AbstractButton.IconOnly
                        icon.source: "qrc:/resources/icons/arrow_forward.svg"
                        icon.width: 20
                        icon.height: 20
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

                        onClicked: page.navigateToMediaLibrary(page.projectId)
                    }
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: 16
                    model: bridge.storyboard.model
                    spacing: 8
                    clip: true

                    delegate: Comp.StoryboardCard {
                        width: ListView.view.width - 32
                        shotId: model.shotId || 0
                        sceneNumber: model.sceneNumber || 0
                        shotNumber: model.shotNumber || 0
                        visualContent: model.visualContent || ""
                        designImage: model.designImagePath || ""
                        designImageBusy: generatingDesignShotIds.indexOf(String(model.shotId)) !== -1
                        videoGenerationBusy: generatingVideoShotIds.indexOf(String(model.shotId)) !== -1
                        cameraMovement: model.cameraMovement || ""
                        duration: model.duration || 0
                        multiSelect: _multiSelect
                        selected: _selectedIds.indexOf(model.shotId) >= 0
                        onClicked: {
                            if (_multiSelect) {
                                var ids = _selectedIds.slice()
                                var idx = ids.indexOf(model.shotId)
                                if (idx >= 0) ids.splice(idx, 1)
                                else ids.push(model.shotId)
                                _selectedIds = ids
                            } else {
                                _editingShotId = model.shotId
                                _showDetail = true
                            }
                        }
                    }

                    Comp.EmptyState {
                        visible: bridge.storyboard.model.count === 0
                        anchors.centerIn: parent
                        text: "暂无分镜数据"
                    }
                }
            }
        }

        StoryboardDetailPage {
            projectId: page.projectId
            projectName: _projectName
            shotId: _editingShotId
            generatingDesignShotIds: page.generatingDesignShotIds
            onBackClicked: {
                _showDetail = false
                _editingShotId = -1
                bridge.storyboard.load_for_project(page.projectId)
            }
        }
    }

    Dialogs.AlertDialog { id: alertDialog }
    Dialogs.ConfirmDialog { id: confirmDialog }
    Dialogs.VideoGenerateDialog { id: videoGenerateDialog }
    Dialogs.ImagePreviewDialog { id: imagePreviewDialog }
    Dialogs.AIOptimizeDialog {
        id: aiOptimizeDialog
        onOptimizeRequested: function(userInput) {
            bridge.storyboard.optimize_with_ai(userInput, page.projectId)
        }
    }

    QtDialogs.FileDialog {
        id: saveDialog
        title: "导出视频"
        fileMode: QtDialogs.FileDialog.SaveFile
        defaultSuffix: "mp4"
        nameFilters: ["视频文件 (*.mp4)"]
        onAccepted: {
            var path = selectedFile.toString()
            if (path.startsWith("file:///")) path = path.substring(8)
            exportMessage.text = "正在准备导出..."
            exportOverlay.visible = true
            page._exporting = true
            bridge.media.export_project_video(page.projectId, path)
        }
    }

    Rectangle {
        id: exportOverlay
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.5)
        visible: false
        z: 999

        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 16

            Comp.SpinnerOverlay {
                Layout.alignment: Qt.AlignHCenter
                width: 48
                height: 48
            }

            Label {
                id: exportMessage
                text: "正在导出视频..."
                font.pixelSize: Theme.fontSizeMedium
                color: "white"
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }
}
