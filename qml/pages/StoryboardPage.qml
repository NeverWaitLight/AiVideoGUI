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
    property var _relatedVideos: []
    property bool _multiSelect: false
    property var _selectedIds: []
    property int _designImageVersion: 0

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
            bridge.storyboard.load_for_project(projectId)
            _showDetail = false
            _multiSelect = false
            _selectedIds = []
        }
    }

    Connections {
        target: bridge.storyboard
        function onShot_saved() {
            alertDialog.info("成功", "分镜已保存")
        }
        function onShot_deleted() {
            alertDialog.info("成功", "分镜已删除")
            _showDetail = false
            _editingShotId = -1
        }
        function onStoryboard_generated(shotCount) {
            aiOptimizeDialog.finishOptimizing()
            alertDialog.info("成功", "分镜已生成，共 " + shotCount + " 个镜头")
        }
        function onStoryboard_optimized(shotCount) {
            aiOptimizeDialog.finishOptimizing()
            alertDialog.info("成功", "分镜优化完成，共 " + shotCount + " 个镜头")
        }
        function onStoryboard_generation_failed(error) {
            aiOptimizeDialog.finishOptimizing()
            alertDialog.error("错误", "生成分镜失败：" + error)
        }
        function onDesign_image_ready(shotId, path) {
            alertDialog.info("成功", "设计图已生成")
            _designImageVersion++
            if (_showDetail) _loadRelatedVideos()
        }
        function onDesign_image_failed(error) {
            alertDialog.error("错误", "设计图生成失败：" + error)
        }
        function onBatch_progress(current, total, message) {
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

        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Comp.PageHeader {
                    title: "分镜"
                    subtitle: "共" + bridge.storyboard.model.count + "镜"
                    Layout.fillWidth: true
                    onBackClicked: page.backClicked()

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
                            confirmDialog.confirm(
                                "确定要为选中的 " + selectedIdsCopy.length + " 个分镜生成视频吗？",
                                function() {
                                    bridge.storyboard.batch_generate_videos(page.projectId, JSON.stringify(selectedIdsCopy))
                                }
                            )
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
                                bridge.storyboard.load_shot(model.shotId)
                                _showDetail = true
                                _loadRelatedVideos()
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

        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Comp.PageHeader {
                    title: bridge.storyboard.curSceneNumber + "场" + bridge.storyboard.curShotNumber + "镜"
                    Layout.fillWidth: true
                    onBackClicked: {
                        _showDetail = false
                        _editingShotId = -1
                        bridge.storyboard.load_for_project(page.projectId)
                    }

                    Button {
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 36
                        display: AbstractButton.IconOnly
                        icon.source: "qrc:/resources/icons/video_camera_back.svg"
                        icon.width: 20
                        icon.height: 20
                        icon.color: "white"
                        topPadding: 8
                        bottomPadding: 8
                        leftPadding: 8
                        rightPadding: 8
                        ToolTip.visible: hovered
                        ToolTip.text: "生成视频"

                        background: Rectangle {
                            anchors.fill: parent
                            radius: parent.width / 2
                            color: parent.pressed ? "#C62828" : (parent.hovered ? "#E53935" : "#F44336")
                        }

                        onClicked: confirmDialog.confirm(
                            "确定要为此分镜生成视频吗？",
                            function() { bridge.storyboard.batch_generate_videos(page.projectId, JSON.stringify([bridge.storyboard.curShotId])) }
                        )
                    }

                    Button {
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 34
                        display: AbstractButton.IconOnly
                        icon.source: "qrc:/resources/icons/save.svg"
                        icon.width: 20
                        icon.height: 20
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

                        onClicked: _saveCurrentShot()
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 0

                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.preferredWidth: 2
                        clip: true

                        ColumnLayout {
                            width: parent.width
                            spacing: 0

                            Item { width: 1; height: 8 }

                            RowLayout {
                                Layout.fillWidth: true
                                Layout.leftMargin: 20
                                Layout.rightMargin: 20
                                spacing: 16
                                Layout.preferredHeight: childrenRect.height

                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    columnSpacing: 10
                                    rowSpacing: 6

                                    Label { text: "场次/镜头："; font.pixelSize: Theme.fontSizeSmall }
                                    Label {
                                        text: bridge.storyboard.curSceneNumber + "场" + bridge.storyboard.curShotNumber + "镜"
                                        font.pixelSize: Theme.fontSizeSmall; font.bold: true
                                    }

                                    Label { text: "景别："; font.pixelSize: Theme.fontSizeSmall }
                                    ComboBox {
                                        id: shotSizeCombo
                                        model: ["特写", "近景", "中景", "全景", "远景", "大远景"]
                                        currentIndex: bridge.storyboard.curShotSizeIndex
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 32
                                        font.pixelSize: Theme.fontSizeSmall
                                    }

                                    Label { text: "运镜："; font.pixelSize: Theme.fontSizeSmall }
                                    Comp.AppTextField {
                                        id: cameraInput
                                        text: bridge.storyboard.curCameraMovement
                                        placeholderText: "固定、慢推、跟拍"
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 32
                                    }

                                    Label { text: "时长（秒）："; font.pixelSize: Theme.fontSizeSmall }
                                    SpinBox {
                                        id: durationSpin
                                        from: 0; to: 600; stepSize: 5
                                        value: Math.round(bridge.storyboard.curDuration * 10)
                                        property real realValue: value / 10.0
                                        textFromValue: function(v, l) { return (v / 10.0).toFixed(1) }
                                        valueFromText: function(t, l) { return parseFloat(t) * 10 }
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 32
                                    }

                                    Label { text: "Seed："; font.pixelSize: Theme.fontSizeSmall }
                                    RowLayout {
                                        spacing: 6
                                        Layout.fillWidth: true
                                        Comp.AppTextField {
                                            id: seedInput
                                            text: bridge.storyboard.curSeed
                                            placeholderText: "留空自动生成"
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 32
                                        }
                                        Button {
                                            text: "随机"
                                            Layout.preferredHeight: 32
                                            onClicked: seedInput.text = String(Math.floor(Math.random() * 2147483647))
                                        }
                                    }
                                }

                                RowLayout {
                                    spacing: 8
                                    Layout.alignment: Qt.AlignTop

                                    Rectangle {
                                        width: 160; height: 90; radius: Theme.radiusMedium
                                        color: "transparent"
                                        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.15)
                                        Image {
                                            anchors.fill: parent
                                            source: bridge.storyboard.curDesignImage
                                                ? "file:///" + bridge.storyboard.curDesignImage + "?v=" + _designImageVersion
                                                : ""
                                            fillMode: Image.PreserveAspectCrop
                                            visible: source !== ""
                                        }
                                        Label {
                                            anchors.centerIn: parent
                                            text: "暂无设计图"
                                            font.pixelSize: Theme.fontSizeSmall
                                            visible: !bridge.storyboard.curDesignImage
                                            opacity: 0.5
                                        }
                                    }

                                    ColumnLayout {
                                        spacing: 6
                                        Button {
                                            text: "AI 生成"
                                            highlighted: true
                                            Layout.preferredHeight: 30
                                            onClicked: bridge.storyboard.generate_design_image(bridge.storyboard.curShotId, page.projectId)
                                        }
                                        Button {
                                            text: "上传"
                                            Layout.preferredHeight: 30
                                            onClicked: designImageDialog.open()
                                        }
                                        Button {
                                            text: "删除"
                                            flat: true
                                            Layout.preferredHeight: 30
                                            visible: !!bridge.storyboard.curDesignImage
                                            onClicked: confirmDialog.confirm(
                                                "确定要删除设计图吗？",
                                                function() { bridge.storyboard.delete_design_image(bridge.storyboard.curShotId) }
                                            )
                                        }
                                    }
                                }
                            }

                            Item { width: 1; height: 12 }

                            Label {
                                text: "画面内容描述"
                                font.pixelSize: Theme.fontSizeSmall; font.bold: true
                                Layout.leftMargin: 20
                            }
                            ScrollView {
                                Layout.fillWidth: true; Layout.preferredHeight: 100
                                Layout.leftMargin: 20; Layout.rightMargin: 20; clip: true
                                TextArea {
                                    id: visualEdit
                                    text: bridge.storyboard.curVisualContent
                                    placeholderText: "描述镜头中的人物、动作、环境细节..."
                                    wrapMode: TextArea.Wrap; font.pixelSize: Theme.fontSizeSmall
                                }
                            }

                            Label {
                                text: "音效"
                                font.pixelSize: Theme.fontSizeSmall; font.bold: true
                                Layout.leftMargin: 20
                            }
                            ScrollView {
                                Layout.fillWidth: true; Layout.preferredHeight: 64
                                Layout.leftMargin: 20; Layout.rightMargin: 20; clip: true
                                TextArea {
                                    id: soundEffectEdit
                                    text: bridge.storyboard.curSoundEffect
                                    placeholderText: "脚步声、敲门声、物体坠地等特定声音效果..."
                                    wrapMode: TextArea.Wrap; font.pixelSize: Theme.fontSizeSmall
                                }
                            }

                            Label {
                                text: "环境音"
                                font.pixelSize: Theme.fontSizeSmall; font.bold: true
                                Layout.leftMargin: 20
                            }
                            ScrollView {
                                Layout.fillWidth: true; Layout.preferredHeight: 64
                                Layout.leftMargin: 20; Layout.rightMargin: 20; clip: true
                                TextArea {
                                    id: ambientSoundEdit
                                    text: bridge.storyboard.curAmbientSound
                                    placeholderText: "树叶沙沙声、城市嗡鸣声等环境背景声音..."
                                    wrapMode: TextArea.Wrap; font.pixelSize: Theme.fontSizeSmall
                                }
                            }

                            Label {
                                text: "背景音乐"
                                font.pixelSize: Theme.fontSizeSmall; font.bold: true
                                Layout.leftMargin: 20
                            }
                            ScrollView {
                                Layout.fillWidth: true; Layout.preferredHeight: 64
                                Layout.leftMargin: 20; Layout.rightMargin: 20; clip: true
                                TextArea {
                                    id: backgroundMusicEdit
                                    text: bridge.storyboard.curBackgroundMusic
                                    placeholderText: "温馨快乐氛围音乐、卡点音乐等情绪音乐提示..."
                                    wrapMode: TextArea.Wrap; font.pixelSize: Theme.fontSizeSmall
                                }
                            }

                            Label {
                                text: "备注"
                                font.pixelSize: Theme.fontSizeSmall; font.bold: true
                                Layout.leftMargin: 20
                            }
                            ScrollView {
                                Layout.fillWidth: true; Layout.preferredHeight: 48
                                Layout.leftMargin: 20; Layout.rightMargin: 20; clip: true
                                TextArea {
                                    id: notesEdit
                                    text: bridge.storyboard.curNotes
                                    placeholderText: "其他说明..."
                                    wrapMode: TextArea.Wrap; font.pixelSize: Theme.fontSizeSmall
                                }
                            }

                            Item { Layout.fillHeight: true }
                        }
                    }

                    Rectangle {
                        width: 1
                        Layout.fillHeight: true
                        color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.preferredWidth: 1
                        spacing: 0

                        Label {
                            text: "关联视频"
                            font.pixelSize: Theme.fontSizeSmall; font.bold: true
                            Layout.leftMargin: 16
                            Layout.topMargin: 8
                            Layout.bottomMargin: 4
                        }

                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.leftMargin: 12
                            Layout.rightMargin: 12
                            model: _relatedVideos
                            spacing: 6
                            clip: true

                            delegate: VideoRowDelegate {
                                width: ListView.view.width
                                videoData: modelData
                                onPlayClicked: bridge.play_video(modelData.filePath)
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

                            Label {
                                visible: _relatedVideos.length === 0
                                text: "暂无关联视频"
                                font.pixelSize: Theme.fontSizeSmall
                                anchors.centerIn: parent
                                opacity: 0.5
                            }
                        }
                    }
                }
            }
        }
    }

    Dialogs.AlertDialog { id: alertDialog }
    Dialogs.ConfirmDialog { id: confirmDialog }
    Dialogs.AIOptimizeDialog {
        id: aiOptimizeDialog
        onOptimizeRequested: function(userInput) {
            bridge.storyboard.optimize_with_ai(userInput, page.projectId)
        }
    }

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

    component VideoRowDelegate: Item {
        property var videoData: ({})
        signal playClicked()
        signal deleteClicked()

        implicitHeight: 60

        Rectangle {
            anchors.fill: parent
            anchors.leftMargin: 6
            anchors.rightMargin: 6
            anchors.topMargin: 3
            anchors.bottomMargin: 3
            radius: Theme.radiusSmall
            color: mouseArea.containsMouse ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.05) : "transparent"
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: playClicked()
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            anchors.topMargin: 6
            anchors.bottomMargin: 6
            spacing: 10

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

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: videoData.fileName || ""
                    font.pixelSize: Theme.fontSizeSmall
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                Label {
                    text: _formatVideoMeta(videoData)
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                }
            }

            Button {
                text: "删除"; flat: true
                Layout.preferredHeight: 30
                z: 1
                onClicked: deleteClicked()
            }
        }
    }

    function _saveCurrentShot() {
        bridge.storyboard.save_shot(
            _editingShotId,
            shotSizeCombo.currentIndex,
            cameraInput.text,
            visualEdit.text,
            durationSpin.realValue,
            soundEffectEdit.text,
            ambientSoundEdit.text,
            backgroundMusicEdit.text,
            notesEdit.text,
            bridge.storyboard.curDesignImage,
            seedInput.text
        )
    }

    function _loadRelatedVideos() {
        var json = bridge.storyboard.get_related_videos(_editingShotId)
        _relatedVideos = JSON.parse(json)
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
