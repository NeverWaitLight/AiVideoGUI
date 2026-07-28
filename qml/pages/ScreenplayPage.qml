import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: page
    property int projectId: -1
    property bool _showHistory: false
    property bool _showDetail: false
    property int _editingSceneId: -1
    property string _outlineContent: ""

    signal backClicked()
    signal generateStoryboardClicked(int projectId)

    onProjectIdChanged: {
        if (projectId > 0) {
            bridge.screenplay.load_for_project(projectId)
            _showDetail = false
            _showHistory = false
        }
    }

    // Bridge connections
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
            alertDialog.info("成功", "剧本已生成，共 " + sceneCount + " 场")
        }

        function onScript_failed(error) {
            alertDialog.error("错误", "生成剧本失败：" + error)
        }

        function onError(msg) {
            alertDialog.error("错误", msg)
        }
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: _showDetail ? 1 : 0

        // ═══════════ 0: 场次列表视图 ═══════════
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Comp.PageHeader {
                    title: "剧本编辑"
                    Layout.fillWidth: true
                    onBackClicked: page.backClicked()

                    Button {
                        text: "生成分镜"
                        highlighted: true
                        enabled: bridge.screenplay.sceneModel.count > 0
                        onClicked: page.generateStoryboardClicked(page.projectId)
                    }

                    Button {
                        text: "保存历史版本"
                        onClicked: bridge.screenplay.save_history()
                    }

                    Button {
                        text: _showHistory ? "隐藏历史" : "历史版本"
                        onClicked: _showHistory = !_showHistory
                    }
                }

                SplitView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    orientation: Qt.Horizontal

                    handle: Rectangle {
                        implicitWidth: 1
                        color: Theme.border
                    }

                    // 左侧：场次列表
                    Item {
                        SplitView.fillWidth: true
                        SplitView.minimumWidth: 400

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            spacing: 12

                            Label {
                                text: "场次列表"
                                font.pixelSize: Theme.fontSizeMedium
                                font.bold: true
                                color: Theme.textAI
                            }

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
                                        width: ListView.view.width - 4
                                        sceneNumber: model.sceneNumber || 0
                                        location: model.location || ""
                                        locationType: model.locationType || ""
                                        timeType: model.timeType || ""
                                        content: model.content || ""
                                        onClicked: {
                                            _editingSceneId = model.sceneId
                                            bridge.screenplay.load_scene(model.sceneId)
                                            _showDetail = true
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

                    // 右侧：历史版本面板（可切换）
                    Rectangle {
                        visible: _showHistory
                        SplitView.preferredWidth: _showHistory ? 300 : 0
                        SplitView.minimumWidth: 200
                        color: "#FAFAFA"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 12

                            Label {
                                text: "历史版本"
                                font.pixelSize: Theme.fontSizeMedium
                                font.bold: true
                                color: Theme.textAI
                            }

                            ListView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                spacing: 6
                                model: bridge.screenplay.historyModel

                                delegate: Pane {
                                    width: ListView.view.width - 4
                                    padding: 8

                                    background: Rectangle {
                                        radius: Theme.borderRadius
                                        color: parent.hovered ? "#F0F0F0" : "#FFFFFF"
                                        border.color: Theme.border
                                    }

                                    RowLayout {
                                        anchors.fill: parent
                                        spacing: 8

                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 2
                                            Label {
                                                text: model.displayTime || ""
                                                font.pixelSize: Theme.fontSizeSmall
                                                color: Theme.textAI
                                            }
                                            Label {
                                                text: (model.sceneCount || 0) + " 场"
                                                font.pixelSize: Theme.fontSizeSmall
                                                color: Theme.textSecondary
                                            }
                                        }

                                        Button {
                                            text: "恢复"
                                            flat: true
                                            onClicked: {
                                                var ts = model.createdAt
                                                confirmDialog.confirm(
                                                    "确定要恢复到此历史版本吗？当前所有场次将被覆盖。",
                                                    function() { bridge.screenplay.restore_history(ts) }
                                                )
                                            }
                                        }
                                    }
                                }

                                Label {
                                    visible: !bridge.screenplay.historyModel || bridge.screenplay.historyModel.count === 0
                                    anchors.centerIn: parent
                                    text: "暂无历史版本"
                                    color: Theme.textSecondary
                                    font.pixelSize: Theme.fontSizeSmall
                                }
                            }
                        }
                    }
                }
            }
        }

        // ═══════════ 1: 场次详情编辑视图 ═══════════
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Comp.PageHeader {
                    title: "第 " + bridge.screenplay.curSceneNumber + " 场"
                    Layout.fillWidth: true
                    onBackClicked: {
                        _showDetail = false
                        bridge.screenplay.load_for_project(page.projectId)
                    }

                    Button {
                        text: "保存"
                        highlighted: true
                        onClicked: _saveCurrentScene()
                    }

                    Button {
                        text: "删除"
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

                        // 场景信息卡片
                        Pane {
                            Layout.fillWidth: true
                            Layout.leftMargin: 24
                            Layout.rightMargin: 24
                            padding: 16

                            background: Rectangle {
                                radius: Theme.cardRadius
                                color: "#FFFFFF"
                                border.color: Theme.border
                            }

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
                                    color: Theme.primary
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
                                TextField {
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
                                TextField {
                                    id: timeDetailInput
                                    text: bridge.screenplay.curTimeDetail
                                    placeholderText: "如：下午3点"
                                    visible: timeTypeCombo.currentIndex === 5
                                    Layout.fillWidth: true
                                }
                            }
                        }

                        // 场次内容
                        Label {
                            text: "场次内容"
                            font.pixelSize: Theme.fontSizeMedium
                            font.bold: true
                            color: Theme.textAI
                            Layout.leftMargin: 24
                        }

                        ScrollView {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 400
                            Layout.leftMargin: 24
                            Layout.rightMargin: 24
                            clip: true

                            background: Rectangle {
                                radius: Theme.borderRadius
                                color: "#FFFFFF"
                                border.color: contentEdit.activeFocus ? Theme.primary : Theme.border
                            }

                            TextArea {
                                id: contentEdit
                                text: bridge.screenplay.curContent
                                placeholderText: "请输入场次内容（动作描述 + 对话）..."
                                wrapMode: TextArea.Wrap
                                font.pixelSize: Theme.fontSizeMedium
                                padding: 12
                                color: Theme.textAI
                            }
                        }

                        Item { width: 1; height: 16 }
                    }
                }
            }
        }
    }

    // ── 对话框 ──

    Dialogs.AlertDialog {
        id: alertDialog
    }

    Dialogs.ConfirmDialog {
        id: confirmDialog
    }

    // ── 内部函数 ──

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

    // ── 场次卡片组件 ──

    component SceneCardDelegate: Pane {
        id: cardRoot
        property int sceneNumber: 0
        property string location: ""
        property string locationType: ""
        property string timeType: ""
        property string content: ""

        signal clicked()
        signal deleteRequested()

        padding: 12
        height: 110

        background: Rectangle {
            radius: Theme.borderRadius
            color: cardHover.hovered ? "#F0F5FF" : "#FFFFFF"
            border.color: Theme.border
            border.width: 1
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 6

            // 标题行
            RowLayout {
                spacing: 10
                Label {
                    text: "第 " + sceneNumber + " 场"
                    font.pixelSize: Theme.fontSizeLarge
                    font.bold: true
                    color: Theme.primary
                }
                Rectangle {
                    width: locTypeLabel.implicitWidth + 12
                    height: 20
                    radius: 4
                    color: "#E3F2FD"
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
                        color: "#666"
                    }
                }
                Item { Layout.fillWidth: true }
                Label {
                    text: {
                        switch(timeType) {
                            case "day": return "日"
                            case "night": return "夜"
                            case "dawn": return "晨"
                            case "dusk": return "黄昏"
                            case "evening": return "傍晚"
                            default: return "日"
                        }
                    }
                    font.pixelSize: Theme.fontSizeSmall
                    color: Theme.textSecondary
                }
            }

            // 地点
            Label {
                text: location
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.textAI
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            // 内容预览
            Label {
                text: content.length > 60 ? content.substring(0, 60) + "..." : content
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.textSecondary
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: cardRoot.clicked()
        }
        HoverHandler { id: cardHover }
    }
}
