import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp

Item {
    id: root

    signal taskClicked(int taskId)

    property int _filterProjectId: -1
    property string _filterCallerType: ""

    Component.onCompleted: {
        loadTasks()
    }

    function loadTasks() {
        var tasks = bridge.tasks.list_tasks_filtered(_filterProjectId, _filterCallerType)
        taskModel.clear()
        for (var i = 0; i < tasks.length; i++) {
            var t = tasks[i]
            taskModel.append({
                id: t.id || 0,
                type: t.type || "",
                provider_task_id: t.provider_task_id || "",
                provider_name: t.provider_name || "",
                model_name: t.model_name || "",
                status: t.status || "",
                completed: t.completed || false,
                request_params: t.request_params || "",
                remote_url: t.remote_url || "",
                local_path: t.local_path || "",
                error_message: t.error_message || "",
                caller_type: t.caller_type || "",
                caller_id: t.caller_id || "",
                project_id: t.project_id !== undefined ? t.project_id : -1,
                parent_ids: t.parent_ids || "",
                created_at: t.created_at || 0,
                updated_at: t.updated_at || 0
            })
        }
    }

    Connections {
        target: bridge
        function onTask_finished() { loadTasks() }
        function onTask_failed() { loadTasks() }
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

                Label {
                    text: "任务历史"
                    font.pixelSize: Theme.fontSizeMedium
                    font.bold: true
                }

                Item { Layout.fillWidth: true }

                ComboBox {
                    id: projectFilterCombo
                    Layout.preferredWidth: 160
                    Layout.preferredHeight: 34

                    model: ListModel { id: projectFilterModel }
                    textRole: "name"
                    displayText: currentIndex >= 0 ? currentText : "全部项目"

                    Component.onCompleted: {
                        projectFilterModel.append({id: -1, name: "全部项目"})
                        var projectsJson = bridge.projects.list_projects_for_filter()
                        var projects = JSON.parse(projectsJson)
                        for (var i = 0; i < projects.length; i++) {
                            projectFilterModel.append(projects[i])
                        }
                        currentIndex = 0
                    }

                    onActivated: {
                        _filterProjectId = projectFilterModel.get(currentIndex).id
                        loadTasks()
                    }

                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: Material.background
                        border.width: 1
                        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g,
                                             Material.foreground.b, 0.12)
                    }
                }

                ComboBox {
                    id: callerTypeFilterCombo
                    Layout.preferredWidth: 140
                    Layout.preferredHeight: 34

                    model: ListModel {
                        ListElement { value: ""; label: "全部类型" }
                        ListElement { value: "cover"; label: "封面" }
                        ListElement { value: "outline"; label: "大纲" }
                        ListElement { value: "script"; label: "剧本" }
                        ListElement { value: "character"; label: "角色" }
                        ListElement { value: "storyboard"; label: "分镜" }
                        ListElement { value: "chat"; label: "聊天" }
                    }
                    textRole: "label"
                    displayText: currentIndex >= 0 ? currentText : "全部类型"

                    Component.onCompleted: {
                        currentIndex = 0
                    }

                    onActivated: {
                        _filterCallerType = model.get(currentIndex).value
                        loadTasks()
                    }

                    background: Rectangle {
                        radius: Theme.radiusSmall
                        color: Material.background
                        border.width: 1
                        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g,
                                             Material.foreground.b, 0.12)
                    }
                }

                Button {
                    visible: _filterProjectId !== -1 || _filterCallerType !== ""
                    Layout.preferredWidth: 34
                    Layout.preferredHeight: 34
                    flat: true
                    display: AbstractButton.IconOnly
                    icon.source: "qrc:/resources/icons/close.svg"
                    icon.width: 16
                    icon.height: 16
                    topPadding: 9
                    bottomPadding: 9
                    leftPadding: 9
                    rightPadding: 9
                    ToolTip.visible: hovered
                    ToolTip.text: "清除过滤"

                    onClicked: {
                        projectFilterCombo.currentIndex = 0
                        callerTypeFilterCombo.currentIndex = 0
                        _filterProjectId = -1
                        _filterCallerType = ""
                        loadTasks()
                    }

                    background: Rectangle {
                        anchors.fill: parent
                        radius: Theme.radiusSmall
                        color: parent.hovered
                            ? Qt.rgba(Material.foreground.r, Material.foreground.g,
                                     Material.foreground.b, 0.08)
                            : "transparent"
                    }
                }

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
                    onClicked: loadTasks()

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

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: taskModel.count > 0

            ScrollView {
                anchors.fill: parent
                clip: true
                contentWidth: availableWidth

                GridView {
                id: gridView
                width: parent.width
                cellWidth: Math.floor(width / Math.max(1, Math.floor(width / 380)))
                cellHeight: 200
                model: ListModel { id: taskModel }

                delegate: Control {
                    width: gridView.cellWidth - 8
                    height: gridView.cellHeight - 8
                    padding: 12

                    background: Rectangle {
                        radius: 8
                        color: Material.background
                        border.width: 1
                        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                    }

                    contentItem: ColumnLayout {
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Rectangle {
                                Layout.preferredWidth: 32
                                Layout.preferredHeight: 32
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
                                    font.pixelSize: 12
                                    font.weight: Font.Medium
                                }
                            }

                            Label {
                                text: model.type || "未知"
                                font.pixelSize: 14
                                font.weight: Font.Medium
                                color: Material.accent
                            }

                            Item { Layout.fillWidth: true }

                            Label {
                                text: {
                                    if (model.status === "succeeded") return "✓ 成功"
                                    if (model.status === "failed") return "✗ 失败"
                                    if (model.status === "running") return "⟳ 运行中"
                                    return "○ 等待中"
                                }
                                font.pixelSize: 13
                                color: {
                                    if (model.status === "succeeded") return Material.color(Material.Green)
                                    if (model.status === "failed") return Material.color(Material.Red)
                                    if (model.status === "running") return Material.color(Material.Blue)
                                    return Material.color(Material.Grey)
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                        }

                        GridLayout {
                            Layout.fillWidth: true
                            columns: 2
                            rowSpacing: 6
                            columnSpacing: 12

                            Label {
                                text: "Provider:"
                                font.pixelSize: 12
                                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.6)
                            }
                            Label {
                                text: model.provider_name || "-"
                                font.pixelSize: 12
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }

                            Label {
                                text: "Model:"
                                font.pixelSize: 12
                                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.6)
                            }
                            Label {
                                text: model.model_name || "-"
                                font.pixelSize: 12
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }

                            Label {
                                text: "入参:"
                                font.pixelSize: 12
                                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.6)
                            }
                            Label {
                                text: {
                                    var params = model.request_params || ""
                                    return params.length > 80 ? params.substring(0, 80) + "..." : params
                                }
                                font.pixelSize: 11
                                font.family: "Consolas"
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                                wrapMode: Text.NoWrap
                            }
                        }

                        Item { Layout.fillHeight: true }

                        Label {
                            text: "创建时间: " + new Date(model.created_at).toLocaleString(Qt.locale(), "yyyy-MM-dd hh:mm:ss")
                            font.pixelSize: 11
                            color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.5)
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.taskClicked(model.id)
                    }
                }
            }
        }
        }

        Comp.EmptyState {
            visible: taskModel.count === 0
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "暂无任务记录"
        }
    }
}
