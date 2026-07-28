import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Pane {
    id: card
    height: 200
    padding: 8

    property string fileName: ""
    property string fileType: ""
    property string thumbnailPath: ""

    signal clicked()
    signal doubleClicked()


    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 130
            radius: Theme.radiusSmall
            clip: true

            Image {
                anchors.fill: parent
                source: thumbnailPath ? "file:///" + thumbnailPath : ""
                fillMode: Image.PreserveAspectCrop
                visible: source !== ""
            }

            // 类型标签
            Rectangle {
                anchors.top: parent.top
                anchors.right: parent.right
                width: typeLabel.implicitWidth + 8
                height: 18
                radius: Theme.radiusSmall
                Label {
                    id: typeLabel
                    anchors.centerIn: parent
                    text: fileType === "video" ? "视频" : (fileType === "image" ? "图片" : "音频")
                    font.pixelSize: Theme.fontSizeTiny
                }
            }
        }

        Label {
            text: fileName
            font.pixelSize: Theme.fontSizeSmall
            elide: Text.ElideRight
            Layout.fillWidth: true
        }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: card.clicked()
        onDoubleClicked: card.doubleClicked()
    }

    property bool isHovered: hoverHandler.hovered
    HoverHandler { id: hoverHandler }
}
