import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs as QtDialogs
import "../components" as Comp
import "../dialogs" as Dialogs

Dialog {
    id: projectDialog
    modal: true
    width: 480
    anchors.centerIn: parent
    padding: 0

    property bool isEdit: false
    property int editProjectId: 0
    property string coverImagePath: ""
    property bool isGeneratingCover: false

    title: ""

    Connections {
        target: bridge.projects

        function onCover_generation_started() {
            isGeneratingCover = true
        }

        function onCover_generation_finished(relativePath) {
            isGeneratingCover = false
            coverImagePath = relativePath
        }

        function onCover_generation_failed(errorMsg) {
            isGeneratingCover = false
            console.error("封面生成失败:", errorMsg)
        }
    }

    background: Rectangle {
        color: Material.dialogColor
        radius: Theme.radiusMedium
    }

    header: Item {
        implicitHeight: 56

        Rectangle {
            anchors.fill: parent
            color: "transparent"

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
            }

            Label {
                anchors.left: parent.left
                anchors.leftMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                text: projectDialog.isEdit ? "编辑项目" : "新建项目"
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
            }
        }
    }

    footer: Item {
        implicitHeight: 64

        Rectangle {
            anchors.fill: parent
            color: "transparent"

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
            }

            RowLayout {
                anchors.right: parent.right
                anchors.rightMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                spacing: 12

                Button {
                    text: "取消"
                    flat: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 80
                    onClicked: projectDialog.reject()
                }

                Button {
                    text: projectDialog.isEdit ? "保存" : "创建"
                    highlighted: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 80
                    onClicked: {
                        if (isEdit) {
                            bridge.projects.update_project(editProjectId, nameField.text, resCombo.currentText, ratioCombo.currentText, coverImagePath)
                        } else {
                            bridge.projects.create_project(nameField.text, resCombo.currentText, ratioCombo.currentText, coverImagePath)
                        }
                        projectDialog.accept()
                    }
                }
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        anchors.leftMargin: 18
        anchors.rightMargin: 18
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        contentWidth: availableWidth
        clip: true

        ColumnLayout {
            width: parent.parent.width - 36
            spacing: 20

            ColumnLayout {
                spacing: 8
                Layout.fillWidth: true

                Label {
                    text: "项目名称"
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                }
                Comp.AppTextField {
                    id: nameField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    placeholderText: "输入项目名称"
                }
            }

            ColumnLayout {
                spacing: 8
                Layout.fillWidth: true

                Label {
                    text: "封面图"
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                }

                RowLayout {
                    spacing: 8
                    Layout.fillWidth: true

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 36
                        radius: Theme.radiusSmall
                        color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.05)
                        border.width: 1
                        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)

                        Label {
                            anchors.left: parent.left
                            anchors.leftMargin: 12
                            anchors.verticalCenter: parent.verticalCenter
                            text: coverImagePath ? coverImagePath.split("/").pop() : "未选择图片"
                            font.pixelSize: Theme.fontSizeSmall
                            opacity: coverImagePath ? 1.0 : 0.5
                            elide: Text.ElideMiddle
                            width: parent.width - 24
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
                        enabled: !isGeneratingCover
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
                            if (!editProjectId || editProjectId <= 0) {
                                alertDialog.error("错误", "请先保存项目后再生成封面图")
                                return
                            }

                            // 检查是否有大纲内容
                            var outlineContent = bridge.storyOutline.get_outline_content(editProjectId)
                            if (!outlineContent || outlineContent.trim() === "") {
                                alertDialog.error("错误", "请先编写项目大纲后再生成封面图")
                                return
                            }

                            characterSelectDialog.projectId = editProjectId
                            characterSelectDialog.outlineContent = outlineContent
                            characterSelectDialog.open()
                        }

                        BusyIndicator {
                            anchors.centerIn: parent
                            width: 24
                            height: 24
                            visible: isGeneratingCover
                            running: isGeneratingCover
                        }
                    }

                    Button {
                        text: "选择"
                        flat: true
                        Layout.preferredHeight: 36
                        Layout.preferredWidth: 64
                        onClicked: coverFileDialog.open()
                    }

                    Button {
                        text: "清除"
                        flat: true
                        Layout.preferredHeight: 36
                        Layout.preferredWidth: 64
                        visible: coverImagePath !== ""
                        onClicked: coverImagePath = ""
                    }
                }
            }

            ColumnLayout {
                spacing: 8
                Layout.fillWidth: true

                Label {
                    text: "画面比例"
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                }
                ComboBox {
                    id: ratioCombo
                    model: ["16:9", "9:16", "1:1", "4:3", "3:4"]
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                }
            }

            ColumnLayout {
                spacing: 8
                Layout.fillWidth: true

                Label {
                    text: "分辨率"
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                }
                ComboBox {
                    id: resCombo
                    model: ["480P", "720P", "1080P", "2K", "4K"]
                    currentIndex: 1
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                }
            }

            Item { Layout.preferredHeight: 1 }
        }
    }

    function openForCreate() {
        isEdit = false
        editProjectId = 0
        nameField.text = ""
        coverImagePath = ""
        resCombo.currentIndex = 1
        ratioCombo.currentIndex = 0
        open()
    }

    function openForEdit(projectId) {
        isEdit = true
        editProjectId = projectId
        var info = JSON.parse(bridge.projects.get_project_info(projectId))
        nameField.text = info.name || ""
        coverImagePath = info.coverImage || ""
        var ratioIdx = ratioCombo.model.indexOf(info.aspectRatio)
        if (ratioIdx >= 0) ratioCombo.currentIndex = ratioIdx
        var resIdx = resCombo.model.indexOf(info.resolution)
        if (resIdx >= 0) resCombo.currentIndex = resIdx
        open()
    }

    QtDialogs.FileDialog {
        id: coverFileDialog
        title: "选择封面图片"
        fileMode: QtDialogs.FileDialog.OpenFile
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.bmp *.svg)", "所有文件 (*)"]
        onAccepted: {
            var p = selectedFile.toString()
            if (p.startsWith("file:///")) p = p.substring(8)
            coverImagePath = p
        }
    }

    Dialogs.CharacterSelectDialog {
        id: characterSelectDialog
        projectId: projectDialog.editProjectId > 0 ? projectDialog.editProjectId : 0

        property string outlineContent: ""

        onCharactersSelected: function(characters) {
            if (!projectDialog.editProjectId || projectDialog.editProjectId <= 0) {
                alertDialog.error("错误", "无效的项目 ID")
                return
            }

            if (characters.length === 0) {
                alertDialog.error("错误", "请至少选择一个角色")
                return
            }

            var missingDesignImage = false
            var characterNames = []
            var characterDescriptions = []
            var designImageUrls = []

            for (var i = 0; i < characters.length; i++) {
                var char = characters[i]
                if (!char.designImagePath || char.designImagePath === "") {
                    missingDesignImage = true
                    break
                }
                characterNames.push(char.name)
                characterDescriptions.push(char.description)
                designImageUrls.push(char.designImagePath)
            }

            if (missingDesignImage) {
                alertDialog.error("错误", "所选角色中存在没有设计图的角色，请先生成角色设计图")
                return
            }

            bridge.projects.generate_cover_with_characters(
                projectDialog.editProjectId,
                characterNames.join(", "),
                characterDescriptions.join("\n\n"),
                ratioCombo.currentText,
                nameField.text,
                outlineContent,
                designImageUrls.join("|")
            )
        }
    }

    Dialogs.AlertDialog {
        id: alertDialog
    }
}
