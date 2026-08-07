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
            _projectInfo = (info.aspectRatio || "") + " · " + (info.resolution || "")
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Comp.PageHeader {
            projectName: _projectName
            title: ""
            titleSuffix: _projectInfo
            Layout.fillWidth: true
            onBackClicked: detailPage.backClicked()
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
                title: "详情"
                iconSource: "qrc:/resources/icons/info.svg"
                description: "编辑项目信息"
                moduleName: "project_info"
            }
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
                title: "角色"
                iconSource: "qrc:/resources/icons/person.svg"
                description: "管理角色形象"
                moduleName: "character"
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
                title: "素材库"
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
