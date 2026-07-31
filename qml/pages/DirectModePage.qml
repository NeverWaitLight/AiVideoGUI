import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp

Item {
    id: directMode

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal

        handle: Rectangle {
            implicitWidth: 1
        }

        Comp.Sidebar {
            id: sidebar
            SplitView.preferredWidth: Theme.sidebarWidth
            SplitView.minimumWidth: 200
            SplitView.maximumWidth: 360
        }

        Comp.ChatArea {
            id: chatArea
            SplitView.fillWidth: true
        }
    }
}
