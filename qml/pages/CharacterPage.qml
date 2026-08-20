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
    property string _editingCharUuid: ""
    property bool _isNewCharacter: false
    property var _selectedIds: []
    property bool _multiSelect: false
    property bool _showDetail: false
    property string _editingDesignImage: ""
    property int designImageCacheKey: 0
    property string _projectName: ""
    property var generatingDesignCharUuids: []

    signal backClicked()
    signal navigateToStoryboard(int projectId)

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
            bridge.characters.load_for_project(projectId)
            _selectedIds = []
            _showDetail = false
        }
    }

    function openCharacterDetail(uuid) {
        if (!uuid) {
            return
        }
        var info = bridge.characters.get_character_info(uuid)
        if (!info || !info.characterUuid) {
            _showDetail = false
            return
        }
        _isNewCharacter = false
        _editingCharUuid = info.characterUuid || ""
        _editingDesignImage = info.designImagePath || ""
        nameInput.text = info.name || ""
        refCodeInput.text = info.refCode || ""
        descInput.text = info.description || ""
        voiceToneInput.text = info.voiceTone || ""
        voiceRefFileInput.text = info.voiceReferenceFile || ""
        _showDetail = true
    }

    Connections {
        target: bridge.characters
        function onData_changed() {
            bridge.characters.load_for_project(projectId)
        }
        function onCharacter_saved() {
        }
        function onDesign_image_ready(uuid, path) {
            if (uuid === _editingCharUuid) {
                _editingDesignImage = path
                designImageCacheKey++
            }
            characterAIDialog.finishWork()
        }
        function onDesign_image_started(uuid) {
            var ids = page.generatingDesignCharUuids.slice()
            if (ids.indexOf(uuid) === -1) {
                ids.push(uuid)
                page.generatingDesignCharUuids = ids
            }
        }
        function onDesign_image_finished(uuid) {
            var ids = page.generatingDesignCharUuids.slice()
            var index = ids.indexOf(uuid)
            if (index !== -1) {
                ids.splice(index, 1)
                page.generatingDesignCharUuids = ids
            }
        }
        function onDesign_image_failed(error) {
            characterAIDialog.finishWork()
            alertDialog.error("错误", "设计图生成失败：" + error)
        }
        function onDescription_refined(uuid, desc) {
            if (uuid === _editingCharUuid) {
                descInput.text = desc
            }
            characterAIDialog.finishWork()
        }
        function onDescription_refine_failed(error) {
            characterAIDialog.finishWork()
            alertDialog.error("错误", "描述修改失败：" + error)
        }
        function onCharacters_generated(count) {
            aiOptimizeDialog.finishOptimizing()
        }
        function onCharacters_optimized(count) {
            aiOptimizeDialog.finishOptimizing()
        }
        function onBridge_error(msg) {
            aiOptimizeDialog.finishOptimizing()
            alertDialog.error("错误", msg)
        }
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: _showDetail ? 1 : 0

        // ── 列表页 ──
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Comp.PageHeader {
                    projectName: _projectName
                    title: "角色"
                    titleSuffix: "共" + bridge.characters.model.count + "个角色"
                    Layout.fillWidth: true
                    onBackClicked: page.backClicked()

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
                            "确定要删除选中的 " + _selectedIds.length + " 个角色吗？",
                            function() {
                                bridge.characters.batch_delete(_selectedIds)
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
                            var allIds = JSON.parse(bridge.characters.get_all_ids())
                            _selectedIds = _selectedIds.length === allIds.length ? [] : allIds
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
                        enabled: !bridge.characters.isOptimizing
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
                            aiOptimizeDialog.show("AI 优化角色", "请输入优化要求（如添加/删除角色、调整形象描述等）...", "开始优化")
                        }
                    }

                    Button {
                        visible: !_multiSelect
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 34
                        display: AbstractButton.IconOnly
                        icon.source: "qrc:/resources/icons/add.svg"
                        icon.width: 20
                        icon.height: 20
                        topPadding: 7
                        bottomPadding: 7
                        leftPadding: 7
                        rightPadding: 7
                        ToolTip.visible: hovered
                        ToolTip.text: "新增角色"

                        background: Rectangle {
                            anchors.fill: parent
                            radius: Theme.radiusSmall
                            color: parent.hovered
                                ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                                : "transparent"
                        }

                        onClicked: _openNewDetail()
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

                        onClicked: page.navigateToStoryboard(page.projectId)
                    }
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: 16
                    model: bridge.characters.model
                    spacing: 8
                    clip: true

                    delegate: CharacterCardDelegate {
                        width: ListView.view.width - 32
                        characterId: model.characterId || 0
                        characterUuid: model.characterUuid || ""
                        characterName: model.name || ""
                        refCode: model.refCode || ""
                        description: model.description || ""
                        designImage: model.designImagePath || ""
                        designImageRevision: model.designImageRevision || 0
                        designImageBusy: generatingDesignCharUuids.indexOf(model.characterUuid || "") !== -1
                        multiSelect: _multiSelect
                        isSelected: _selectedIds.indexOf(characterUuid) >= 0
                        onCardClicked: {
                            if (_multiSelect) {
                                _toggleSelect(characterUuid)
                            } else {
                                _openEditDetail(model)
                            }
                        }
                        onToggleSelect: _toggleSelect(characterUuid)
                    }

                    Comp.EmptyState {
                        visible: bridge.characters.model.count === 0
                        anchors.centerIn: parent
                        text: "还没有角色"
                        buttonText: "新建"
                        onButtonClicked: _openNewDetail()
                    }
                }
            }
        }

        // ── 详情页 ──
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Comp.PageHeader {
                    projectName: _projectName
                    title: _isNewCharacter ? "新增角色" : "编辑角色"
                    Layout.fillWidth: true
                    onBackClicked: {
                        _isNewCharacter = false
                        _showDetail = false
                    }

                    Button {
                        visible: !_isNewCharacter
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 36
                        display: AbstractButton.IconOnly
                        icon.source: "qrc:/resources/icons/auto_awesome.svg"
                        icon.width: 20
                        icon.height: 20
                        icon.color: "white"
                        topPadding: 8
                        bottomPadding: 8
                        leftPadding: 8
                        rightPadding: 8
                        ToolTip.visible: hovered
                        ToolTip.text: "Ai"

                        background: Rectangle {
                            anchors.fill: parent
                            radius: parent.width / 2
                            color: parent.pressed ? "#E65100" : (parent.hovered ? "#FB8C00" : "#FF9800")
                        }

                        onClicked: characterAIDialog.open()
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

                        onClicked: {
                            if (_isNewCharacter) {
                                bridge.characters.save_new_character(
                                    projectId,
                                    nameInput.text.trim(),
                                    refCodeInput.text.trim(),
                                    descInput.text.trim(),
                                    voiceToneInput.text.trim(),
                                    voiceRefFileInput.text.trim()
                                )
                                _isNewCharacter = false
                            } else {
                                bridge.characters.save_existing_character(
                                    _editingCharUuid,
                                    nameInput.text.trim(),
                                    refCodeInput.text.trim(),
                                    descInput.text.trim(),
                                    voiceToneInput.text.trim(),
                                    voiceRefFileInput.text.trim()
                                )
                            }
                        }
                    }

                    Button {
                        visible: !_isNewCharacter
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
                        ToolTip.text: "删除"

                        background: Rectangle {
                            anchors.fill: parent
                            radius: Theme.radiusSmall
                            color: parent.hovered
                                ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                                : "transparent"
                        }

                        onClicked: {
                            confirmDialog.confirm(
                                "确定要删除此角色吗？",
                                function() {
                                    bridge.characters.delete_character(_editingCharUuid)
                                    _showDetail = false
                                }
                            )
                        }
                    }
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    Item {
                        width: Math.min(parent.width, 960)
                        height: contentCol.implicitHeight + 32
                        anchors.horizontalCenter: parent.horizontalCenter

                        RowLayout {
                            id: contentCol
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 16

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 12

                                Pane {
                                    Layout.fillWidth: true
                                    padding: 12
                                    background: Item {}

                                    GridLayout {
                                        anchors.fill: parent
                                        columns: 4
                                        columnSpacing: 12
                                        rowSpacing: 8

                                        Label {
                                            text: "角色名："
                                            font.pixelSize: Theme.fontSizeSmall
                                        }
                                        Comp.AppTextField {
                                            id: nameInput
                                            Layout.fillWidth: true
                                            Layout.columnSpan: 3
                                            Layout.preferredHeight: 32
                                            font.pixelSize: Theme.fontSizeSmall
                                            padding: 6
                                            leftPadding: 10
                                            rightPadding: 10
                                        }

                                        Label {
                                            text: "引用代号："
                                            font.pixelSize: Theme.fontSizeSmall
                                        }
                                        Comp.AppTextField {
                                            id: refCodeInput
                                            visible: _isNewCharacter
                                            placeholderText: "如 CHAR_A"
                                            Layout.fillWidth: true
                                            Layout.columnSpan: 3
                                            Layout.preferredHeight: 32
                                            font.pixelSize: Theme.fontSizeSmall
                                            padding: 6
                                            leftPadding: 10
                                            rightPadding: 10
                                        }
                                        Label {
                                            visible: !_isNewCharacter
                                            text: refCodeInput.text || "—"
                                            font.pixelSize: Theme.fontSizeSmall
                                            Layout.fillWidth: true
                                            Layout.columnSpan: 3
                                        }
                                    }
                                }

                                Pane {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    padding: 12
                                    background: Item {}

                                    ColumnLayout {
                                        anchors.fill: parent
                                        spacing: 8

                                        Label {
                                            text: "形象描述："
                                            font.pixelSize: Theme.fontSizeSmall
                                        }

                                        ScrollView {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            clip: true
                                            TextArea {
                                                id: descInput
                                                wrapMode: TextArea.Wrap
                                                font.pixelSize: Theme.fontSizeSmall
                                                padding: 10
                                            }
                                        }
                                    }
                                }

                                Pane {
                                    Layout.fillWidth: true
                                    padding: 12
                                    background: Item {}

                                    ColumnLayout {
                                        anchors.fill: parent
                                        spacing: 8

                                        Label {
                                            text: "音色描述："
                                            font.pixelSize: Theme.fontSizeSmall
                                        }

                                        Comp.AppTextField {
                                            id: voiceToneInput
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 32
                                            placeholderText: "如：温柔清脆的女声，语速适中，带有亲切感"
                                            font.pixelSize: Theme.fontSizeSmall
                                            padding: 6
                                            leftPadding: 10
                                            rightPadding: 10
                                        }

                                        Label {
                                            text: "音色参考文件："
                                            font.pixelSize: Theme.fontSizeSmall
                                            Layout.topMargin: 4
                                        }

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 8

                                            Comp.AppTextField {
                                                id: voiceRefFileInput
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 32
                                                placeholderText: "选择音频文件（暂未使用）"
                                                readOnly: true
                                                font.pixelSize: Theme.fontSizeSmall
                                                padding: 6
                                                leftPadding: 10
                                                rightPadding: 10
                                            }

                                            Button {
                                                text: "选择"
                                                Layout.preferredHeight: 32
                                                font.pixelSize: Theme.fontSizeSmall
                                                padding: 4
                                                leftPadding: 12
                                                rightPadding: 12
                                                onClicked: voiceFileDialog.open()
                                            }

                                            Button {
                                                text: "清除"
                                                Layout.preferredHeight: 32
                                                font.pixelSize: Theme.fontSizeSmall
                                                padding: 4
                                                leftPadding: 12
                                                rightPadding: 12
                                                visible: voiceRefFileInput.text.length > 0
                                                onClicked: voiceRefFileInput.text = ""
                                            }
                                        }
                                    }
                                }
                            }

                            Comp.ImagePicker {
                                Layout.preferredWidth: 320
                                Layout.fillHeight: true
                                visible: !_isNewCharacter
                                imageSource: _editingDesignImage
                                cacheKey: designImageCacheKey
                                busy: generatingDesignCharUuids.indexOf(_editingCharUuid) !== -1
                                onAiGenerateClicked: {
                                    characterAIDialog.openGenerateDesign()
                                }
                                onUploadClicked: charDesignDialog.open()
                                onDeleteClicked: {
                                    _editingDesignImage = ""
                                    if (_editingCharUuid)
                                        bridge.characters.delete_design_image(_editingCharUuid)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    QtDialogs.FileDialog {
        id: charDesignDialog
        title: "选择设计图"
        fileMode: QtDialogs.FileDialog.OpenFile
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.webp)", "所有文件 (*)"]
        onAccepted: {
            var p = selectedFile.toString()
            if (p.startsWith("file:///")) p = p.substring(8)
            bridge.characters.upload_design_image(_editingCharUuid, p)
        }
    }

    QtDialogs.FileDialog {
        id: voiceFileDialog
        title: "选择音色参考音频文件"
        fileMode: QtDialogs.FileDialog.OpenFile
        nameFilters: ["音频文件 (*.mp3 *.wav *.m4a *.ogg)", "所有文件 (*)"]
        onAccepted: {
            var p = selectedFile.toString()
            if (p.startsWith("file:///")) p = p.substring(8)
            voiceRefFileInput.text = p
        }
    }

    component CharacterCardDelegate: Pane {
        id: charCard
        property int characterId: 0
        property string characterUuid: ""
        property string characterName: ""
        property string refCode: ""
        property string description: ""
        property string designImage: ""
        property int designImageRevision: 0
        property bool designImageBusy: false
        property bool multiSelect: false
        property bool isSelected: false

        signal cardClicked()
        signal toggleSelect()

        padding: 0
        height: 100

        background: Rectangle {
            radius: Theme.cardRadius
            color: charCard.isSelected ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(0, 0, 0, 0.08)
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: multiSelect ? 48 : 16
            anchors.topMargin: 12
            anchors.bottomMargin: 12
            spacing: 12

            Item {
                width: 72
                height: 72

                Comp.ImagePreview {
                    anchors.fill: parent
                    imageSource: designImage
                    cacheKey: designImageRevision
                    busy: designImageBusy
                    fillMode: Image.PreserveAspectCrop
                    placeholderIcon: (!designImage && !designImageBusy && !characterName)
                        ? "qrc:/resources/icons/person.svg" : ""
                    placeholderIconSize: 32
                }

                Label {
                    anchors.centerIn: parent
                    text: characterName ? characterName[0] : ""
                    font.pixelSize: 24
                    visible: !designImage && !designImageBusy && characterName
                    z: 1
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                RowLayout {
                    spacing: 8
                    Label { text: characterName; font.pixelSize: Theme.fontSizeMedium; font.bold: true }
                    Rectangle {
                        width: refLabel.implicitWidth + 12; height: 20; radius: 10
                        Label {
                            id: refLabel
                            anchors.centerIn: parent
                            text: refCode; font.pixelSize: Theme.fontSizeTiny
                        }
                    }
                }
                Label {
                    text: description || "暂无形象描述"
                    font.pixelSize: Theme.fontSizeSmall
                    elide: Text.ElideRight
                    maximumLineCount: 2
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
            }
        }

        CheckBox {
            visible: multiSelect
            checked: isSelected
            anchors.right: parent.right
            anchors.rightMargin: 16
            anchors.verticalCenter: parent.verticalCenter
            onClicked: charCard.toggleSelect()
        }

        MouseArea {
            id: cardHover
            anchors.fill: parent
            hoverEnabled: true
            z: -1
            onClicked: charCard.cardClicked()
        }
    }

    function _openNewDetail() {
        _isNewCharacter = true
        _editingCharUuid = ""
        _editingDesignImage = ""
        nameInput.text = ""
        refCodeInput.text = ""
        descInput.text = ""
        voiceToneInput.text = ""
        voiceRefFileInput.text = ""
        _showDetail = true
    }

    function _openEditDetail(model) {
        _isNewCharacter = false
        _editingCharUuid = model.characterUuid || ""
        _editingDesignImage = model.designImagePath || ""
        nameInput.text = model.name || ""
        refCodeInput.text = model.refCode || ""
        descInput.text = model.description || ""
        voiceToneInput.text = model.voiceTone || ""
        voiceRefFileInput.text = model.voiceReferenceFile || ""
        _showDetail = true
    }

    function _toggleSelect(uuid) {
        var idx = _selectedIds.indexOf(uuid)
        var newIds = _selectedIds.slice()
        if (idx >= 0) {
            newIds.splice(idx, 1)
        } else {
            newIds.push(uuid)
        }
        _selectedIds = newIds
    }

    function _toggleSelectAll() {
        var allIds = JSON.parse(bridge.characters.get_all_ids())
        if (_selectedIds.length === allIds.length) {
            _selectedIds = []
        } else {
            _selectedIds = allIds
        }
    }

    Dialogs.AlertDialog {
        id: alertDialog
    }

    Dialogs.ConfirmDialog {
        id: confirmDialog
    }

    Dialogs.ImagePreviewDialog {
        id: imagePreviewDialog
    }

    Dialogs.AIOptimizeDialog {
        id: aiOptimizeDialog
        onOptimizeRequested: function(userInput) {
            bridge.characters.optimize_with_ai(userInput, page.projectId)
        }
    }

    Dialogs.CharacterAIDialog {
        id: characterAIDialog
        onRefineRequested: function(userInput) {
            bridge.characters.refine_description(_editingCharUuid, descInput.text.trim(), userInput)
        }
        onGenerateDesignRequested: function(userInput) {
            bridge.characters.generate_design_image(_editingCharUuid, projectId, userInput)
        }
    }
}
