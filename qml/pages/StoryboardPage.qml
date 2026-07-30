import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs as QtDialogs
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: page
    property int projectId: -1
    property bool _showDetail: false
    property int _editingShotId: -1
    property var _relatedVideos: []

    signal backClicked()

    onProjectIdChanged: {
        if (projectId > 0) {
            bridge.storyboard.load_for_project(projectId)
            _showDetail = false
        }
    }

    Connections {
        target: bridge.storyboard
        function onShot_saved() {
            alertDialog.info("成功", "分镜已保存")
            _showDetail = false
        }
        function onShot_deleted() {
            alertDialog.info("成功", "分镜已删除")
            _showDetail = false
        }
        function onStoryboard_generated(shotCount) {
            alertDialog.info("成功", "分镜已生成，共 " + shotCount + " 个镜头")
        }
        function onStoryboard_generation_failed(error) {
            alertDialog.error("错误", "生成分镜失败：" + error)
        }
        function onDesign_image_ready(shotId, path) {
            alertDialog.info("成功", "设计图已生成")
            if (_showDetail) _loadRelatedVideos()
        }
        function onDesign_image_failed(error) {
            alertDialog.error("错误", "设计图生成失败：" + error)
        }
        function onBatch_progress(current, total, message) {
            console.log("批量进度：", message)
        }
        function onBatch_done(successCount, total) {
            alertDialog.info("完成", "批量设计图生成完成：成功 " + successCount + " / 总共 " + total)
        }
        function onError(msg) {
            alertDialog.error("错误", msg)
        }
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: _showDetail ? 1 : 0

        // ═══════════ 0: 分镜列表视图 ═══════════
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Comp.PageHeader {
                    title: "分镜编辑"
                    Layout.fillWidth: true
                    onBackClicked: page.backClicked()

                    Button {
                        Layout.preferredHeight: 34
                        text: "批量生成视频"
                        highlighted: true
                        enabled: bridge.storyboard.model.count > 0
                        topPadding: 6
                        bottomPadding: 6
                        leftPadding: 12
                        rightPadding: 12
                        onClicked: alertDialog.info("提示", "批量视频生成功能开发中")
                    }

                    Button {
                        Layout.preferredHeight: 34
                        text: "批量设计图"
                        enabled: bridge.storyboard.model.count > 0
                        topPadding: 6
                        bottomPadding: 6
                        leftPadding: 12
                        rightPadding: 12
                        onClicked: {
                            confirmDialog.confirm(
                                "确定要为所有分镜生成设计图吗？这可能需要较长时间。",
                                function() { bridge.storyboard.batch_generate_design_images(page.projectId) }
                            )
                        }
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
                        width: ListView.view.width - 4
                        shotId: model.shotId || 0
                        sceneNumber: model.sceneNumber || 0
                        shotNumber: model.shotNumber || 0
                        visualContent: model.visualContent || ""
                        designImage: model.designImagePath || ""
                        cameraMovement: model.cameraMovement || ""
                        duration: model.duration || 0
                        onClicked: {
                            _editingShotId = model.shotId
                            bridge.storyboard.load_shot(model.shotId)
                            _showDetail = true
                            _loadRelatedVideos()
                        }
                        onGenerateVideoClicked: {
                            alertDialog.info("提示", "单个视频生成功能开发中")
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

        // ═══════════ 1: 分镜详情编辑视图 ═══════════
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Comp.PageHeader {
                    title: "场" + bridge.storyboard.curSceneNumber + " 镜" + bridge.storyboard.curShotNumber
                    Layout.fillWidth: true
                    onBackClicked: {
                        _showDetail = false
                        bridge.storyboard.load_for_project(page.projectId)
                    }

                    Button {
                        Layout.preferredHeight: 34
                        text: "查看提示词"
                        topPadding: 6
                        bottomPadding: 6
                        leftPadding: 12
                        rightPadding: 12
                        onClicked: _showPromptPreview()
                    }

                    Button {
                        Layout.preferredHeight: 34
                        text: "保存"
                        highlighted: true
                        topPadding: 6
                        bottomPadding: 6
                        leftPadding: 12
                        rightPadding: 12
                        onClicked: _saveCurrentShot()
                    }

                    Button {
                        Layout.preferredHeight: 34
                        text: "删除"
                        topPadding: 6
                        bottomPadding: 6
                        leftPadding: 12
                        rightPadding: 12
                        onClicked: confirmDialog.confirm(
                            "确定要删除此分镜吗？",
                            function() { bridge.storyboard.delete_shot(_editingShotId) }
                        )
                    }
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    ColumnLayout {
                        width: parent.width
                        spacing: 16

                        Item { width: 1; height: 8 }

                        // 基本信息卡片
                        Pane {
                            Layout.fillWidth: true
                            Layout.leftMargin: 24
                            Layout.rightMargin: 24
                            padding: 16


                            GridLayout {
                                anchors.fill: parent
                                columns: 4
                                columnSpacing: 16
                                rowSpacing: 12

                                Label { text: "场次/镜头："; font.pixelSize: Theme.fontSizeMedium }
                                Label {
                                    text: "第" + bridge.storyboard.curSceneNumber + "场 / 第" + bridge.storyboard.curShotNumber + "镜"
                                    font.pixelSize: Theme.fontSizeMedium; font.bold: true
                                }
                                Item { Layout.fillWidth: true }
                                Item { Layout.fillWidth: true }

                                Label { text: "景别："; font.pixelSize: Theme.fontSizeMedium }
                                ComboBox {
                                    id: shotSizeCombo
                                    model: ["特写", "近景", "中景", "全景", "远景", "大远景"]
                                    currentIndex: bridge.storyboard.curShotSizeIndex
                                    Layout.preferredWidth: 160
                                }
                                Item { Layout.fillWidth: true }
                                Item { Layout.fillWidth: true }

                                Label { text: "运镜方式："; font.pixelSize: Theme.fontSizeMedium }
                                Comp.AppTextField {
                                    id: cameraInput
                                    text: bridge.storyboard.curCameraMovement
                                    placeholderText: "如：固定、慢推、跟拍、摇镜"
                                    Layout.fillWidth: true
                                    Layout.columnSpan: 3
                                }

                                Label { text: "时长（秒）："; font.pixelSize: Theme.fontSizeMedium }
                                SpinBox {
                                    id: durationSpin
                                    from: 0; to: 600; stepSize: 5
                                    value: Math.round(bridge.storyboard.curDuration * 10)
                                    property real realValue: value / 10.0
                                    textFromValue: function(v, l) { return (v / 10.0).toFixed(1) }
                                    valueFromText: function(t, l) { return parseFloat(t) * 10 }
                                    Layout.preferredWidth: 160
                                }
                                Item { Layout.fillWidth: true }
                                Item { Layout.fillWidth: true }
                            }
                        }

                        // 设计图区域
                        RowLayout {
                            Layout.leftMargin: 24
                            Layout.rightMargin: 24
                            spacing: 16

                            Rectangle {
                                width: 200; height: 112; radius: Theme.radiusMedium
                                Image {
                                    anchors.fill: parent
                                    source: bridge.storyboard.curDesignImage ? "file:///" + bridge.storyboard.curDesignImage : ""
                                    fillMode: Image.PreserveAspectCrop
                                    visible: source !== ""
                                }
                                Label {
                                    anchors.centerIn: parent
                                    text: "暂无设计图"
                                    visible: !bridge.storyboard.curDesignImage
                                }
                            }

                            ColumnLayout {
                                spacing: 8
                                Button {
                                    text: "AI 生成设计图"
                                    highlighted: true
                                    onClicked: bridge.storyboard.generate_design_image(_editingShotId, page.projectId)
                                }
                                Button {
                                    text: "上传图片"
                                    onClicked: designImageDialog.open()
                                }
                                Label {
                                    text: "根据画面描述自动生成，或手动上传"
                                    font.pixelSize: Theme.fontSizeSmall
                                }
                            }
                            Item { Layout.fillWidth: true }
                        }

                        // 画面内容
                        Label {
                            text: "画面内容描述"
                            font.pixelSize: Theme.fontSizeMedium; font.bold: true
                        }
                        ScrollView {
                            Layout.fillWidth: true; Layout.preferredHeight: 120
                            Layout.leftMargin: 24; Layout.rightMargin: 24; clip: true
                            TextArea {
                                id: visualEdit
                                text: bridge.storyboard.curVisualContent
                                placeholderText: "描述镜头中的人物、动作、环境细节..."
                                wrapMode: TextArea.Wrap; font.pixelSize: Theme.fontSizeMedium
                            }
                        }

                        // 台词
                        Label {
                            text: "台词/对白"
                            font.pixelSize: Theme.fontSizeMedium; font.bold: true
                        }
                        ScrollView {
                            Layout.fillWidth: true; Layout.preferredHeight: 80
                            Layout.leftMargin: 24; Layout.rightMargin: 24; clip: true
                            TextArea {
                                id: dialogueEdit
                                text: bridge.storyboard.curDialogue
                                placeholderText: "角色对话内容..."
                                wrapMode: TextArea.Wrap; font.pixelSize: Theme.fontSizeMedium
                            }
                        }

                        // 音效
                        Label {
                            text: "音效"
                            font.pixelSize: Theme.fontSizeMedium; font.bold: true
                        }
                        Comp.AppTextField {
                            id: soundEffectInput
                            text: bridge.storyboard.curSoundEffect
                            placeholderText: "环境音、特效音、背景音乐提示..."
                            Layout.fillWidth: true; Layout.leftMargin: 24; Layout.rightMargin: 24
                        }

                        // 备注
                        Label {
                            text: "备注"
                            font.pixelSize: Theme.fontSizeMedium; font.bold: true
                        }
                        ScrollView {
                            Layout.fillWidth: true; Layout.preferredHeight: 60
                            Layout.leftMargin: 24; Layout.rightMargin: 24; clip: true
                            TextArea {
                                id: notesEdit
                                text: bridge.storyboard.curNotes
                                placeholderText: "其他说明..."
                                wrapMode: TextArea.Wrap; font.pixelSize: Theme.fontSizeMedium
                            }
                        }

                        // ── 关联视频 ──
                        Label {
                            text: "关联视频"
                            font.pixelSize: Theme.fontSizeMedium; font.bold: true
                            Layout.topMargin: 8
                        }

                        ColumnLayout {
                            Layout.leftMargin: 24; Layout.rightMargin: 24
                            spacing: 8

                            Repeater {
                                model: _relatedVideos
                                delegate: VideoRowDelegate {
                                    Layout.fillWidth: true
                                    videoData: modelData
                                    onPlayClicked: bridge.play_video(modelData.filePath)
                                    onSetFeaturedClicked: {
                                        bridge.media.set_featured(modelData.fileId, _editingShotId)
                                        _loadRelatedVideos()
                                    }
                                    onDeleteClicked: {
                                        confirmDialog.confirm(
                                            "确定要删除此视频吗？",
                                            function() {
                                                bridge.media.delete_file(modelData.fileId)
                                                _loadRelatedVideos()
                                            }
                                        )
                                    }
                                }
                            }

                            Label {
                                visible: _relatedVideos.length === 0
                                text: "暂无关联视频"
                                font.pixelSize: Theme.fontSizeSmall
                                Layout.alignment: Qt.AlignHCenter
                                Layout.topMargin: 8; Layout.bottomMargin: 8
                            }
                        }

                        Item { width: 1; height: 16 }
                    }
                }
            }
        }
    }

    // ── 对话框 ──
    Dialogs.AlertDialog { id: alertDialog }
    Dialogs.ConfirmDialog { id: confirmDialog }

    // 设计图上传
    QtDialogs.FileDialog {
        id: designImageDialog
        title: "选择设计图"
        fileMode: QtDialogs.FileDialog.OpenFile
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)", "所有文件 (*)"]
        onAccepted: {
            var p = selectedFile.toString()
            if (p.startsWith("file:///")) p = p.substring(8)
            bridge.storyboard.upload_design_image(_editingShotId, p)
        }
    }

    // 提示词预览对话框
    Dialog {
        id: promptDialog
        modal: true
        title: "视频生成提示词预览"
        width: 560
        height: 480
        anchors.centerIn: parent
        standardButtons: Dialog.Close

        ScrollView {
            anchors.fill: parent
            clip: true
            TextArea {
                id: promptText
                readOnly: true
                wrapMode: TextArea.Wrap
                font.pixelSize: Theme.fontSizeSmall
                font.family: "Consolas, monospace"
                padding: 12
            }
        }
    }

    // ── 关联视频行组件 ──
    component VideoRowDelegate: Pane {
        property var videoData: ({})
        signal playClicked()
        signal setFeaturedClicked()
        signal deleteClicked()

        padding: 8

        RowLayout {
            anchors.fill: parent
            spacing: 10

            // 封面标记
            Image {
                source: "qrc:/resources/icons/star.svg"
                sourceSize.width: 20
                sourceSize.height: 20
                visible: videoData.featured
            }

            // 缩略图
            Rectangle {
                width: 64; height: 48; radius: 4
                clip: true
                Image {
                    anchors.fill: parent
                    source: videoData.thumbnailPath ? "file:///" + videoData.thumbnailPath : ""
                    fillMode: Image.PreserveAspectCrop
                    visible: source !== ""
                }
                Image {
                    anchors.centerIn: parent
                    source: "qrc:/resources/icons/movie.svg"
                    sourceSize.width: 24
                    sourceSize.height: 24
                    visible: !videoData.thumbnailPath
                }
            }

            // 文件信息
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: videoData.fileName || ""
                    font.pixelSize: Theme.fontSizeLarge
                    font.bold: true
                }
                Label {
                    text: _formatVideoMeta(videoData)
                    font.pixelSize: Theme.fontSizeSmall
                }
            }

            Button {
                text: "播放"; flat: true
                onClicked: playClicked()
            }
            Button {
                text: "设为封面"
                visible: !videoData.featured
                onClicked: setFeaturedClicked()
            }
            Button {
                text: "删除"; flat: true
                onClicked: deleteClicked()
            }
        }
    }

    // ── 内部函数 ──
    function _saveCurrentShot() {
        bridge.storyboard.save_shot(
            _editingShotId,
            shotSizeCombo.currentIndex,
            cameraInput.text,
            visualEdit.text,
            durationSpin.realValue,
            dialogueEdit.text,
            soundEffectInput.text,
            notesEdit.text,
            bridge.storyboard.curDesignImage
        )
    }

    function _loadRelatedVideos() {
        var json = bridge.storyboard.get_related_videos(_editingShotId)
        _relatedVideos = JSON.parse(json)
    }

    function _showPromptPreview() {
        var prompt = bridge.storyboard.preview_prompt(_editingShotId, page.projectId)
        if (prompt) {
            promptText.text = prompt
            promptDialog.open()
        } else {
            alertDialog.info("提示", "画面内容为空，无法生成提示词")
        }
    }

    function _formatVideoMeta(v) {
        var parts = []
        if (v.duration > 0) {
            var mins = Math.floor(v.duration / 60)
            var secs = Math.floor(v.duration % 60)
            parts.push(mins > 0 ? (mins + ":" + (secs < 10 ? "0" : "") + secs) : (secs + "s"))
        }
        if (v.width > 0 && v.height > 0) {
            parts.push(v.width + "×" + v.height)
        }
        return parts.join(" · ")
    }
}
