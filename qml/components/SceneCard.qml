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

    background: Rectangle {
        radius: Theme.borderRadius
        color: card.isHovered ? "#F0F5FF" : "#FFFFFF"
        border.color: Theme.border
        border.width: 1
    }

    RowLayout {
        anchors.fill: parent
        spacing: 12

        Rectangle {
            width: 36; height: 36; radius: 18
            color: Theme.primary
            Label {
                anchors.centerIn: parent
                text: sceneNumber
                color: "white"; font.bold: true; font.pixelSize: 14
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Label { text: "第" + sceneNumber + "场"; font.pixelSize: Theme.fontSizeMedium; font.bold: true }
            Label { text: location; font.pixelSize: Theme.fontSizeSmall; color: Theme.textSecondary; elide: Text.ElideRight; Layout.fillWidth: true }
        }

        Label {
            text: timeType
            font.pixelSize: Theme.fontSizeSmall
            color: Theme.textSecondary
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
