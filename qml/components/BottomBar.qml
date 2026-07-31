import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Item {
    id: bottomBar
    implicitHeight: Theme.bottomBarHeight

    Timer {
        interval: 2000
        running: true
        repeat: true
        onTriggered: {
            cpuUsage.text = "CPU: " + (Math.random() * 30 + 10).toFixed(1) + "%"
            memoryUsage.text = "RAM: " + (Math.random() * 20 + 40).toFixed(1) + "%"
            gpuUsage.text = "GPU: " + (Math.random() * 40 + 20).toFixed(1) + "%"
            cpuTemp.text = "CPU Temp: " + (Math.random() * 10 + 45).toFixed(0) + "°C"
        }
    }

    Rectangle {
        anchors.fill: parent
        color: Material.background

        RowLayout {
            anchors.left: parent.left
            anchors.leftMargin: 18
            anchors.verticalCenter: parent.verticalCenter
            spacing: 16

            Label {
                id: cpuUsage
                text: "CPU: 15.2%"
                font.pixelSize: Theme.fontSizeSmall
                color: Qt.rgba(0.6, 0.6, 0.6, 1.0)
            }

            Label {
                id: memoryUsage
                text: "RAM: 52.8%"
                font.pixelSize: Theme.fontSizeSmall
                color: Qt.rgba(0.6, 0.6, 0.6, 1.0)
            }

            Label {
                id: gpuUsage
                text: "GPU: 28.5%"
                font.pixelSize: Theme.fontSizeSmall
                color: Qt.rgba(0.6, 0.6, 0.6, 1.0)
            }
        }

        RowLayout {
            anchors.right: parent.right
            anchors.rightMargin: 18
            anchors.verticalCenter: parent.verticalCenter
            spacing: 12

            Label {
                id: cpuTemp
                text: "CPU Temp: 48°C"
                font.pixelSize: Theme.fontSizeSmall
                color: Qt.rgba(0.6, 0.6, 0.6, 1.0)
            }

            Label {
                text: "Windows 10 Pro"
                font.pixelSize: Theme.fontSizeSmall
                color: Qt.rgba(0.6, 0.6, 0.6, 1.0)
            }

            Label {
                text: "v0.0.1"
                font.pixelSize: Theme.fontSizeSmall
                color: Qt.rgba(0.6, 0.6, 0.6, 1.0)
            }
        }
    }
}
