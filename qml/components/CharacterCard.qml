import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as Comp

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


    RowLayout {
        anchors.fill: parent
        spacing: 12

        Comp.ImagePreview {
            width: 72; height: 72; radius: 36
            imageSource: designImage
            placeholderIcon: "qrc:/resources/icons/person.svg"
            placeholderIconSize: 32
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            RowLayout {
                spacing: 8
                Label { text: characterName; font.pixelSize: Theme.fontSizeMedium; font.bold: true }
                Rectangle {
                    width: refLabel.implicitWidth + 12; height: 20; radius: 10
                    Label {
                        id: refLabel
                        anchors.centerIn: parent
                        text: refCode; font.pixelSize: Theme.fontSizeTiny
                    }
                }
            }
            Label {
                text: description
                font.pixelSize: Theme.fontSizeSmall
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
