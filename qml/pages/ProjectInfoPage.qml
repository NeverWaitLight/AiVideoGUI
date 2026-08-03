import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import QtQuick.Dialogs as QtDialogs
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: page

    property int projectId: -1
    property bool isCreate: false
    property string _coverRelativePath: ""
    property string _coverDisplayPath: ""
    property bool isGeneratingCover: false

    readonly property bool _isPortrait: _ratioText === "9:16" || _ratioText === "3:4"
    property string _ratioText: "16:9"
    property string _resText: "720P"
    property string _nameText: ""

    signal backClicked()
    signal projectSaved(int projectId)

    onProjectIdChanged: {
        if (projectId > 0) {
            _loadProjectData()
        }
    }

    Connections {
        target: bridge.projects

        function onCover_generation_started() {
            isGeneratingCover = true
        }

        function onCover_generation_finished(relativePath) {
            isGeneratingCover = false
            _coverRelativePath = relativePath
            if (projectId > 0) {
                var info = JSON.parse(bridge.projects.get_project_info(projectId))
                _coverDisplayPath = info.coverImagePath || ""
            }
        }

        function onCover_generation_failed(errorMsg) {
            isGeneratingCover = false
            alertDialog.error("错误", "封面生成失败: " + errorMsg)
        }
    }

    function _loadProjectData() {
        var info = JSON.parse(bridge.projects.get_project_info(projectId))
        _nameText = info.name || ""
        _coverRelativePath = info.coverImage || ""
        _coverDisplayPath = info.coverImagePath || ""
        if (info.aspectRatio) _ratioText = info.aspectRatio
        if (info.resolution) _resText = info.resolution
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Comp.PageHeader {
            title: page.isCreate ? "新建项目" : "项目详情"
            Layout.fillWidth: true
            onBackClicked: page.backClicked()

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
                ToolTip.text: isGeneratingCover ? "生成中..." : "AI 生成封面图"

                background: Rectangle {
                    anchors.fill: parent
                    radius: parent.width / 2
                    color: parent.enabled ? (parent.pressed ? "#E65100" : (parent.hovered ? "#FB8C00" : "#FF9800")) : "#BDBDBD"
                }

                onClicked: {
                    if (!projectId || projectId <= 0) {
                        alertDialog.error("错误", "请先保存项目后再生成封面图")
                        return
                    }

                    var outlineContent = bridge.storyOutline.get_outline_content(projectId)
                    if (!outlineContent || outlineContent.trim() === "") {
                        alertDialog.error("错误", "请先编写项目大纲后再生成封面图")
                        return
                    }

                    characterSelectDialog.projectId = projectId
                    characterSelectDialog.outlineContent = outlineContent
                    characterSelectDialog.open()
                }
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
                enabled: _nameText.trim() !== ""
                ToolTip.visible: hovered
                ToolTip.text: "保存"

                background: Rectangle {
                    anchors.fill: parent
                    radius: Theme.radiusSmall
                    color: parent.hovered
                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                        : "transparent"
                }

                onClicked: _saveProject()
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: availableWidth
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: 0

                Item { Layout.preferredHeight: 8 }

                Loader {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 720
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredHeight: item ? item.implicitHeight : 0

                    sourceComponent: _isPortrait ? portraitLayout : landscapeLayout
                }

                Item { Layout.preferredHeight: 20 }
            }
        }
    }

    // --- Layouts ---

    Component {
        id: landscapeLayout

        ColumnLayout {
            spacing: 16

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 260
                Layout.leftMargin: 16
                Layout.rightMargin: 16

                Comp.ImageUploadPanel {
                    anchors.fill: parent
                    imageSource: _coverDisplayPath
                    placeholderText: "暂无封面图"
                    busy: isGeneratingCover
                    onUploadClicked: coverFileDialog.open()
                    onClearClicked: {
                        _coverRelativePath = ""
                        _coverDisplayPath = ""
                    }
                }
            }

            FormFields {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
            }
        }
    }

    Component {
        id: portraitLayout

        RowLayout {
            spacing: 16

            ColumnLayout {
                Layout.preferredWidth: 240
                Layout.fillHeight: true
                Layout.leftMargin: 16
                spacing: 8

                Item {
                    Layout.preferredWidth: 240
                    Layout.fillHeight: true

                    Comp.ImageUploadPanel {
                        anchors.fill: parent
                        imageSource: _coverDisplayPath
                        placeholderText: "暂无封面图"
                        busy: isGeneratingCover
                        onUploadClicked: coverFileDialog.open()
                        onClearClicked: {
                            _coverRelativePath = ""
                            _coverDisplayPath = ""
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.rightMargin: 16
                spacing: 16

                FormFields {
                    Layout.fillWidth: true
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    // --- Sub-components ---

    component FormFields: ColumnLayout {
        spacing: 16

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: "项目名称"
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.7
            }
            Comp.AppTextField {
                Layout.fillWidth: true
                Layout.preferredHeight: 36
                placeholderText: "输入项目名称"
                text: _nameText
                onTextChanged: _nameText = text
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    text: "画面比例"
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                }
                ComboBox {
                    model: ["16:9", "9:16", "1:1", "4:3", "3:4"]
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    currentIndex: model.indexOf(_ratioText)
                    onActivated: _ratioText = currentText
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    text: "分辨率"
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                }
                ComboBox {
                    model: ["480P", "720P", "1080P", "2K", "4K"]
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    currentIndex: model.indexOf(_resText)
                    onActivated: _resText = currentText
                }
            }
        }
    }

    // --- Logic ---

    function _saveProject() {
        var coverToSave = _coverRelativePath
        if (_coverDisplayPath && !_coverRelativePath) {
            coverToSave = bridge.projects.resolve_cover_path(_coverDisplayPath)
        }

        bridge.projects.update_project(projectId, _nameText.trim(), _resText, _ratioText, coverToSave)
        page.isCreate = false
        page.projectSaved(projectId)
    }

    // --- Dialogs ---

    QtDialogs.FileDialog {
        id: coverFileDialog
        title: "选择封面图片"
        fileMode: QtDialogs.FileDialog.OpenFile
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.bmp *.svg)", "所有文件 (*)"]
        onAccepted: {
            var p = selectedFile.toString()
            if (p.startsWith("file:///")) p = p.substring(8)
            _coverDisplayPath = p.replace(/\\/g, "/")
            _coverRelativePath = ""
        }
    }

    Dialogs.CharacterSelectDialog {
        id: characterSelectDialog
        projectId: page.projectId > 0 ? page.projectId : 0

        property string outlineContent: ""

        onCharacterSelected: function(characterId, characterName, appearance, designImageUrl) {
            if (!page.projectId || page.projectId <= 0) {
                alertDialog.error("错误", "无效的项目 ID")
                return
            }

            if (!designImageUrl || designImageUrl === "") {
                alertDialog.error("错误", "所选角色没有设计图，请先生成角色设计图")
                return
            }

            bridge.projects.generate_cover_with_character(
                page.projectId,
                characterName,
                appearance,
                _ratioText,
                _nameText,
                outlineContent,
                designImageUrl
            )
        }
    }

    Dialogs.AlertDialog {
        id: alertDialog
    }
}
