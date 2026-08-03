import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: projectGridPage

    signal projectSelected(int projectId)
    signal createRequested()
    signal editRequested(int projectId)

    property var generatingCoverIds: []

    Connections {
        target: bridge

        function onCover_generation_started(projectId) {
            console.log("封面生成开始：项目 ID =", projectId)
            var ids = projectGridPage.generatingCoverIds.slice()
            if (ids.indexOf(projectId) === -1) {
                ids.push(projectId)
                projectGridPage.generatingCoverIds = ids
            }
        }

        function onCover_generation_finished(projectId) {
            console.log("封面生成完成：项目 ID =", projectId)
            var ids = projectGridPage.generatingCoverIds.slice()
            var index = ids.indexOf(projectId)
            if (index !== -1) {
                ids.splice(index, 1)
                projectGridPage.generatingCoverIds = ids
            }
            bridge.projects.load_projects()
        }

        function onCover_generation_failed(projectId, errorMessage) {
            console.log("封面生成失败：项目 ID =", projectId, "错误：", errorMessage)
            var ids = projectGridPage.generatingCoverIds.slice()
            var index = ids.indexOf(projectId)
            if (index !== -1) {
                ids.splice(index, 1)
                projectGridPage.generatingCoverIds = ids
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

                Label {
                    text: "项目"
                    font.pixelSize: Theme.fontSizeMedium
                    font.bold: true
                }

                Item { Layout.fillWidth: true }

                Button {
                    width: 34
                    height: 34
                    flat: true
                    display: AbstractButton.IconOnly
                    icon.source: "qrc:/resources/icons/add.svg"
                    icon.width: 20
                    icon.height: 20
                    topPadding: 7
                    bottomPadding: 7
                    leftPadding: 7
                    rightPadding: 7
                    ToolTip.visible: hovered
                    ToolTip.text: "新建"
                    onClicked: projectGridPage.createRequested()

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
            visible: projectRepeater.count > 0

            ScrollView {
                anchors.fill: parent
                clip: true
                contentWidth: availableWidth

                Grid {
                    width: parent.width
                    columns: 3
                    rowSpacing: 12
                    columnSpacing: 12
                    padding: 20

                    Repeater {
                        id: projectRepeater
                        model: bridge.projects.gridModel
                        delegate: Comp.ProjectCard {
                            width: (parent.width - parent.padding * 2 - parent.columnSpacing * 2) / 3
                            height: 280

                            projectId: model.projectId
                            projectName: model.name
                            resolution: model.resolution
                            aspectRatio: model.aspectRatio
                            coverPath: model.coverPath
                            createdAt: model.createdAt || ""
                            isGeneratingCover: generatingCoverIds.indexOf(projectId) !== -1

                            onClicked: projectGridPage.projectSelected(projectId)
                            onEditClicked: function(id) {
                                projectGridPage.editRequested(id)
                            }
                            onDeleteClicked: function(id) {
                                confirmDialog.confirmDelete("项目", function() {
                                    bridge.projects.delete_project(id)
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
            buttonText: "新建"
            onButtonClicked: projectGridPage.createRequested()
        }
    }

    Dialogs.ConfirmDialog {
        id: confirmDialog
    }
}
