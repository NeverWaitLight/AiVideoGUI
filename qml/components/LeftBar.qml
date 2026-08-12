import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Item {
    id: tabBar
    width: Theme.tabBarWidth

    signal tabChanged(int index)
    signal libraryClicked()
    signal visualStylesClicked()
    signal tasksClicked()
    signal settingsClicked()

    property int currentIndex: 0

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 4
        anchors.bottomMargin: 4
        anchors.leftMargin: 6
        anchors.rightMargin: 6
        spacing: 10

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

        TabButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            icon.source: "qrc:/resources/icons/palette.svg"
            icon.width: 22
            icon.height: 22
            checked: tabBar.currentIndex === 2
            isActive: tabBar.currentIndex === 2
            onClicked: {
                tabBar.currentIndex = 2
                tabBar.visualStylesClicked()
            }
            ToolTip.text: "视觉风格"
            ToolTip.visible: hovered
        }

        Item { Layout.fillHeight: true }

        TabButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            icon.source: "qrc:/resources/icons/history.svg"
            icon.width: 22
            icon.height: 22
            checked: tabBar.currentIndex === 3
            isActive: tabBar.currentIndex === 3
            onClicked: {
                tabBar.currentIndex = 3
                tabBar.tasksClicked()
            }
            ToolTip.text: "任务历史"
            ToolTip.visible: hovered
        }

        TabButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            icon.source: "qrc:/resources/icons/settings.svg"
            icon.width: 22
            icon.height: 22
            checked: tabBar.currentIndex === 4
            isActive: tabBar.currentIndex === 4
            onClicked: {
                tabBar.currentIndex = 4
                tabBar.settingsClicked()
            }
            ToolTip.text: "设置"
            ToolTip.visible: hovered
        }
    }

    component TabButton: Button {
        property bool isActive: false
        flat: true
        display: AbstractButton.IconOnly
        padding: 0
        topPadding: 0
        bottomPadding: 0
        leftPadding: 0
        rightPadding: 0

        background: Rectangle {
            anchors.fill: parent
            radius: 2
            color: parent.isActive
                ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                : parent.hovered
                    ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                    : "transparent"
        }
    }
}
