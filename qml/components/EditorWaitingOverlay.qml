import QtQuick 2.15
import QtQuick.Controls.Material 2.15

Item {
    id: overlay
    visible: false
    z: 10

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(Material.background.r, Material.background.g, Material.background.b, 0.45)
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        hoverEnabled: true
        onPressed: function(mouse) { mouse.accepted = true }
    }

    SpinnerOverlay {
        anchors.centerIn: parent
        width: 40
        height: 40
        strokeColor: Material.foreground
        visible: overlay.visible
    }
}
