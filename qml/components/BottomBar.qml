import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Item {
    id: bottomBar
    implicitHeight: Theme.bottomBarHeight

    Rectangle {
        anchors.fill: parent
        color: Material.background

        Label {
            anchors.right: parent.right
            anchors.rightMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            text: "v0.0.1"
            font.pixelSize: Theme.fontSizeTiny
            color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.45)
        }
    }

    // 顶部分割线已移除
}
