import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Pane {
    id: card
    width: 220
    height: 280
    padding: 0

    background: Rectangle {
        radius: Theme.cardRadius
        border.width: 1
    }

    property int projectId: 0
    property string projectName: ""
    property string resolution: ""
    property string aspectRatio: ""
    property string coverPath: ""
    property string createdAt: ""

    signal clicked()
    signal editClicked(int projectId)
    signal deleteClicked(int projectId)


    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        // 封面
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 160
            radius: Theme.radiusMedium
            clip: true

            Image {
                anchors.fill: parent
                source: coverPath ? "file:///" + coverPath : ""
                fillMode: Image.PreserveAspectCrop
                visible: source !== ""
            }

            Image {
                anchors.centerIn: parent
                source: "qrc:/icons/outlined/movie.svg"
                sourceSize.width: 48
                sourceSize.height: 48
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

        // 信息行：分辨率左对齐，时间右对齐
        RowLayout {
            Layout.fillWidth: true
            spacing: 4

            Label {
                text: resolution + " · " + aspectRatio
                font.pixelSize: Theme.fontSizeSmall
                Layout.fillWidth: true
            }

            Label {
                text: createdAt
                font.pixelSize: Theme.fontSizeSmall
                horizontalAlignment: Text.AlignRight
            }
        }

        // 操作按钮：均匀分布
        RowLayout {
            Layout.fillWidth: true
            spacing: 0

            Button {
                Layout.fillWidth: true
                flat: true
                icon.source: "qrc:/icons/outlined/edit.svg"
                icon.width: 20
                icon.height: 20
                onClicked: card.editClicked(card.projectId)
                ToolTip.text: "编辑"
                ToolTip.visible: hovered
            }
            Button {
                Layout.fillWidth: true
                flat: true
                icon.source: "qrc:/icons/outlined/delete.svg"
                icon.width: 20
                icon.height: 20
                onClicked: card.deleteClicked(card.projectId)
                ToolTip.text: "删除"
                ToolTip.visible: hovered
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
