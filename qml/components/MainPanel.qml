import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import "../pages" as Pages

// 主内容面板 - 中间主页面区域（项目管理/素材库）
Control {
    id: mainPanel
    padding: 0

    property string currentPage: "project"

    background: Rectangle {
        color: "transparent"
    }

    contentItem: ColumnLayout {
        spacing: 0

        // 标题栏
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

            contentItem: RowLayout {
                spacing: 0

                // 左侧容器 - 显示标题
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    Label {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        text: mainPanel.currentPage === "project" ? "项目" : "素材库"
                        font.pixelSize: Theme.fontSizeMedium
                        font.bold: true
                    }
                }

                // 右侧容器 - 操作按钮区
                Item {
                    Layout.preferredWidth: 76  // 扩展宽度以容纳两个按钮
                    Layout.fillHeight: true

                    RowLayout {
                        anchors.fill: parent
                        spacing: 4

                        // 生成封面按钮
                        Button {
                            visible: mainPanel.currentPage === "project"
                            Layout.preferredWidth: 34
                            Layout.preferredHeight: 34
                            flat: true
                            display: AbstractButton.IconOnly
                            icon.source: "qrc:/resources/icons/image.svg"
                            icon.width: 20
                            icon.height: 20
                            padding: 0
                            ToolTip.visible: hovered
                            ToolTip.text: "生成项目封面"
                            onClicked: {
                                console.log("触发封面生成任务")
                                bridge.trigger_project_cover_generation()
                            }

                            background: Rectangle {
                                anchors.fill: parent
                                radius: Theme.radiusSmall
                                color: parent.hovered
                                    ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                                    : "transparent"
                            }
                        }

                        // 新建项目按钮
                        Button {
                            visible: mainPanel.currentPage === "project"
                            Layout.preferredWidth: 34
                            Layout.preferredHeight: 34
                            flat: true
                            display: AbstractButton.IconOnly
                            icon.source: "qrc:/resources/icons/add.svg"
                            icon.width: 20
                            icon.height: 20
                            padding: 0
                            ToolTip.visible: hovered
                            ToolTip.text: "新建项目"
                            onClicked: projectModePage.openCreateDialog()

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
            }
        }

        // 页面内容
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: mainPanel.currentPage === "project" ? 0 : 1

            Pages.ProjectModePage {
                id: projectModePage
            }

            Pages.MediaLibraryPage {
                id: globalMediaPage
                onBackClicked: {
                    mainPanel.currentPage = "project"
                }
            }
        }
    }

    // 暴露内部页面引用，供外部访问
    readonly property alias projectModePage: projectModePage
    readonly property alias mediaLibraryPage: globalMediaPage
}
