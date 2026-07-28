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

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: 20
                anchors.margins: 30

                GridLayout {
                    columns: 3
                    columnSpacing: 20
                    rowSpacing: 20
                    Layout.fillWidth: true

                    ModuleCard {
                        visible: _hasVideos
                        title: "播放"; icon: "▶️"; description: "播放项目分镜视频"; moduleName: "player"
                    }
                    ModuleCard { title: "大纲"; icon: "📝"; description: "编辑故事大纲"; moduleName: "outline" }
                    ModuleCard { title: "剧本"; icon: "📋"; description: "编辑剧本场次"; moduleName: "screenplay" }
                    ModuleCard { title: "分镜"; icon: "🎬"; description: "编辑分镜头脚本"; moduleName: "storyboard" }
                    ModuleCard { title: "角色"; icon: "👤"; description: "管理角色形象"; moduleName: "character" }
                    ModuleCard { title: "素材"; icon: "📂"; description: "管理项目素材"; moduleName: "media" }
                }
            }
        }
    }

    component ModuleCard: Pane {
        property string title: ""
        property string icon: ""
        property string description: ""
        property string moduleName: ""

        Layout.preferredWidth: 200
        Layout.preferredHeight: 160
        padding: 16

        background: Rectangle {
            radius: Theme.cardRadius
            color: cardMouse.containsMouse ? "#F8F8F8" : "#FFFFFF"
            border.color: Theme.border
            border.width: 1
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 12

            Label {
                text: icon
                font.pixelSize: 36
                Layout.alignment: Qt.AlignHCenter
            }

            Label {
                text: title
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                Layout.alignment: Qt.AlignHCenter
            }

            Label {
                text: description
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.textSecondary
                wrapMode: Text.Wrap
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
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
