import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs as QtDialogs
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: page
    property int projectId: -1
    property string _filterType: ""
    property string _searchText: ""

    signal backClicked()

    onProjectIdChanged: {
        if (projectId > 0) {
            bridge.media.load_project_files(projectId)
        }
    }

    Connections {
        target: bridge.media
        function onFiles_changed() {
            _reloadFiles()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Comp.PageHeader {
            title: "素材库"
            Layout.fillWidth: true
            onBackClicked: page.backClicked()

            ComboBox {
                id: typeFilter
                model: ["全部", "视频", "图片", "音频"]
                onCurrentTextChanged: {
                    _filterType = currentText === "全部" ? "" : currentText
                    _reloadFiles()
                }
            }

            Comp.AppTextField {
                id: searchInput
                placeholderText: "搜索文件名..."
                implicitWidth: 180
                onTextChanged: {
                    _searchText = text
                    _reloadFiles()
                }
            }

            Button {
                text: "导入"
                highlighted: true
                onClicked: fileDialog.open()
            }
        }

        Comp.CardGrid {
            id: mediaGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: mediaRepeater.count > 0
            sideMargin: 16
            cardSpacing: 16
            cardHeight: 210
            columns: 4

            Repeater {
                id: mediaRepeater
                model: bridge.media.model
                delegate: MediaCardDelegate {
                    width: mediaGrid.cardWidth
                    height: mediaGrid.cardHeight
                    fileId: model.fileId || ""
                    fileName: model.fileName || ""
                    fileType: model.fileType || ""
                    filePath: model.filePath || ""
                    thumbnailPath: model.thumbnailPath || ""
                    fileSize: model.fileSize || 0
                    duration: model.duration || 0
                    videoWidth: model.videoWidth || 0
                    videoHeight: model.videoHeight || 0
                    onPlayRequested: {
                        if (filePath) bridge.play_video(filePath)
                    }
                    onDeleteRequested: {
                        confirmDialog.confirm(
                            "确定要删除「" + fileName + "」吗？",
                            function() { bridge.media.delete_file(fileId) }
                        )
                    }
                    onOpenFolderRequested: {
                        if (filePath) bridge.open_folder(filePath)
                    }
                }
            }
        }

        Comp.EmptyState {
            visible: mediaRepeater.count === 0
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "素材库为空"
            buttonText: "导入文件"
            onButtonClicked: fileDialog.open()
        }
    }

    // ── 文件选择对话框 ──
    QtDialogs.FileDialog {
        id: fileDialog
        title: "选择要导入的文件"
        fileMode: QtDialogs.FileDialog.OpenFiles
        nameFilters: [
            "所有支持的文件 (*.mp4 *.mov *.avi *.mkv *.jpg *.jpeg *.png *.gif *.bmp *.mp3 *.wav *.aac *.flac)",
            "视频文件 (*.mp4 *.mov *.avi *.mkv)",
            "图片文件 (*.jpg *.jpeg *.png *.gif *.bmp)",
            "音频文件 (*.mp3 *.wav *.aac *.flac)",
            "所有文件 (*)"
        ]
        onAccepted: {
            var paths = []
            for (var i = 0; i < selectedFiles.length; i++) {
                var p = selectedFiles[i].toString()
                if (p.startsWith("file:///")) p = p.substring(8)
                paths.push(p)
            }
            if (paths.length > 0) {
                bridge.media.import_files(paths)
            }
        }
    }

    // ── 对话框 ──
    Dialogs.AlertDialog { id: alertDialog }
    Dialogs.ConfirmDialog { id: confirmDialog }

    // ── 内部函数 ──
    function _reloadFiles() {
        bridge.media.load_files_filtered(_filterType, _searchText, projectId)
    }

    // ── 素材卡片组件 ──
    component MediaCardDelegate: Pane {
        property string fileId: ""
        property string fileName: ""
        property string fileType: ""
        property string filePath: ""
        property string thumbnailPath: ""
        property int fileSize: 0
        property real duration: 0
        property int videoWidth: 0
        property int videoHeight: 0

        signal playRequested()
        signal deleteRequested()
        signal openFolderRequested()

        padding: 8
        height: 210


        ColumnLayout {
            anchors.fill: parent
            spacing: 6

            // 缩略图
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 120
                radius: Theme.radiusSmall; clip: true

                Image {
                    anchors.fill: parent
                    source: thumbnailPath ? "file:///" + thumbnailPath : ""
                    fillMode: Image.PreserveAspectCrop
                    visible: source !== ""
                }

                // 类型标签
                Rectangle {
                    anchors.top: parent.top; anchors.right: parent.right
                    width: typeLabel.implicitWidth + 8; height: 18; radius: Theme.radiusSmall
                    Label {
                        id: typeLabel; anchors.centerIn: parent
                        text: fileType === "video" ? "视频" : (fileType === "image" ? "图片" : "音频")
                    }
                }

                // 播放按钮（仅视频）
                Button {
                    anchors.centerIn: parent
                    text: "▶"
                    visible: fileType === "video"
                    onClicked: playRequested()
                }

                // 时长标签
                Rectangle {
                    anchors.bottom: parent.bottom; anchors.right: parent.right
                    width: durationLabel.implicitWidth + 8; height: 18; radius: Theme.radiusSmall
                    visible: duration > 0
                    Label {
                        id: durationLabel; anchors.centerIn: parent
                        text: _formatDuration(duration)
                    }
                }
            }

            // 文件名
            Label {
                text: fileName
                font.pixelSize: Theme.fontSizeSmall
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            // 元信息 + 操作
            RowLayout {
                Layout.fillWidth: true
                spacing: 4
                Label {
                    text: _formatSize(fileSize)
                    font.pixelSize: Theme.fontSizeTiny
                    Layout.fillWidth: true
                }
                Button {
                    text: "📂"; flat: true; implicitWidth: 28; implicitHeight: 24
                    ToolTip.text: "打开所在文件夹"
                    ToolTip.visible: hovered
                    onClicked: openFolderRequested()
                }
                Button {
                    text: "🗑"; flat: true; implicitWidth: 28; implicitHeight: 24
                    ToolTip.text: "删除"
                    ToolTip.visible: hovered
                    onClicked: deleteRequested()
                }
            }
        }

        HoverHandler { id: cardHover }
    }

    function _formatDuration(seconds) {
        if (seconds <= 0) return ""
        var m = Math.floor(seconds / 60)
        var s = Math.floor(seconds % 60)
        return m + ":" + (s < 10 ? "0" : "") + s
    }

    function _formatSize(bytes) {
        if (bytes <= 0) return ""
        if (bytes < 1024) return bytes + " B"
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB"
        if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + " MB"
        return (bytes / 1073741824).toFixed(2) + " GB"
    }
}
