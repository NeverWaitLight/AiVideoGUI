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
    property string _projectName: ""

    readonly property bool _isPortrait: _ratioText === "9:16" || _ratioText === "3:4"
    property string _ratioText: "16:9"
    property string _resText: "720P"
    property string _nameText: ""
    property int _visualStyleId: -1  // -1 表示默认（数据库 null），0+ 表示具体风格

    signal backClicked()
    signal projectSaved(int projectId)
    signal nextStepClicked()

    onProjectIdChanged: {
        if (projectId > 0) {
            _loadProjectData()
        }
    }

    Component.onCompleted: {
        bridge.visualStyles.load_styles()
    }

    Connections {
        target: bridge.projects

        function onCover_generation_started(projectId) {
            isGeneratingCover = true
        }

        function onCover_generation_finished(projectId, relativePath) {
            isGeneratingCover = false
            _coverRelativePath = relativePath
            if (page.projectId > 0) {
                var info = JSON.parse(bridge.projects.get_project_info(page.projectId))
                _coverDisplayPath = info.coverImagePath || ""
            }
        }

        function onCover_generation_failed(projectId, errorMsg) {
            isGeneratingCover = false
            alertDialog.error("错误", "封面生成失败: " + errorMsg)
        }
    }

    function _loadProjectData() {
        var info = JSON.parse(bridge.projects.get_project_info(projectId))
        _projectName = info.name || ""
        _nameText = info.name || ""
        _coverRelativePath = info.coverImage || ""
        _coverDisplayPath = info.coverImagePath || ""
        if (info.aspectRatio) _ratioText = info.aspectRatio
        if (info.resolution) _resText = info.resolution
        _visualStyleId = info.visualStyleId !== undefined && info.visualStyleId !== null ? info.visualStyleId : -1
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Comp.PageHeader {
            projectName: page.isCreate ? "" : _projectName
            title: page.isCreate ? "新建项目" : "编辑"
            Layout.fillWidth: true
            onBackClicked: page.backClicked()

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
                enabled: _nameText.trim() !== ""
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
                    if (projectId <= 0) {
                        alertDialog.error("错误", "请先保存项目")
                        return
                    }
                    page.nextStepClicked()
                }
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

                Comp.ImagePicker {
                    anchors.fill: parent
                    imageSource: _coverDisplayPath
                    busy: isGeneratingCover
                    onAiGenerateClicked: {
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
                    onUploadClicked: coverFileDialog.open()
                    onDeleteClicked: {
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

                    Comp.ImagePicker {
                        anchors.fill: parent
                        imageSource: _coverDisplayPath
                        busy: isGeneratingCover
                        onAiGenerateClicked: {
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
                        onUploadClicked: coverFileDialog.open()
                        onDeleteClicked: {
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

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: "视觉风格"
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.7
            }

            ComboBox {
                id: styleComboBox
                Layout.fillWidth: true
                Layout.preferredHeight: 36
                model: bridge.visualStyles.listModel
                textRole: "name"
                valueRole: "styleId"

                Component.onCompleted: {
                    updateIndex()
                }

                onModelChanged: {
                    updateIndex()
                }

                onActivated: function(index) {
                    if (index === 0) {
                        _visualStyleId = -1  // 默认选项
                    } else {
                        _visualStyleId = currentValue !== undefined ? currentValue : -1
                    }
                }

                Connections {
                    target: page
                    function onProjectIdChanged() {
                        if (projectId > 0) {
                            Qt.callLater(styleComboBox.updateIndex)
                        }
                    }
                }

                Connections {
                    target: page
                    function on_VisualStyleIdChanged() {
                        styleComboBox.updateIndex()
                    }
                }

                function updateIndex() {
                    if (_visualStyleId === -1) {
                        currentIndex = 0  // 默认选项
                        return
                    }
                    if (model && model.rowCount && model.rowCount() > 0) {
                        var idx = indexOfValue(_visualStyleId)
                        currentIndex = idx >= 0 ? idx + 1 : 0  // +1 因为有默认选项
                    }
                }

                delegate: ItemDelegate {
                    required property int index
                    required property var model

                    width: styleComboBox.width
                    height: index === 0 ? 36 : 48

                    contentItem: RowLayout {
                        spacing: 12

                        Image {
                            Layout.preferredWidth: 32
                            Layout.preferredHeight: 32
                            source: parent.parent.index === 0 ? "" : (parent.parent.model.sampleImagePath ? "file:///" + parent.parent.model.sampleImagePath : "")
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                            cache: true
                            smooth: false
                            mipmap: false
                            visible: parent.parent.index !== 0

                            Rectangle {
                                anchors.fill: parent
                                color: "transparent"
                                border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                                border.width: 1
                                radius: 4
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            text: parent.parent.index === 0 ? "默认" : parent.parent.model.name
                            elide: Text.ElideRight
                        }
                    }
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

        bridge.projects.update_project(projectId, _nameText.trim(), _resText, _ratioText, coverToSave, _visualStyleId)
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

        onCharactersSelected: function(characters) {
            if (!page.projectId || page.projectId <= 0) {
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
                page.projectId,
                characterNames.join(", "),
                characterDescriptions.join("\n\n"),
                _ratioText,
                _nameText,
                outlineContent,
                designImageUrls.join("|")
            )
        }
    }

    Dialogs.AlertDialog {
        id: alertDialog
    }
}
