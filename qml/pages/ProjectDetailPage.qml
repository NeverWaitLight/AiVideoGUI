import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import "../components" as Comp

Item {
    id: detailPage

    property int projectId: -1
    property string _projectName: ""
    property string _projectInfo: ""

    signal backClicked()
    signal moduleSelected(string moduleName)

    onProjectIdChanged: {
        if (projectId > 0) {
            var info = JSON.parse(bridge.projects.get_project_info(projectId))
            _projectName = info.name || "项目详情"
            _projectInfo = (info.aspectRatio || "") + " · " + (info.resolution || "") + " · " + (info.videoCount || 0) + " 个视频"
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
                    Layout.preferredWidth: 34
                    Layout.preferredHeight: 34
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
                    onClicked: detailPage.backClicked()

                    background: Rectangle {
                        anchors.fill: parent
                        radius: Theme.radiusSmall
                        color: parent.hovered
                            ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                            : "transparent"
                    }
                }

                ColumnLayout {
                    spacing: 2

                    Label {
                        text: _projectName
                        font.pixelSize: Theme.fontSizeMedium
                        font.bold: true
                    }

                    Label {
                        text: _projectInfo
                        font.pixelSize: Theme.fontSizeSmall
                        opacity: 0.7
                    }
                }

                Item { Layout.fillWidth: true }
            }
        }

        Grid {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 20
            columns: 3
            rowSpacing: 12
            columnSpacing: 12

            property real cardWidth: (width - columnSpacing * 2) / 3
            property real cardHeight: (height - rowSpacing) / 2

            ModuleCard {
                width: parent.cardWidth
                height: parent.cardHeight
                title: "大纲"
                iconSource: "qrc:/resources/icons/article.svg"
                description: "编辑故事大纲"
                moduleName: "outline"
            }
            ModuleCard {
                width: parent.cardWidth
                height: parent.cardHeight
                title: "剧本"
                iconSource: "qrc:/resources/icons/description.svg"
                description: "编辑剧本场次"
                moduleName: "screenplay"
            }
            ModuleCard {
                width: parent.cardWidth
                height: parent.cardHeight
                title: "分镜"
                iconSource: "qrc:/resources/icons/video_camera_back.svg"
                description: "编辑分镜头脚本"
                moduleName: "storyboard"
            }
            ModuleCard {
                width: parent.cardWidth
                height: parent.cardHeight
                title: "角色"
                iconSource: "qrc:/resources/icons/person.svg"
                description: "管理角色形象"
                moduleName: "character"
            }
            ModuleCard {
                width: parent.cardWidth
                height: parent.cardHeight
                title: "粗剪"
                iconSource: "qrc:/resources/icons/play_circle.svg"
                description: "播放项目分镜视频"
                moduleName: "player"
            }
            ModuleCard {
                width: parent.cardWidth
                height: parent.cardHeight
                title: "素材"
                iconSource: "qrc:/resources/icons/video_library.svg"
                description: "管理项目素材"
                moduleName: "media"
            }
        }
    }

    component ModuleCard: Rectangle {
        property string title: ""
        property string iconSource: ""
        property string description: ""
        property string moduleName: ""

        radius: Theme.cardRadius
        color: Qt.rgba(0, 0, 0, 0.08)
        border.width: 0

        Column {
            anchors.centerIn: parent
            spacing: 8

            Image {
                source: iconSource
                sourceSize.width: 40
                sourceSize.height: 40
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Label {
                text: title
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                wrapMode: Text.Wrap
                maximumLineCount: 2
                horizontalAlignment: Text.AlignHCenter
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Label {
                text: description
                font.pixelSize: Theme.fontSizeSmall
                wrapMode: Text.Wrap
                maximumLineCount: 2
                horizontalAlignment: Text.AlignHCenter
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }

        MouseArea {
            id: cardMouse
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true
            onClicked: detailPage.moduleSelected(moduleName)
        }
    }
}
