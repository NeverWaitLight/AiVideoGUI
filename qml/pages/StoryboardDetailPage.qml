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
    property bool contentFullscreen: false
    property var takesList: []
    property var generatingDesignShotIds: []

    ListModel {
        id: takesListModel
    }

    signal backClicked()

    property color borderColor: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.15)

    onContentFullscreenChanged: {
        if (contentFullscreen) {
            fullscreenContentEdit.text = contentEdit.text
            detailPage.forceActiveFocus()
        }
    }

    focus: true

    Keys.onEscapePressed: {
        if (contentFullscreen) {
            contentEdit.text = fullscreenContentEdit.text
            contentFullscreen = false
        }
    }

    onShotIdChanged: {
        if (shotId > 0) {
            bridge.storyboard.load_shot(shotId)
            _loadTakes()
        }
    }

    Connections {
        target: bridge.storyboard
        function onTakes_changed() {
            _loadTakes()
        }
    }

    Connections {
        target: bridge
        function onTask_failed(providerTaskId, error) {
            _loadTakes()
        }
        function onTask_finished(providerTaskId, savePath, storyboardId) {
            if (storyboardId === detailPage.shotId) {
                _loadTakes()
            }
        }
    }

    Component.onCompleted: {
        if (detailPage.shotId > 0) {
            _loadTakes()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Comp.PageHeader {
            projectName: detailPage.projectName
            title: bridge.storyboard.curSceneNumber + "场" + bridge.storyboard.curShotNumber + "镜"
            titleSuffix: detailPage.contentFullscreen ? "- 画面内容" : ""
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

                onClicked: videoGenerateDialog.show(detailPage.projectId, [bridge.storyboard.curShotId], function(promptExtendEnabled, useStoryboardDesign, useCharacterDesign) {
                    bridge.storyboard.batch_generate_videos(
                        detailPage.projectId,
                        JSON.stringify([bridge.storyboard.curShotId]),
                        promptExtendEnabled,
                        useStoryboardDesign,
                        useCharacterDesign
                    )
                })
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

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !detailPage.contentFullscreen
            enabled: !detailPage.contentFullscreen

        Flickable {
            width: parent.width * 2 / 3
            height: parent.height
            contentHeight: contentColumn.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            ColumnLayout {
                id: contentColumn
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: 0

                // Top section: form + image side by side
                Item {
                    Layout.fillWidth: true
                    implicitHeight: Math.max(formGrid.implicitHeight + 24, imagePicker.height + 24)

                    GridLayout {
                        id: formGrid
                        anchors.left: parent.left
                        anchors.top: parent.top
                        width: parent.width / 2 - 20
                        anchors.leftMargin: 20
                        anchors.topMargin: 12
                        columns: 2
                        columnSpacing: 10
                        rowSpacing: 6

                        Label { text: "景别："; font.pixelSize: Theme.fontSizeSmall; Layout.preferredWidth: 80; horizontalAlignment: Text.AlignRight }
                        ComboBox {
                            id: shotSizeCombo
                            model: ["特写", "近景", "中景", "全景", "远景", "大远景"]
                            currentIndex: bridge.storyboard.curShotSizeIndex
                            Layout.fillWidth: true
                            Layout.preferredHeight: 32
                            font.pixelSize: Theme.fontSizeSmall
                            background: Rectangle {
                                radius: Theme.radiusSmall
                                color: "transparent"
                                border.width: 1
                                border.color: detailPage.borderColor
                            }
                        }

                        Label { text: "运镜："; font.pixelSize: Theme.fontSizeSmall; Layout.preferredWidth: 80; horizontalAlignment: Text.AlignRight }
                        Comp.AppTextField {
                            id: cameraInput
                            text: bridge.storyboard.curCameraMovement
                            placeholderText: "固定、慢推、跟拍"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 32
                            background: Rectangle {
                                radius: Theme.radiusSmall
                                color: "transparent"
                                border.width: 1
                                border.color: detailPage.borderColor
                            }
                        }

                        Label { text: "时长："; font.pixelSize: Theme.fontSizeSmall; Layout.preferredWidth: 80; horizontalAlignment: Text.AlignRight }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            SpinBox {
                                id: durationSpin
                                from: 0; to: 600; stepSize: 1
                                value: bridge.storyboard.curDuration
                                Layout.fillWidth: true
                                Layout.preferredHeight: 32
                                background: Rectangle {
                                    radius: Theme.radiusSmall
                                    color: "transparent"
                                    border.width: 1
                                    border.color: detailPage.borderColor
                                }
                            }

                            Label { text: "秒"; font.pixelSize: Theme.fontSizeSmall }
                        }

                        Label { text: "种子："; font.pixelSize: Theme.fontSizeSmall; Layout.preferredWidth: 80; horizontalAlignment: Text.AlignRight }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6

                            Comp.AppTextField {
                                id: seedInput
                                text: bridge.storyboard.curSeed
                                placeholderText: "留空则随机"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 32
                                validator: IntValidator { bottom: 0; top: 2147483647 }
                                background: Rectangle {
                                    radius: Theme.radiusSmall
                                    color: "transparent"
                                    border.width: 1
                                    border.color: detailPage.borderColor
                                }
                            }

                            Button {
                                Layout.preferredWidth: 32
                                Layout.preferredHeight: 32
                                display: AbstractButton.IconOnly
                                icon.source: "qrc:/resources/icons/autorenew.svg"
                                icon.width: 18
                                icon.height: 18
                                topPadding: 7
                                bottomPadding: 7
                                leftPadding: 7
                                rightPadding: 7
                                ToolTip.visible: hovered
                                ToolTip.text: "随机种子"

                                background: Rectangle {
                                    anchors.fill: parent
                                    radius: Theme.radiusSmall
                                    color: parent.hovered
                                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                                        : "transparent"
                                }

                                onClicked: seedInput.text = Math.floor(Math.random() * 2147483647).toString()
                            }
                        }
                    }

                    Comp.ImagePicker {
                        id: imagePicker
                        x: parent.width / 2 + 10
                        y: 12
                        width: parent.width / 2 - 30
                        height: formGrid.implicitHeight
                        imageSource: bridge.storyboard.curDesignImage
                        busy: generatingDesignShotIds.indexOf(String(bridge.storyboard.curShotId)) !== -1

                        onAiGenerateClicked: bridge.storyboard.generate_design_image(
                            bridge.storyboard.curShotId, detailPage.projectId)
                        onUploadClicked: uploadImageDialog.open()
                        onDeleteClicked: bridge.storyboard.delete_design_image(
                            bridge.storyboard.curShotId)
                    }
                }

                // Bottom section: remaining fields
                GridLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 20
                    Layout.rightMargin: 20
                    Layout.topMargin: 12
                    Layout.bottomMargin: 20
                    columns: 2
                    columnSpacing: 10
                    rowSpacing: 6

                    Label { text: "画面内容："; font.pixelSize: Theme.fontSizeSmall; Layout.preferredWidth: 80; horizontalAlignment: Text.AlignRight; Layout.alignment: Qt.AlignTop }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: width / 4
                        radius: Theme.radiusSmall
                        color: "transparent"
                        border.width: 1
                        border.color: detailPage.borderColor
                        clip: true

                        Flickable {
                            id: contentFlick
                            anchors.fill: parent
                            anchors.margins: 8
                            anchors.rightMargin: 36
                            contentHeight: contentEdit.contentHeight
                            boundsBehavior: Flickable.StopAtBounds
                            clip: true

                            TextArea.flickable: TextArea {
                                id: contentEdit
                                text: bridge.storyboard.curVisualContent
                                placeholderText: "画面描述"
                                wrapMode: TextArea.Wrap
                                font.pixelSize: Theme.fontSizeMedium
                                padding: 0
                                background: null
                                selectByMouse: true
                            }

                            ScrollBar.vertical: ScrollBar {
                                policy: ScrollBar.AsNeeded
                            }
                        }

                        Button {
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 4
                            width: 28
                            height: 28
                            display: AbstractButton.IconOnly
                            icon.source: "qrc:/resources/icons/fullscreen.svg"
                            icon.width: 18
                            icon.height: 18
                            topPadding: 5
                            bottomPadding: 5
                            leftPadding: 5
                            rightPadding: 5
                            ToolTip.visible: hovered
                            ToolTip.text: "全屏查看"
                            onClicked: detailPage.contentFullscreen = true

                            background: Rectangle {
                                anchors.fill: parent
                                radius: Theme.radiusSmall
                                color: parent.hovered
                                    ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                                    : "transparent"
                            }
                        }
                    }

                    Label { text: "音效："; font.pixelSize: Theme.fontSizeSmall; Layout.preferredWidth: 80; horizontalAlignment: Text.AlignRight; Layout.alignment: Qt.AlignTop }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 56
                        radius: Theme.radiusSmall
                        color: "transparent"
                        border.width: 1
                        border.color: detailPage.borderColor
                        clip: true

                        Flickable {
                            anchors.fill: parent
                            anchors.margins: 8
                            contentHeight: soundEffectInput.contentHeight
                            boundsBehavior: Flickable.StopAtBounds
                            clip: true

                            TextArea.flickable: TextArea {
                                id: soundEffectInput
                                text: bridge.storyboard.curSoundEffect
                                placeholderText: "音效描述"
                                wrapMode: TextArea.Wrap
                                font.pixelSize: Theme.fontSizeMedium
                                padding: 0
                                background: null
                                selectByMouse: true
                            }

                            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                        }
                    }

                    Label { text: "环境音："; font.pixelSize: Theme.fontSizeSmall; Layout.preferredWidth: 80; horizontalAlignment: Text.AlignRight; Layout.alignment: Qt.AlignTop }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 56
                        radius: Theme.radiusSmall
                        color: "transparent"
                        border.width: 1
                        border.color: detailPage.borderColor
                        clip: true

                        Flickable {
                            anchors.fill: parent
                            anchors.margins: 8
                            contentHeight: ambientSoundInput.contentHeight
                            boundsBehavior: Flickable.StopAtBounds
                            clip: true

                            TextArea.flickable: TextArea {
                                id: ambientSoundInput
                                text: bridge.storyboard.curAmbientSound
                                placeholderText: "环境音描述"
                                wrapMode: TextArea.Wrap
                                font.pixelSize: Theme.fontSizeMedium
                                padding: 0
                                background: null
                                selectByMouse: true
                            }

                            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                        }
                    }

                    Label { text: "背景音乐："; font.pixelSize: Theme.fontSizeSmall; Layout.preferredWidth: 80; horizontalAlignment: Text.AlignRight; Layout.alignment: Qt.AlignTop }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 56
                        radius: Theme.radiusSmall
                        color: "transparent"
                        border.width: 1
                        border.color: detailPage.borderColor
                        clip: true

                        Flickable {
                            anchors.fill: parent
                            anchors.margins: 8
                            contentHeight: bgMusicInput.contentHeight
                            boundsBehavior: Flickable.StopAtBounds
                            clip: true

                            TextArea.flickable: TextArea {
                                id: bgMusicInput
                                text: bridge.storyboard.curBackgroundMusic
                                placeholderText: "背景音乐描述"
                                wrapMode: TextArea.Wrap
                                font.pixelSize: Theme.fontSizeMedium
                                padding: 0
                                background: null
                                selectByMouse: true
                            }

                            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                        }
                    }

                    Label { text: "备注："; font.pixelSize: Theme.fontSizeSmall; Layout.preferredWidth: 80; horizontalAlignment: Text.AlignRight; Layout.alignment: Qt.AlignTop }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 56
                        radius: Theme.radiusSmall
                        color: "transparent"
                        border.width: 1
                        border.color: detailPage.borderColor
                        clip: true

                        Flickable {
                            anchors.fill: parent
                            anchors.margins: 8
                            contentHeight: notesInput.contentHeight
                            boundsBehavior: Flickable.StopAtBounds
                            clip: true

                            TextArea.flickable: TextArea {
                                id: notesInput
                                text: bridge.storyboard.curNotes
                                placeholderText: "备注信息"
                                wrapMode: TextArea.Wrap
                                font.pixelSize: Theme.fontSizeMedium
                                padding: 0
                                background: null
                                selectByMouse: true
                            }

                            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                        }
                    }
                }
            }
        }

        // Right panel: takes list
        Rectangle {
            x: parent.width * 2 / 3
            width: parent.width / 3
            height: parent.height
            color: "transparent"
            border.width: 1
            border.color: detailPage.borderColor

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                Label {
                    text: "拍摄记录"
                    font.pixelSize: Theme.fontSizeMedium
                    font.bold: true
                    Layout.fillWidth: true
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: takesListModel
                    spacing: 8
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    delegate: Rectangle {
                        id: takeCard
                        width: ListView.view.width
                        height: 80
                        radius: Theme.radiusSmall
                        color: takeCard.hasMedia
                            ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.04)
                            : Qt.rgba(Material.accent.r, Material.accent.g, Material.accent.b, takeCard.isFailed ? 0.08 : 0.05)
                        border.width: takeCard.hasMedia ? 1 : 2
                        border.color: takeCard.isGenerating
                            ? Material.accent
                            : (takeCard.isFailed ? "#F44336" : (takeCard.hasMedia ? detailPage.borderColor : "#FF9800"))

                        readonly property bool hasMedia: model.hasMedia === 1 || model.hasMedia === true
                        readonly property bool isGenerating: model.generating === 1 || model.generating === true
                        readonly property bool isFailed: model.failed === 1 || model.failed === true
                        readonly property int takeId: model.id
                        readonly property int takeNumber: model.number
                        readonly property string takeStatus: model.status
                        readonly property string stateLabel: {
                            if (takeCard.hasMedia)
                                return ""
                            if (takeCard.isGenerating)
                                return "生成中"
                            if (takeCard.isFailed)
                                return "生成失败"
                            return "无视频"
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 8

                            // Thumbnail
                            Rectangle {
                                Layout.preferredWidth: 112
                                Layout.fillHeight: true
                                radius: Theme.radiusSmall
                                color: takeCard.hasMedia ? "#222" : "#2a2a2a"
                                clip: true
                                border.width: takeCard.hasMedia ? 0 : 1
                                border.color: takeCard.isGenerating
                                    ? Material.accent
                                    : (takeCard.isFailed ? "#F44336" : "#FF9800")

                                Image {
                                    anchors.fill: parent
                                    source: takeCard.hasMedia
                                            && model.thumbnailPath && model.thumbnailPath !== ""
                                            ? ("file:///" + model.thumbnailPath) : ""
                                    fillMode: Image.PreserveAspectCrop
                                    visible: source !== ""
                                }

                                Column {
                                    anchors.centerIn: parent
                                    spacing: 4
                                    visible: takeCard.isGenerating

                                    BusyIndicator {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        width: 28
                                        height: 28
                                        running: parent.visible
                                    }

                                    Label {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: "生成中"
                                        font.pixelSize: Theme.fontSizeSmall
                                        color: "#ccc"
                                    }
                                }

                                Label {
                                    anchors.centerIn: parent
                                    text: takeCard.isFailed ? "生成失败" : "无视频"
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: takeCard.isFailed ? "#F44336" : "#888"
                                    visible: !takeCard.hasMedia && !takeCard.isGenerating
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    visible: takeCard.hasMedia
                                             && model.filePath
                                             && model.filePath !== ""
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: bridge.play_video(model.filePath)
                                }
                            }

                            // Take number
                            ColumnLayout {
                                Layout.preferredWidth: 56
                                spacing: 2

                                Label {
                                    text: "第" + takeCard.takeNumber + "次"
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold: true
                                }

                                Label {
                                    text: takeCard.stateLabel
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: takeCard.isFailed
                                        ? "#F44336"
                                        : (takeCard.isGenerating ? Material.accent : "#888")
                                    visible: takeCard.stateLabel !== ""
                                }
                            }

                            // Status dropdown
                            ComboBox {
                                id: statusCombo
                                Layout.fillWidth: true
                                Layout.preferredHeight: 32
                                model: ["备选", "选用", "放弃"]
                                currentIndex: takeCard.takeStatus === "candidate" ? 0 : (takeCard.takeStatus === "selected" ? 1 : 2)
                                font.pixelSize: Theme.fontSizeSmall

                                background: Rectangle {
                                    radius: Theme.radiusSmall
                                    color: statusCombo.currentIndex === 1 ? "#4CAF50" : (statusCombo.currentIndex === 2 ? "#9E9E9E" : "#FF9800")
                                }

                                contentItem: Text {
                                    text: statusCombo.displayText
                                    font: statusCombo.font
                                    color: "white"
                                    verticalAlignment: Text.AlignVCenter
                                    leftPadding: 8
                                }

                                onActivated: {
                                    var statusMap = ["candidate", "selected", "abandoned"]
                                    bridge.storyboard.update_take_status(takeCard.takeId, statusMap[currentIndex])
                                }
                            }

                            // Delete button
                            Button {
                                Layout.preferredWidth: 32
                                Layout.preferredHeight: 32
                                display: AbstractButton.IconOnly
                                icon.source: "qrc:/resources/icons/delete.svg"
                                icon.width: 18
                                icon.height: 18
                                topPadding: 7
                                bottomPadding: 7
                                leftPadding: 7
                                rightPadding: 7
                                ToolTip.visible: hovered
                                ToolTip.text: "删除"

                                background: Rectangle {
                                    anchors.fill: parent
                                    radius: Theme.radiusSmall
                                    color: parent.hovered
                                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                                        : "transparent"
                                }

                                onClicked: confirmDialog.confirm(
                                    "确定要删除第" + takeCard.takeNumber + "次拍摄记录吗？",
                                    function() { bridge.storyboard.delete_take(takeCard.takeId) }
                                )
                            }
                        }
                    }

                    Comp.EmptyState {
                        visible: takesListModel.count === 0
                        anchors.centerIn: parent
                        text: "暂无拍摄记录"
                    }
                }
            }
        }

        } // content area (Item)

        // Fullscreen content overlay
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: detailPage.contentFullscreen
            enabled: detailPage.contentFullscreen

            Rectangle {
                anchors.fill: parent
                anchors.margins: 20
                radius: Theme.radiusSmall
                color: "transparent"
                border.width: 1
                border.color: detailPage.borderColor
                clip: true

                Flickable {
                    id: fullscreenContentFlick
                    anchors.fill: parent
                    anchors.margins: 12
                    anchors.rightMargin: 44
                    contentHeight: fullscreenContentEdit.contentHeight
                    boundsBehavior: Flickable.StopAtBounds
                    clip: true

                    TextArea.flickable: TextArea {
                        id: fullscreenContentEdit
                        text: bridge.storyboard.curVisualContent
                        placeholderText: "画面描述"
                        wrapMode: TextArea.Wrap
                        font.pixelSize: Theme.fontSizeMedium
                        padding: 0
                        background: null
                        selectByMouse: true

                        onTextChanged: {
                            if (detailPage.contentFullscreen) {
                                contentEdit.text = text
                            }
                        }
                    }

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }
                }

                Button {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 8
                    width: 28
                    height: 28
                    display: AbstractButton.IconOnly
                    icon.source: "qrc:/resources/icons/fullscreen_exit.svg"
                    icon.width: 18
                    icon.height: 18
                    topPadding: 5
                    bottomPadding: 5
                    leftPadding: 5
                    rightPadding: 5
                    ToolTip.visible: hovered
                    ToolTip.text: "退出全屏"
                    onClicked: {
                        contentEdit.text = fullscreenContentEdit.text
                        detailPage.contentFullscreen = false
                    }

                    background: Rectangle {
                        anchors.fill: parent
                        radius: Theme.radiusSmall
                        color: parent.hovered
                            ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                            : "transparent"
                    }
                }
            }
        }
    }

    Dialogs.ConfirmDialog { id: confirmDialog }
    Dialogs.VideoGenerateDialog { id: videoGenerateDialog }

    QtDialogs.FileDialog {
        id: uploadImageDialog
        title: "选择图片"
        fileMode: QtDialogs.FileDialog.OpenFile
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)"]
        onAccepted: {
            var path = selectedFile.toString()
            if (path.startsWith("file:///")) path = path.substring(8)
            bridge.storyboard.upload_design_image(bridge.storyboard.curShotId, path)
        }
    }

    function _saveCurrentShot() {
        bridge.storyboard.save_shot(
            detailPage.shotId,
            shotSizeCombo.currentIndex,
            cameraInput.text,
            contentEdit.text,
            durationSpin.value,
            soundEffectInput.text,
            ambientSoundInput.text,
            bgMusicInput.text,
            notesInput.text,
            bridge.storyboard.curDesignImage,
            seedInput.text
        )
    }

    function _loadTakes() {
        takesListModel.clear()
        if (detailPage.shotId <= 0) {
            detailPage.takesList = []
            return
        }

        var json = bridge.storyboard.get_takes_for_shot(detailPage.shotId)
        try {
            var arr = JSON.parse(json)
            detailPage.takesList = arr
            for (var i = 0; i < arr.length; i++) {
                takesListModel.append(arr[i])
            }
        } catch (e) {
            detailPage.takesList = []
        }
    }

}
