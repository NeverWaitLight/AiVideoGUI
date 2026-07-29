import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Item {
    id: tabBar
    width: Theme.tabBarWidth

    signal tabChanged(int index)
    signal libraryClicked()
    signal settingsClicked()

    // 由 main.qml 根据 root.currentPage 响应式设置，不再独立维护
    property int currentIndex: 0

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 6
        spacing: 10

        // 项目管理按钮
        TabButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            icon.source: "qrc:/resources/icons/folder.svg"
            icon.width: 22
            icon.height: 22
            checked: tabBar.currentIndex === 0
            isActive: tabBar.currentIndex === 0
            onClicked: {
                tabBar.currentIndex = 0
                tabBar.tabChanged(0)
            }
            ToolTip.text: "项目管理"
            ToolTip.visible: hovered
        }

        // 素材库按钮
        TabButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            icon.source: "qrc:/resources/icons/video_library.svg"
            icon.width: 22
            icon.height: 22
            checked: tabBar.currentIndex === 1
            isActive: tabBar.currentIndex === 1
            onClicked: {
                tabBar.currentIndex = 1
                tabBar.libraryClicked()
            }
            ToolTip.text: "素材库"
            ToolTip.visible: hovered
        }

        Item { Layout.fillHeight: true }

        // 设置按钮
        TabButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            icon.source: "qrc:/resources/icons/settings.svg"
            icon.width: 22
            icon.height: 22
            onClicked: tabBar.settingsClicked()
            ToolTip.text: "设置"
            ToolTip.visible: hovered
        }

        Item { Layout.preferredHeight: 4 }
    }

    component TabButton: Button {
        property bool isActive: false
        flat: true
        display: AbstractButton.IconOnly

        background: Rectangle {
            radius: 2
            color: parent.isActive
                ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                : parent.hovered
                    ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                    : "transparent"
        }
    }
}
