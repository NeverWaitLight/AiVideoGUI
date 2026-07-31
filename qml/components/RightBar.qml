import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Item {
    id: rightBar
    width: Theme.rightBarWidth

    property alias aiChatVisible: root.aiChatVisible

    QtObject {
        id: root
        property bool aiChatVisible: true
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 4
        anchors.bottomMargin: 4
        anchors.leftMargin: 6
        anchors.rightMargin: 6
        spacing: 10

        RightBarButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            icon.source: "qrc:/resources/icons/chat.svg"
            icon.width: 22
            icon.height: 22
            ToolTip.text: "AI 助手"
            ToolTip.visible: hovered
            checkable: true
            checked: root.aiChatVisible
            isActive: root.aiChatVisible
            onClicked: root.aiChatVisible = !root.aiChatVisible
        }

        Item { Layout.fillHeight: true }

        RightBarButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            icon.source: "qrc:/resources/icons/info.svg"
            icon.width: 22
            icon.height: 22
            ToolTip.text: "关于"
            ToolTip.visible: hovered
        }
    }

    component RightBarButton: Button {
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
