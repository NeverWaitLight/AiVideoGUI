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

    background: Rectangle {
        radius: Theme.borderRadius
        color: card.isHovered ? "#F8F8F8" : "#FFFFFF"
        border.color: Theme.border
        border.width: 1
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 130
            radius: 4
            color: "#E8E8E8"
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
                radius: 4
                color: fileType === "video" ? Theme.primary : (fileType === "image" ? Theme.success : Theme.warning)
                Label {
                    id: typeLabel
                    anchors.centerIn: parent
                    text: fileType === "video" ? "视频" : (fileType === "image" ? "图片" : "音频")
                    color: "white"; font.pixelSize: 10
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
