import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: projectGrid

    signal projectSelected(int projectId)

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Comp.PageHeader {
            title: "项目管理"
            showBack: false
            Layout.fillWidth: true

            Button {
                text: "新建项目"
                highlighted: true
                onClicked: projectDialog.openForCreate()
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            GridView {
                id: grid
                cellWidth: 240
                cellHeight: 300
                model: bridge.projects.gridModel
                delegate: Comp.ProjectCard {
                    width: grid.cellWidth - 20
                    projectId: model.projectId
                    projectName: model.name
                    resolution: model.resolution
                    aspectRatio: model.aspectRatio
                    coverPath: model.coverPath
                    createdAt: model.createdAt || ""
                    onClicked: projectGrid.projectSelected(projectId)
                    onEditClicked: projectDialog.openForEdit(projectId)
                    onDeleteClicked: confirmDialog.confirmDelete("项目", function() {
                        bridge.projects.delete_project(projectId)
                    })
                }

                // 空状态
                Comp.EmptyState {
                    visible: grid.count === 0
                    anchors.centerIn: parent
                    text: "还没有项目，点击右上角创建"
                    buttonText: "新建项目"
                    onButtonClicked: projectDialog.openForCreate()
                }
            }
        }
    }

    // 项目对话框
    Dialogs.ProjectDialog {
        id: projectDialog
    }
}
