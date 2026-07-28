import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Pane {
    id: card
    width: 220
    height: 280
    padding: 0

    property int projectId: 0
    property string projectName: ""
    property string resolution: ""
    property string aspectRatio: ""
    property string coverPath: ""
    property string createdAt: ""

    signal clicked()
    signal editClicked(int projectId)
    signal deleteClicked(int projectId)

    background: Rectangle {
        radius: Theme.cardRadius
        color: card.isHovered ? "#F8F8F8" : "#FFFFFF"
        border.color: Theme.border
        border.width: 1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        // 封面
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 160
            radius: 6
            color: "#E8E8E8"
            clip: true

            Image {
                anchors.fill: parent
                source: coverPath ? "file:///" + coverPath : ""
                fillMode: Image.PreserveAspectCrop
                visible: source !== ""
            }

            Label {
                anchors.centerIn: parent
                text: "🎬"
                font.pixelSize: 36
                visible: !coverPath
            }
        }

        // 项目名
        Label {
            text: projectName
            font.pixelSize: Theme.fontSizeMedium
            font.bold: true
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        // 信息
        Label {
            text: resolution + " · " + aspectRatio
            font.pixelSize: Theme.fontSizeSmall
            color: Theme.textSecondary
        }

        // 创建时间
        Label {
            text: createdAt
            font.pixelSize: 11
            color: "#999"
        }

        // 操作按钮
        RowLayout {
            spacing: 4
            Button {
                flat: true; text: "✏️"; font.pixelSize: 14
                onClicked: card.editClicked(card.projectId)
            }
            Button {
                flat: true; text: "🗑"; font.pixelSize: 14
                onClicked: card.deleteClicked(card.projectId)
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        z: -1
        onClicked: card.clicked()
    }

    property bool isHovered: hoverHandler.hovered
    HoverHandler { id: hoverHandler }
}
