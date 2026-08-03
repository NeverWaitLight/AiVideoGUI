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
    property int _editingCharId: -1
    property string _editingCharUuid: ""
    property bool _isNewCharacter: false
    property var _selectedIds: []
    property bool _multiSelect: false
    property bool _showDetail: false
    property string _editingDesignImage: ""

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
            bridge.characters.load_for_project(projectId)
            _selectedIds = []
            _showDetail = false
        }
    }

    Connections {
        target: bridge.characters
        function onData_changed() {
            bridge.characters.load_for_project(projectId)
        }
        function onCharacter_saved() {
            alertDialog.info("成功", "角色已保存")
            _showDetail = false
        }
        function onDesign_image_ready(uuid, path) {
            if (uuid === _editingCharUuid) {
                _editingDesignImage = path
            }
            alertDialog.info("成功", "角色设计图已生成")
        }
        function onDesign_image_failed(error) {
            alertDialog.error("错误", "设计图生成失败：" + error)
        }
        function onCharacters_generated(count) {
            aiOptimizeDialog.finishOptimizing()
            alertDialog.info("成功", "角色生成完成，共 " + count + " 个角色")
        }
        function onCharacters_optimized(count) {
            aiOptimizeDialog.finishOptimizing()
            alertDialog.info("成功", "角色优化完成，共 " + count + " 个角色")
        }
        function onError(msg) {
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
                    title: "角色管理"
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
                        ToolTip.text: "AI优化"

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
                        ToolTip.text: "AI 生成设计图"

                        background: Rectangle {
                            anchors.fill: parent
                            radius: parent.width / 2
                            color: parent.pressed ? "#E65100" : (parent.hovered ? "#FB8C00" : "#FF9800")
                        }

                        onClicked: bridge.characters.generate_design_image(_editingCharUuid, projectId)
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
                                    descInput.text.trim()
                                )
                                _isNewCharacter = false
                            } else {
                                bridge.characters.save_existing_character(
                                    _editingCharId,
                                    nameInput.text.trim(),
                                    refCodeInput.text.trim(),
                                    descInput.text.trim()
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

                    RowLayout {
                        width: parent.width
                        spacing: 16

                        Item { Layout.preferredWidth: 8 }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: 16

                            Item { width: 1; height: 8 }

                            Pane {
                                Layout.fillWidth: true
                                padding: 16

                                GridLayout {
                                    anchors.fill: parent
                                    columns: 4
                                    columnSpacing: 16
                                    rowSpacing: 12

                                    Label {
                                        text: "角色名："
                                        font.pixelSize: Theme.fontSizeMedium
                                    }
                                    Comp.AppTextField {
                                        id: nameInput
                                        Layout.fillWidth: true
                                        Layout.columnSpan: 3
                                    }

                                    Label {
                                        text: "引用代号："
                                        font.pixelSize: Theme.fontSizeMedium
                                    }
                                    Comp.AppTextField {
                                        id: refCodeInput
                                        visible: _isNewCharacter
                                        placeholderText: "如 CHAR_A"
                                        Layout.fillWidth: true
                                        Layout.columnSpan: 3
                                    }
                                    Label {
                                        visible: !_isNewCharacter
                                        text: refCodeInput.text || "—"
                                        font.pixelSize: Theme.fontSizeMedium
                                        Layout.fillWidth: true
                                        Layout.columnSpan: 3
                                    }
                                }
                            }

                            Pane {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                padding: 16

                                ColumnLayout {
                                    anchors.fill: parent
                                    spacing: 12

                                    Label {
                                        text: "形象描述："
                                        font.pixelSize: Theme.fontSizeMedium
                                    }

                                    ScrollView {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        clip: true
                                        TextArea {
                                            id: descInput
                                            wrapMode: TextArea.Wrap
                                            font.pixelSize: Theme.fontSizeSmall
                                            padding: 12
                                        }
                                    }

                                }
                            }

                            Item { width: 1; height: 16 }
                        }

                        Comp.ImageUploadPanel {
                            Layout.preferredWidth: 320
                            Layout.fillHeight: true
                            visible: !_isNewCharacter
                            imageSource: _editingDesignImage
                            placeholderText: "暂无设计图"
                            onUploadClicked: charDesignDialog.open()
                            onClearClicked: _editingDesignImage = ""
                        }

                        Item { Layout.preferredWidth: 8 }
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

    component CharacterCardDelegate: Pane {
        id: charCard
        property int characterId: 0
        property string characterUuid: ""
        property string characterName: ""
        property string refCode: ""
        property string description: ""
        property string designImage: ""
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

            Rectangle {
                width: 72; height: 72; radius: 36
                clip: true
                Image {
                    anchors.fill: parent
                    source: designImage ? "file:///" + designImage : ""
                    fillMode: Image.PreserveAspectCrop
                    visible: source !== ""
                }
                Label {
                    anchors.centerIn: parent
                    text: characterName ? characterName[0] : ""
                    font.pixelSize: 24
                    visible: !designImage && characterName
                }
                Image {
                    anchors.centerIn: parent
                    source: "qrc:/resources/icons/person.svg"
                    sourceSize.width: 32
                    sourceSize.height: 32
                    visible: !designImage && !characterName
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
        _editingCharId = -1
        _editingCharUuid = ""
        _editingDesignImage = ""
        nameInput.text = ""
        refCodeInput.text = ""
        descInput.text = ""
        _showDetail = true
    }

    function _openEditDetail(model) {
        _isNewCharacter = false
        _editingCharId = model.characterId
        _editingCharUuid = model.characterUuid || ""
        _editingDesignImage = model.designImagePath || ""
        nameInput.text = model.name || ""
        refCodeInput.text = model.refCode || ""
        descInput.text = model.description || ""
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

    Dialogs.AIOptimizeDialog {
        id: aiOptimizeDialog
        onOptimizeRequested: function(userInput) {
            bridge.characters.optimize_with_ai(userInput, page.projectId)
        }
    }
}
