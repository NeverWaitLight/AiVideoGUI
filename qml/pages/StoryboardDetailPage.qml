import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs as QtDialogs
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: detailPage
    property int projectId: -1
    property string projectName: ""
    property int shotId: -1
    property var _relatedVideos: []
    property int _designImageVersion: 0

    signal backClicked()

    onShotIdChanged: {
        if (shotId > 0) {
            bridge.storyboard.load_shot(shotId)
            _loadRelatedVideos()
        }
    }

    Connections {
        target: bridge.storyboard
        function onDesign_image_ready(shotId, path) {
            console.log("[StoryboardDetailPage] onDesign_image_ready:", shotId, path)
            _designImageVersion++
            _loadRelatedVideos()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Comp.PageHeader {
            projectName: detailPage.projectName
            title: bridge.storyboard.curSceneNumber + "场" + bridge.storyboard.curShotNumber + "镜"
            Layout.fillWidth: true
            onBackClicked: detailPage.backClicked()

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
                    function() { bridge.storyboard.batch_generate_videos(detailPage.projectId, JSON.stringify([bridge.storyboard.curShotId])) }
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

                    Item { width: 1; height: 12 }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.leftMargin: 20
                        Layout.rightMargin: 20
                        spacing: 16

                        GridLayout {
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: 10
                            rowSpacing: 6

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
                        }

                        ColumnLayout {
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

                                MouseArea {
                                    anchors.fill: parent
                                    enabled: bridge.storyboard.curDesignImage !== ""
                                    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                                    onClicked: if (bridge.storyboard.curDesignImage) imagePreviewDialog.show(bridge.storyboard.curDesignImage)
                                }
                            }

                            RowLayout {
                                spacing: 6
                                Layout.preferredWidth: 160
                                Button {
                                    text: "AI 生成"
                                    highlighted: true
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30
                                    onClicked: {
                                        console.log("[StoryboardDetailPage] AI生成 clicked: curShotId=", bridge.storyboard.curShotId, "projectId=", detailPage.projectId)
                                        bridge.storyboard.generate_design_image(bridge.storyboard.curShotId, detailPage.projectId)
                                    }
                                }
                                Button {
                                    text: "上传"
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30
                                    onClicked: designImageDialog.open()
                                }
                            }

                            Button {
                                text: "删除"
                                flat: true
                                Layout.preferredWidth: 160
                                Layout.preferredHeight: 30
                                visible: !!bridge.storyboard.curDesignImage
                                onClicked: confirmDialog.confirm(
                                    "确定要删除设计图吗？",
                                    function() { bridge.storyboard.delete_design_image(bridge.storyboard.curShotId) }
                                )
                            }
                        }
                    }

                    Item { width: 1; height: 12 }

                    GridLayout {
                        Layout.fillWidth: true
                        Layout.leftMargin: 20
                        Layout.rightMargin: 20
                        columns: 2
                        columnSpacing: 10
                        rowSpacing: 6

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

    Dialogs.AlertDialog { id: alertDialog }
    Dialogs.ConfirmDialog { id: confirmDialog }
    Dialogs.ImagePreviewDialog { id: imagePreviewDialog }

    QtDialogs.FileDialog {
        id: designImageDialog
        title: "选择设计图"
        fileMode: QtDialogs.FileDialog.OpenFile
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)", "所有文件 (*)"]
        onAccepted: {
            var p = selectedFile.toString()
            if (p.startsWith("file:///")) p = p.substring(8)
            bridge.storyboard.upload_design_image(detailPage.shotId, p)
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
            detailPage.shotId,
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
        var json = bridge.storyboard.get_related_videos(detailPage.shotId)
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
