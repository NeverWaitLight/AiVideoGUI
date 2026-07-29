import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp

Item {
    id: detailPage

    property int projectId: -1
    property string _projectName: ""
    property string _projectInfo: ""
    property bool _hasVideos: false

    signal backClicked()
    signal moduleSelected(string moduleName)

    onProjectIdChanged: {
        if (projectId > 0) {
            var info = JSON.parse(bridge.projects.get_project_info(projectId))
            _projectName = info.name || "项目详情"
            _projectInfo = (info.aspectRatio || "") + " · " + (info.resolution || "") + " · " + (info.videoCount || 0) + " 个视频"
            _hasVideos = info.hasStoryboardVideos || false
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Comp.PageHeader {
            title: _projectName
            subtitle: _projectInfo
            Layout.fillWidth: true
            onBackClicked: detailPage.backClicked()
        }

        Comp.CardGrid {
            id: moduleGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            cardHeight: 140

            ModuleCard {
                visible: _hasVideos
                width: moduleGrid.cardWidth
                height: moduleGrid.cardHeight
                title: "播放"; iconSource: "qrc:/resources/icons/play_circle.svg"; description: "播放项目分镜视频"; moduleName: "player"
            }
            ModuleCard {
                width: moduleGrid.cardWidth
                height: moduleGrid.cardHeight
                title: "大纲"; iconSource: "qrc:/resources/icons/article.svg"; description: "编辑故事大纲"; moduleName: "outline"
            }
            ModuleCard {
                width: moduleGrid.cardWidth
                height: moduleGrid.cardHeight
                title: "剧本"; iconSource: "qrc:/resources/icons/description.svg"; description: "编辑剧本场次"; moduleName: "screenplay"
            }
            ModuleCard {
                width: moduleGrid.cardWidth
                height: moduleGrid.cardHeight
                title: "分镜"; iconSource: "qrc:/resources/icons/video_camera_back.svg"; description: "编辑分镜头脚本"; moduleName: "storyboard"
            }
            ModuleCard {
                width: moduleGrid.cardWidth
                height: moduleGrid.cardHeight
                title: "角色"; iconSource: "qrc:/resources/icons/person.svg"; description: "管理角色形象"; moduleName: "character"
            }
            ModuleCard {
                width: moduleGrid.cardWidth
                height: moduleGrid.cardHeight
                title: "素材"; iconSource: "qrc:/resources/icons/video_library.svg"; description: "管理项目素材"; moduleName: "media"
            }
        }
    }

    component ModuleCard: Rectangle {
        property string title: ""
        property string iconSource: ""
        property string description: ""
        property string moduleName: ""

        radius: Theme.cardRadius
        border.width: 1

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
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Label {
                text: description
                font.pixelSize: Theme.fontSizeSmall
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
