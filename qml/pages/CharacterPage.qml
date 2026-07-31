import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs as QtDialogs
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: page
    property int projectId: -1
    property bool _editingExisting: false
    property int _editingCharId: -1
    property string _editingCharUuid: ""
    property var _selectedIds: []

    signal backClicked()

    onProjectIdChanged: {
        if (projectId > 0) {
            bridge.characters.load_for_project(projectId)
            _selectedIds = []
        }
    }

    Connections {
        target: bridge.characters
        function onData_changed() {
            bridge.characters.load_for_project(projectId)
        }
        function onDesign_image_ready(uuid, path) {
            alertDialog.info("成功", "角色设计图已生成")
        }
        function onDesign_image_failed(error) {
            alertDialog.error("错误", "设计图生成失败：" + error)
        }
        function onError(msg) {
            alertDialog.error("错误", msg)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Comp.PageHeader {
            title: "角色管理"
            Layout.fillWidth: true
            onBackClicked: page.backClicked()

            Button {
                Layout.preferredHeight: 34
                text: "全选"
                visible: bridge.characters.model.count > 0
                topPadding: 6
                bottomPadding: 6
                leftPadding: 12
                rightPadding: 12
                onClicked: _toggleSelectAll()
            }

            Button {
                Layout.preferredHeight: 34
                text: "删除"
                visible: _selectedIds.length > 0
                topPadding: 6
                bottomPadding: 6
                leftPadding: 12
                rightPadding: 12
                onClicked: confirmDialog.confirm(
                    "确定要删除选中的 " + _selectedIds.length + " 个角色吗？",
                    function() {
                        bridge.characters.batch_delete(_selectedIds)
                        _selectedIds = []
                    }
                )
            }

            Button {
                Layout.preferredHeight: 34
                text: "新建"
                highlighted: true
                topPadding: 6
                bottomPadding: 6
                leftPadding: 12
                rightPadding: 12
                onClicked: _openAddDialog()
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
                width: ListView.view.width - 4
                characterId: model.characterId || 0
                characterUuid: model.characterUuid || ""
                characterName: model.name || ""
                refCode: model.refCode || ""
                description: model.description || ""
                designImage: model.designImagePath || ""
                isSelected: _selectedIds.indexOf(characterId) >= 0
                onCardClicked: _openEditDialog(model)
                onToggleSelect: _toggleSelect(characterId)
            }

            Comp.EmptyState {
                visible: bridge.characters.model.count === 0
                anchors.centerIn: parent
                text: "还没有角色"
                buttonText: "新建"
                onButtonClicked: _openAddDialog()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 32
            border.width: 1

            Label {
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 20
                anchors.left: parent.left
                text: "共 " + bridge.characters.model.count + " 个角色"
                font.pixelSize: 12
            }
        }
    }

    Dialog {
        id: charDialog
        modal: true
        title: _editingExisting ? "编辑角色" : "新增角色"
        width: 520
        height: 540
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel

        onAccepted: {
            if (_editingExisting) {
                bridge.characters.update_character(
                    _editingCharId,
                    nameInput.text.trim(),
                    refCodeInput.text.trim(),
                    descInput.text.trim()
                )
            } else {
                bridge.characters.create_character(
                    projectId,
                    nameInput.text.trim(),
                    refCodeInput.text.trim(),
                    descInput.text.trim()
                )
            }
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 12

            GridLayout {
                columns: 2
                columnSpacing: 12
                rowSpacing: 12

                Label { text: "角色名："; font.pixelSize: Theme.fontSizeMedium }
                Comp.AppTextField {
                    id: nameInput
                    placeholderText: "角色名字"
                    Layout.fillWidth: true
                }

                Label { text: "引用代号："; font.pixelSize: Theme.fontSizeMedium }
                Comp.AppTextField {
                    id: refCodeInput
                    placeholderText: "如 CHAR_A"
                    Layout.fillWidth: true
                }
            }

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
                    placeholderText: "结构化形象描述，每行一个分区：\n[物种] 人类-黄种人\n[外貌] 25岁女性，瓜子脸\n[发型] 齐肩黑色直发\n[发色] 自然黑\n[瞳色] 深棕色\n[体型] 165cm，纤细匀称\n[上装] 白色棉质衬衫\n[裤子] 深蓝色高腰牛仔裤\n[鞋袜] 白色帆布鞋\n[帽子] 无"
                    wrapMode: TextArea.Wrap
                    font.pixelSize: Theme.fontSizeSmall
                    padding: 12
                }
            }

            RowLayout {
                spacing: 8
                Button {
                    text: "AI 提取特征"
                    visible: descInput.text.trim().length > 0
                    onClicked: {
                        var traits = bridge.characters.extract_traits(descInput.text)
                        if (traits) {
                            descInput.text = traits
                        }
                    }
                }
                Button {
                    text: "AI 生成设计图"
                    highlighted: true
                    visible: _editingExisting
                    onClicked: bridge.characters.generate_design_image(_editingCharUuid, projectId)
                }
                Button {
                    text: "上传图片"
                    visible: _editingExisting
                    onClicked: charDesignDialog.open()
                }
                Item { Layout.fillWidth: true }
                Button {
                    text: "删除"
                    visible: _editingExisting
                    onClicked: {
                        charDialog.close()
                        confirmDialog.confirm(
                            "确定要删除此角色吗？",
                            function() { bridge.characters.delete_character(_editingCharId) }
                        )
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

    Dialogs.AlertDialog { id: alertDialog }
    Dialogs.ConfirmDialog { id: confirmDialog }

    component CharacterCardDelegate: Pane {
        id: charCard
        property int characterId: 0
        property string characterUuid: ""
        property string characterName: ""
        property string refCode: ""
        property string description: ""
        property string designImage: ""
        property bool isSelected: false

        signal cardClicked()
        signal toggleSelect()

        padding: 10
        height: 100

        RowLayout {
            anchors.fill: parent
            spacing: 12

            CheckBox {
                checked: isSelected
                onToggled: toggleSelect()
            }

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

        MouseArea {
            id: cardHover
            anchors.fill: parent
            hoverEnabled: true
            z: -1
            onClicked: charCard.cardClicked()
        }
    }

    function _openAddDialog() {
        _editingExisting = false
        _editingCharId = -1
        _editingCharUuid = ""
        nameInput.text = ""
        refCodeInput.text = ""
        descInput.text = ""
        charDialog.open()
    }

    function _openEditDialog(model) {
        _editingExisting = true
        _editingCharId = model.characterId
        _editingCharUuid = model.characterUuid || ""
        nameInput.text = model.name || ""
        refCodeInput.text = model.refCode || ""
        descInput.text = model.description || ""
        charDialog.open()
    }

    function _toggleSelect(charId) {
        var idx = _selectedIds.indexOf(charId)
        var newIds = _selectedIds.slice()
        if (idx >= 0) {
            newIds.splice(idx, 1)
        } else {
            newIds.push(charId)
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
}
