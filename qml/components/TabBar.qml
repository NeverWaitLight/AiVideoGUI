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

    property int currentIndex: 0

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 6
        spacing: 10

        // 项目管理按钮
        TabButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 40
            Layout.preferredHeight: 40
            icon.source: "qrc:/resources/icons/folder.svg"
            icon.width: 20
            icon.height: 20
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
            Layout.preferredWidth: 40
            Layout.preferredHeight: 40
            icon.source: "qrc:/resources/icons/video_library.svg"
            icon.width: 20
            icon.height: 20
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
            Layout.preferredWidth: 40
            Layout.preferredHeight: 40
            icon.source: "qrc:/resources/icons/settings.svg"
            icon.width: 20
            icon.height: 20
            onClicked: tabBar.settingsClicked()
            ToolTip.text: "设置"
            ToolTip.visible: hovered
        }

        Item { Layout.preferredHeight: 4 }
    }

    // 右侧分割线已移除

    component TabButton: Button {
        property bool isActive: false
        flat: true
        display: AbstractButton.IconOnly
    }
}
