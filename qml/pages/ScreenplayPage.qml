import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: page
    property int projectId: -1
    property bool _showHistory: false
    property bool _showDetail: false
    property int _editingSceneId: -1
    property bool _isNewScene: false
    property string _outlineContent: ""
    property bool _multiSelect: false
    property var _selectedIds: []

    signal backClicked()
    signal navigateToCharacters(int projectId)

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
            bridge.screenplay.load_for_project(projectId)
            _showDetail = false
            _showHistory = false
        }
    }

    Connections {
        target: bridge.screenplay

        function onScene_saved() {
            alertDialog.info("成功", "场次已保存")
            _showDetail = false
        }

        function onHistory_saved() {
            alertDialog.info("成功", "历史版本已保存")
        }

        function onHistory_restored() {
            alertDialog.info("成功", "已恢复到历史版本")
        }

        function onScript_generated(title, sceneCount) {
            aiOptimizeDialog.finishOptimizing()
            alertDialog.info("成功", "剧本已生成，共 " + sceneCount + " 场")
        }

        function onScript_optimized(sceneCount) {
            aiOptimizeDialog.finishOptimizing()
            alertDialog.info("成功", "剧本优化完成，共 " + sceneCount + " 场")
        }

        function onScript_failed(error) {
            aiOptimizeDialog.finishOptimizing()
            alertDialog.error("错误", "生成剧本失败：" + error)
        }

        function onNew_scene_created() {
            _isNewScene = true
            _editingSceneId = -1
            _showDetail = true
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
                    title: "剧本"
                    subtitle: "共" + bridge.screenplay.sceneModel.count + "场"
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
                            "确定要删除选中的 " + _selectedIds.length + " 个场次吗？",
                            function() {
                                for (var i = 0; i < _selectedIds.length; i++)
                                    bridge.screenplay.delete_scene(_selectedIds[i])
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
                            var m = bridge.screenplay.sceneModel
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
                        enabled: !bridge.screenplay.isOptimizing
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

                        onClicked: aiOptimizeDialog.show("AI 优化剧本", "请输入优化要求（如修改剧情、增减场次等）...", "开始优化")
                    }

                    Button {
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
                        ToolTip.text: "新增场次"

                        background: Rectangle {
                            anchors.fill: parent
                            radius: Theme.radiusSmall
                            color: parent.hovered
                                ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                                : "transparent"
                        }

                        onClicked: bridge.screenplay.prepare_new_scene(page.projectId)
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

                        onClicked: page.navigateToCharacters(page.projectId)
                    }
                }

                SplitView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    orientation: Qt.Horizontal

                    handle: Rectangle {
                        implicitWidth: 1
                    }

                    Item {
                        SplitView.fillWidth: true
                        SplitView.minimumWidth: 400

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            spacing: 12

                            ScrollView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true

                                ListView {
                                    id: sceneListView
                                    model: bridge.screenplay.sceneModel
                                    spacing: 10
                                    clip: true

                                    delegate: SceneCardDelegate {
                                        width: ListView.view.width - 32
                                        sceneNumber: model.sceneNumber || 0
                                        location: model.location || ""
                                        locationType: model.locationType || ""
                                        timeType: model.timeType || ""
                                        content: model.content || ""
                                        multiSelect: _multiSelect
                                        selected: _selectedIds.indexOf(model.sceneId) >= 0
                                        onClicked: {
                                            if (_multiSelect) {
                                                var ids = _selectedIds.slice()
                                                var idx = ids.indexOf(model.sceneId)
                                                if (idx >= 0) ids.splice(idx, 1)
                                                else ids.push(model.sceneId)
                                                _selectedIds = ids
                                            } else {
                                                _isNewScene = false
                                                _editingSceneId = model.sceneId
                                                bridge.screenplay.load_scene(model.sceneId)
                                                _showDetail = true
                                            }
                                        }
                                        onDeleteRequested: {
                                            confirmDialog.confirm(
                                                "确定要删除第" + model.sceneNumber + "场吗？",
                                                function() { bridge.screenplay.delete_scene(model.sceneId) }
                                            )
                                        }
                                    }
                                }
                            }

                            Comp.EmptyState {
                                visible: bridge.screenplay.sceneModel.count === 0
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                text: "暂无场次，请从大纲生成剧本"
                            }
                        }
                    }
                }
            }
        }

        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Comp.PageHeader {
                    title: "第 " + bridge.screenplay.curSceneNumber + " 场"
                    Layout.fillWidth: true
                    onBackClicked: {
                        _isNewScene = false
                        _showDetail = false
                        bridge.screenplay.load_for_project(page.projectId)
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
                            if (_isNewScene) {
                                bridge.screenplay.create_scene(
                                    page.projectId,
                                    locationTypeCombo.currentIndex,
                                    locationInput.text,
                                    timeTypeCombo.currentIndex,
                                    timeDetailInput.text,
                                    contentEdit.text
                                )
                                _isNewScene = false
                            } else {
                                _saveCurrentScene()
                            }
                        }
                    }

                    Button {
                        visible: !_isNewScene
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
                                "确定要删除第" + bridge.screenplay.curSceneNumber + "场吗？",
                                function() {
                                    bridge.screenplay.delete_scene(_editingSceneId)
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

                    ColumnLayout {
                        width: parent.width
                        spacing: 16

                        Item { width: 1; height: 8 }

                        Pane {
                            Layout.fillWidth: true
                            Layout.leftMargin: 24
                            Layout.rightMargin: 24
                            padding: 16

                            GridLayout {
                                anchors.fill: parent
                                columns: 4
                                columnSpacing: 16
                                rowSpacing: 12

                                Label {
                                    text: "场次号："
                                    font.pixelSize: Theme.fontSizeMedium
                                }
                                Label {
                                    text: "第 " + bridge.screenplay.curSceneNumber + " 场"
                                    font.pixelSize: Theme.fontSizeMedium
                                    font.bold: true
                                }
                                Item { Layout.fillWidth: true }
                                Item { Layout.fillWidth: true }

                                Label {
                                    text: "内外景："
                                    font.pixelSize: Theme.fontSizeMedium
                                }
                                ComboBox {
                                    id: locationTypeCombo
                                    model: ["内景", "外景", "内景/外景"]
                                    currentIndex: bridge.screenplay.curLocationTypeIndex
                                    Layout.preferredWidth: 160
                                }
                                Item { Layout.fillWidth: true }
                                Item { Layout.fillWidth: true }

                                Label {
                                    text: "地点："
                                    font.pixelSize: Theme.fontSizeMedium
                                }
                                Comp.AppTextField {
                                    id: locationInput
                                    text: bridge.screenplay.curLocation
                                    placeholderText: "如：审讯室、老城区街道"
                                    Layout.fillWidth: true
                                    Layout.columnSpan: 3
                                }

                                Label {
                                    text: "时间："
                                    font.pixelSize: Theme.fontSizeMedium
                                }
                                ComboBox {
                                    id: timeTypeCombo
                                    model: ["日", "夜", "晨", "黄昏", "傍晚", "自定义"]
                                    currentIndex: bridge.screenplay.curTimeTypeIndex
                                    Layout.preferredWidth: 160
                                }
                                Label {
                                    text: "详细时间："
                                    font.pixelSize: Theme.fontSizeMedium
                                    visible: timeTypeCombo.currentIndex === 5
                                }
                                Comp.AppTextField {
                                    id: timeDetailInput
                                    text: bridge.screenplay.curTimeDetail
                                    placeholderText: "如：下午3点"
                                    visible: timeTypeCombo.currentIndex === 5
                                    Layout.fillWidth: true
                                }
                            }
                        }

                        ScrollView {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 400
                            Layout.leftMargin: 24
                            Layout.rightMargin: 24
                            clip: true

                            TextArea {
                                id: contentEdit
                                text: bridge.screenplay.curContent
                                placeholderText: "请输入场次内容（动作描述 + 对话）..."
                                wrapMode: TextArea.Wrap
                                font.pixelSize: Theme.fontSizeMedium
                                padding: 12
                        }

                        Item { width: 1; height: 16 }
                    }
                }
            }
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
            bridge.screenplay.optimize_with_ai(userInput, page.projectId)
        }
    }

    function _saveCurrentScene() {
        bridge.screenplay.save_scene(
            _editingSceneId,
            locationTypeCombo.currentIndex,
            locationInput.text,
            timeTypeCombo.currentIndex,
            timeDetailInput.text,
            contentEdit.text
        )
    }

    component SceneCardDelegate: Pane {
        id: cardRoot
        property int sceneNumber: 0
        property string location: ""
        property string locationType: ""
        property string timeType: ""
        property string content: ""
        property bool multiSelect: false
        property bool selected: false

        signal clicked()
        signal deleteRequested()

        padding: 0
        height: 110

        background: Rectangle {
            radius: Theme.cardRadius
            color: cardRoot.selected ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(0, 0, 0, 0.08)
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: multiSelect ? 48 : 16
            anchors.topMargin: 12
            anchors.bottomMargin: 12
            spacing: 6

            RowLayout {
                spacing: 10
                Label {
                    text: "第 " + sceneNumber + " 场"
                    font.pixelSize: Theme.fontSizeLarge
                    font.bold: true
                }
                Rectangle {
                    width: locTypeLabel.implicitWidth + 12
                    height: 20
                    radius: Theme.radiusSmall
                    Label {
                        id: locTypeLabel
                        anchors.centerIn: parent
                        text: {
                            switch(locationType) {
                                case "interior": return "内景"
                                case "exterior": return "外景"
                                case "interior_exterior": return "内景/外景"
                                default: return "内景"
                            }
                        }
                        font.pixelSize: Theme.fontSizeSmall
                    }
                }
                Item { Layout.fillWidth: true }
            }

            Label {
                text: location
                font.pixelSize: Theme.fontSizeSmall
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Label {
                text: content.length > 60 ? content.substring(0, 60) + "..." : content
                font.pixelSize: Theme.fontSizeSmall
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }

        CheckBox {
            visible: multiSelect
            checked: cardRoot.selected
            anchors.right: parent.right
            anchors.rightMargin: 16
            anchors.verticalCenter: parent.verticalCenter
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: cardRoot.clicked()
        }
        HoverHandler { id: cardHover }
    }
}
}
