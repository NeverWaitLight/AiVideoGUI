import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Pane {
    id: card
    height: 100
    padding: 10

    property string characterUuid: ""
    property string characterName: ""
    property string refCode: ""
    property string description: ""
    property string designImage: ""

    signal clicked()

    background: Rectangle {
        radius: Theme.borderRadius
        color: card.isHovered ? "#FAFAFA" : "#FFFFFF"
        border.color: Theme.border
        border.width: 1
    }

    RowLayout {
        anchors.fill: parent
        spacing: 12

        Rectangle {
            width: 72; height: 72; radius: 36
            color: "#E8E8E8"
            clip: true
            Image {
                anchors.fill: parent
                source: designImage ? "file:///" + designImage : ""
                fillMode: Image.PreserveAspectCrop
                visible: source !== ""
            }
            Label {
                anchors.centerIn: parent
                text: "👤"
                font.pixelSize: 24
                visible: !designImage
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            RowLayout {
                spacing: 8
                Label { text: characterName; font.pixelSize: Theme.fontSizeMedium; font.bold: true }
                Rectangle {
                    width: refLabel.implicitWidth + 12; height: 20; radius: 10
                    color: Theme.primary
                    Label {
                        id: refLabel
                        anchors.centerIn: parent
                        text: refCode; color: "white"; font.pixelSize: 10
                    }
                }
            }
            Label {
                text: description
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.textSecondary
                elide: Text.ElideRight
                maximumLineCount: 2
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: card.clicked()
    }

    property bool isHovered: hoverHandler.hovered
    HoverHandler { id: hoverHandler }
}
