import QtQuick 2.15
import QtQuick.Controls 2.15
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
        anchors.margins: 8
        spacing: 12

        // 直接生成按钮
        TabButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 44
            Layout.preferredHeight: 44
            text: "💬"
            checked: tabBar.currentIndex === 0
            isActive: tabBar.currentIndex === 0
            onClicked: {
                tabBar.currentIndex = 0
                tabBar.tabChanged(0)
            }
            ToolTip.text: "直接生成"
            ToolTip.visible: hovered
        }

        // 项目管理按钮
        TabButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 44
            Layout.preferredHeight: 44
            text: "📁"
            checked: tabBar.currentIndex === 1
            isActive: tabBar.currentIndex === 1
            onClicked: {
                tabBar.currentIndex = 1
                tabBar.tabChanged(1)
            }
            ToolTip.text: "项目管理"
            ToolTip.visible: hovered
        }

        Item { Layout.fillHeight: true }

        // 素材库按钮
        TabButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 44
            Layout.preferredHeight: 44
            text: "🎬"
            onClicked: tabBar.libraryClicked()
            ToolTip.text: "素材库"
            ToolTip.visible: hovered
        }

        // 设置按钮
        TabButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 44
            Layout.preferredHeight: 44
            text: "⚙️"
            onClicked: tabBar.settingsClicked()
            ToolTip.text: "设置"
            ToolTip.visible: hovered
        }

        Item { Layout.preferredHeight: 8 }
    }

    component TabButton: Button {
        property bool isActive: false
        flat: true
        font.pixelSize: 20
    }
}
