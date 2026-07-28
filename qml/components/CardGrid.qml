import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root

    property int columns: 3
    property real sideMargin: 30
    property real cardSpacing: 24
    property real cardHeight: 140
    property real topMargin: 20
    readonly property real cardWidth: Math.max(0, (width - 2 * sideMargin - (columns - 1) * cardSpacing) / columns)

    default property alias cardChildren: flow.data

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth

        Item {
            id: container
            width: root.width
            height: flow.y + flow.height + 20

            Flow {
                id: flow
                x: root.sideMargin
                y: root.topMargin
                width: container.width - 2 * root.sideMargin
                spacing: root.cardSpacing
                flow: Flow.LeftToRight
            }
        }
    }
}
