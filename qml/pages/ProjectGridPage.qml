import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: projectGridPage

    signal projectSelected(int projectId)
    signal createProjectClicked()

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // 固定 3×2 网格布局
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: projectRepeater.count > 0

            ScrollView {
                anchors.fill: parent
                anchors.margins: 20
                clip: true
                contentWidth: availableWidth

                Item {
                    width: parent.parent.width - 40
                    height: gridContainer.height

                    // 网格容器
                    Item {
                        id: gridContainer
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: Math.min(parent.width, 900)
                        height: 280 * 2 + 12  // 2 行 + 行间距

                        property real cardSpacing: 12  // 卡片间距

                        // 项目卡片（最多 6 个）
                        Repeater {
                            id: projectRepeater
                            model: bridge.projects.gridModel
                            delegate: Comp.ProjectCard {
                                x: (index % 3) * ((gridContainer.width + gridContainer.cardSpacing) / 3)
                                y: Math.floor(index / 3) * (280 + gridContainer.cardSpacing)
                                width: (gridContainer.width - gridContainer.cardSpacing * 2) / 3
                                height: 280
                                visible: index < 6

                                projectId: model.projectId
                                projectName: model.name
                                resolution: model.resolution
                                aspectRatio: model.aspectRatio
                                coverPath: model.coverPath
                                createdAt: model.createdAt || ""

                                onClicked: projectGridPage.projectSelected(projectId)
                                onEditClicked: projectDialog.openForEdit(projectId)
                                onDeleteClicked: confirmDialog.confirmDelete("项目", function() {
                                    bridge.projects.delete_project(projectId)
                                })
                            }
                        }
                    }
                }
            }
        }

        Comp.EmptyState {
            visible: projectRepeater.count === 0
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "还没有项目，点击右上角创建"
            buttonText: "新建项目"
            onButtonClicked: projectGridPage.createProjectClicked()
        }
    }

    // 项目对话框
    Dialogs.ProjectDialog {
        id: projectDialog
    }

    // 确认对话框
    Dialogs.ConfirmDialog {
        id: confirmDialog
    }

    // 对外暴露方法
    function openCreateDialog() {
        projectDialog.openForCreate()
    }
}
