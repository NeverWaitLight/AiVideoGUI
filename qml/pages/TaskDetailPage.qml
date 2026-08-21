import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Item {
    id: root

    property int taskId: 0

    signal backClicked()

    onTaskIdChanged: {
        if (taskId > 0) {
            loadTaskDetail()
        }
    }

    Component.onCompleted: {
        if (taskId > 0) {
            loadTaskDetail()
        }
    }

    function loadChildTasks() {
        childTaskModel.clear()
        var children = bridge.tasks.list_child_tasks(taskId)
        for (var i = 0; i < children.length; i++) {
            var c = children[i]
            childTaskModel.append({
                id: c.id || 0,
                type: c.type || "",
                provider_name: c.provider_name || "",
                model_name: c.model_name || "",
                status: c.status || ""
            })
        }
    }

    function loadTaskDetail() {
        var task = bridge.tasks.get_task_detail(taskId)
        if (task && task.id) {
            titleLabel.text = "任务详情-" + task.id
            typeLabel.text = task.type || ""
            providerNameLabel.text = task.provider_name || ""
            modelNameLabel.text = task.model_name || ""
            statusLabel.text = task.status || ""
            completedLabel.text = task.completed ? "是" : "否"

            // 格式化 JSON
            var params = task.request_params || ""
            try {
                var jsonObj = JSON.parse(params)
                requestParamsText.text = JSON.stringify(jsonObj, null, 2)
            } catch (e) {
                requestParamsText.text = params
            }

            var responseData = task.response_data || ""
            try {
                var responseJson = JSON.parse(responseData)
                responseDataText.text = JSON.stringify(responseJson, null, 2)
            } catch (e) {
                responseDataText.text = responseData
            }

            remoteUrlLabel.text = task.remote_url || ""
            localPathLabel.text = task.local_path || ""
            errorMessageLabel.text = task.error_message || ""
            callerTypeLabel.text = task.caller_type || ""
            callerIdLabel.text = task.caller_id || ""

            // 处理父任务ID
            var parentIds = task.parent_ids || ""
            if (parentIds) {
                var ids = parentIds.split(",")
                var lastId = ids[ids.length - 1].trim()
                parentTaskButton.text = "#" + lastId
                parentTaskButton.visible = true
                childTaskModel.clear()
            } else {
                parentTaskButton.visible = false
                loadChildTasks()
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Pane {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            padding: 5

            background: Rectangle {
                color: "transparent"
                border.width: 0
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 1
                    color: "white"
                }
            }

            RowLayout {
                anchors.fill: parent
                spacing: 12

                Button {
                    width: 34
                    height: 34
                    flat: true
                    display: AbstractButton.IconOnly
                    icon.source: "qrc:/resources/icons/arrow_back.svg"
                    icon.width: 20
                    icon.height: 20
                    topPadding: 7
                    bottomPadding: 7
                    leftPadding: 7
                    rightPadding: 7
                    ToolTip.visible: hovered
                    ToolTip.text: "返回"
                    onClicked: root.backClicked()

                    background: Rectangle {
                        anchors.fill: parent
                        radius: Theme.radiusSmall
                        color: parent.hovered
                            ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                            : "transparent"
                    }
                }

                Label {
                    id: titleLabel
                    text: "任务详情"
                    font.pixelSize: Theme.fontSizeMedium
                    font.bold: true
                }

                Item { Layout.fillWidth: true }

                Button {
                    width: 34
                    height: 34
                    flat: true
                    display: AbstractButton.IconOnly
                    icon.source: "qrc:/resources/icons/refresh.svg"
                    icon.width: 20
                    icon.height: 20
                    topPadding: 7
                    bottomPadding: 7
                    leftPadding: 7
                    rightPadding: 7
                    ToolTip.visible: hovered
                    ToolTip.text: "刷新"
                    onClicked: loadTaskDetail()

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

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth

            ColumnLayout {
                id: contentColumn
                width: parent.width
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                anchors.topMargin: 20
                anchors.bottomMargin: 20
                spacing: 16

                Control {
                    Layout.fillWidth: true
                    padding: 20

                    background: Rectangle {
                        radius: 8
                        color: "transparent"
                        border.width: 1
                        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                    }

                    contentItem: GridLayout {
                        columns: 4
                        rowSpacing: 12
                        columnSpacing: 20

                        Label { text: "类型:"; font.weight: Font.Medium }
                        Label { id: typeLabel; Layout.fillWidth: true }

                        Label { text: "服务商:"; font.weight: Font.Medium }
                        Label { id: providerNameLabel; Layout.fillWidth: true }

                        Label { text: "模型:"; font.weight: Font.Medium }
                        Label { id: modelNameLabel; Layout.fillWidth: true }

                        Label { text: "状态:"; font.weight: Font.Medium }
                        Label {
                            id: statusLabel
                            Layout.fillWidth: true
                            color: {
                                if (text === "succeeded") return Material.color(Material.Green)
                                if (text === "failed") return Material.color(Material.Red)
                                if (text === "running") return Material.color(Material.Blue)
                                return Material.foreground
                            }
                        }

                        Label { text: "已完成:"; font.weight: Font.Medium }
                        Label { id: completedLabel; Layout.fillWidth: true }

                        Label { text: "调用者类型:"; font.weight: Font.Medium }
                        Label { id: callerTypeLabel; Layout.fillWidth: true }

                        Label { text: "调用者ID:"; font.weight: Font.Medium }
                        Label { id: callerIdLabel; Layout.fillWidth: true }

                        Label { text: "父任务:"; font.weight: Font.Medium }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Button {
                                id: parentTaskButton
                                visible: false
                                flat: true
                                font.pixelSize: 12
                                padding: 4
                                leftPadding: 8
                                rightPadding: 8
                                onClicked: {
                                    var parentId = text.replace("#", "")
                                    root.taskId = parseInt(parentId)
                                }

                                background: Rectangle {
                                    radius: 4
                                    color: parent.hovered
                                        ? Qt.rgba(Material.accent.r, Material.accent.g, Material.accent.b, 0.1)
                                        : Qt.rgba(Material.accent.r, Material.accent.g, Material.accent.b, 0.05)
                                    border.width: 1
                                    border.color: Material.accent
                                }

                                contentItem: Label {
                                    text: parent.text
                                    color: Material.accent
                                    font.pixelSize: 12
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }

                            Label {
                                id: noParentLabel
                                text: "-"
                                visible: !parentTaskButton.visible
                            }

                            Item { Layout.fillWidth: true }
                        }

                        Label { text: "远程URL:"; font.weight: Font.Medium }
                        Label {
                            id: remoteUrlLabel
                            Layout.fillWidth: true
                            Layout.columnSpan: 3
                            wrapMode: Text.WrapAnywhere
                            font.family: "Consolas"
                            font.pixelSize: 11
                        }

                        Label { text: "本地路径:"; font.weight: Font.Medium }
                        Label {
                            id: localPathLabel
                            Layout.fillWidth: true
                            Layout.columnSpan: 3
                            wrapMode: Text.WrapAnywhere
                            font.family: "Consolas"
                            font.pixelSize: 11
                        }
                    }
                }

                Label {
                    text: "子任务"
                    font.pixelSize: 16
                    font.weight: Font.Medium
                    visible: childTaskModel.count > 0
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: childTaskRow.implicitHeight
                    visible: childTaskModel.count > 0
                    clip: true
                    ScrollBar.vertical.policy: ScrollBar.AlwaysOff

                    Row {
                        id: childTaskRow
                        spacing: 12

                        Repeater {
                            model: ListModel { id: childTaskModel }

                            Control {
                                width: 200
                                height: 100
                                padding: 12

                                background: Rectangle {
                                    radius: 8
                                    color: Material.background
                                    border.width: 1
                                    border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                                }

                                contentItem: ColumnLayout {
                                    spacing: 6

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        Rectangle {
                                            Layout.preferredWidth: 28
                                            Layout.preferredHeight: 28
                                            radius: 4
                                            color: {
                                                if (model.status === "succeeded") return Material.color(Material.Green, Material.Shade200)
                                                if (model.status === "failed") return Material.color(Material.Red, Material.Shade200)
                                                if (model.status === "running") return Material.color(Material.Blue, Material.Shade200)
                                                return Material.color(Material.Grey, Material.Shade200)
                                            }

                                            Label {
                                                anchors.centerIn: parent
                                                text: "#" + model.id
                                                font.pixelSize: 11
                                                font.weight: Font.Medium
                                            }
                                        }

                                        Label {
                                            text: model.type || "未知"
                                            font.pixelSize: 13
                                            font.weight: Font.Medium
                                            color: Material.accent
                                        }

                                        Item { Layout.fillWidth: true }

                                        Label {
                                            text: {
                                                if (model.status === "succeeded") return "成功"
                                                if (model.status === "failed") return "失败"
                                                if (model.status === "running") return "运行中"
                                                return "等待中"
                                            }
                                            font.pixelSize: 12
                                            color: {
                                                if (model.status === "succeeded") return Material.color(Material.Green)
                                                if (model.status === "failed") return Material.color(Material.Red)
                                                if (model.status === "running") return Material.color(Material.Blue)
                                                return Material.color(Material.Grey)
                                            }
                                        }
                                    }

                                    Label {
                                        text: model.provider_name || "-"
                                        font.pixelSize: 11
                                        color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.6)
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }

                                    Label {
                                        text: model.model_name || "-"
                                        font.pixelSize: 11
                                        color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.6)
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.taskId = model.id
                                }
                            }
                        }
                    }
                }

                Label {
                    text: "请求参数"
                    font.pixelSize: 16
                    font.weight: Font.Medium
                }

                Control {
                    Layout.fillWidth: true
                    padding: 12

                    background: Rectangle {
                        radius: 8
                        color: "transparent"
                        border.width: 1
                        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                    }

                    contentItem: TextArea {
                        id: requestParamsText
                        readOnly: true
                        wrapMode: TextArea.Wrap
                        font.family: "Consolas"
                        font.pixelSize: 12
                        selectByMouse: true
                        background: null
                        implicitHeight: contentHeight
                    }
                }

                Label {
                    text: "响应数据"
                    font.pixelSize: 16
                    font.weight: Font.Medium
                }

                Control {
                    Layout.fillWidth: true
                    padding: 12

                    background: Rectangle {
                        radius: 8
                        color: "transparent"
                        border.width: 1
                        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                    }

                    contentItem: TextArea {
                        id: responseDataText
                        readOnly: true
                        wrapMode: TextArea.Wrap
                        font.family: "Consolas"
                        font.pixelSize: 12
                        selectByMouse: true
                        background: null
                        implicitHeight: Math.max(contentHeight, 40)
                    }
                }

                Label {
                    text: "错误消息"
                    font.pixelSize: 16
                    font.weight: Font.Medium
                    visible: errorMessageLabel.text !== ""
                }

                Control {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 100
                    padding: 12
                    visible: errorMessageLabel.text !== ""

                    background: Rectangle {
                        radius: 8
                        color: "transparent"
                        border.width: 1
                        border.color: Material.color(Material.Red, Material.Shade200)
                    }

                    contentItem: ScrollView {
                        Label {
                            id: errorMessageLabel
                            width: parent.width
                            wrapMode: Text.Wrap
                            font.family: "Consolas"
                            font.pixelSize: 12
                            color: Material.color(Material.Red)
                        }
                    }
                }
            }
        }
    }
}
