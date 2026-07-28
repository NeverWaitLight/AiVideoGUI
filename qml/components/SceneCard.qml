import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Pane {
    id: card
    height: 80
    padding: 12

    property int sceneNumber: 0
    property string location: ""
    property string timeType: ""

    signal clicked()


    RowLayout {
        anchors.fill: parent
        spacing: 12

        Rectangle {
            width: 36; height: 36; radius: 18
            Label {
                anchors.centerIn: parent
                text: sceneNumber
                font.bold: true; font.pixelSize: Theme.fontSizeMedium
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Label { text: "第" + sceneNumber + "场"; font.pixelSize: Theme.fontSizeMedium; font.bold: true }
            Label { text: location; font.pixelSize: Theme.fontSizeSmall; elide: Text.ElideRight; Layout.fillWidth: true }
        }

        Label {
            text: timeType
            font.pixelSize: Theme.fontSizeSmall
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
