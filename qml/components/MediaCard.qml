import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as Comp

Pane {
    id: card
    height: 200
    padding: 8

    property string fileName: ""
    property string fileType: ""
    property string thumbnailPath: ""

    signal clicked()
    signal doubleClicked()
    signal playRequested()


    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        Comp.ImagePreview {
            Layout.fillWidth: true
            Layout.preferredHeight: 130
            radius: Theme.radiusSmall
            imageSource: thumbnailPath

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

            Image {
                anchors.centerIn: parent
                source: "qrc:/resources/icons/play-circle.svg"
                sourceSize.width: 64
                sourceSize.height: 64
                opacity: 0.6
                visible: fileType === "video"
            }

            MouseArea {
                anchors.centerIn: parent
                width: parent.width * 0.8
                height: parent.height * 0.8
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (fileType === "video") {
                        card.playRequested()
                    }
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
