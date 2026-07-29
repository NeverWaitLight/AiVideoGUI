import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Pane {
    id: sidebar

    signal newConversationClicked()
    signal conversationSelected(string convId)
    signal conversationDeleted(string convId)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        Button {
            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            flat: true
            display: AbstractButton.IconOnly
            icon.source: "qrc:/resources/icons/add.svg"
            icon.width: 22
            icon.height: 22
            padding: 0
            topPadding: 0
            bottomPadding: 0
            leftPadding: 0
            rightPadding: 0
            onClicked: {
                bridge.conversations.create_new()
                sidebar.newConversationClicked()
            }
            ToolTip.text: "新建对话"
            ToolTip.visible: hovered

            background: Rectangle {
                anchors.fill: parent
                radius: 2
                color: parent.hovered
                    ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                    : "transparent"
            }
        }

        ListView {
            id: convList
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: bridge.conversations.model
            clip: true
            spacing: 4

            delegate: ItemDelegate {
                width: convList.width
                height: 44
                text: model.title || "新对话"
                font.pixelSize: Theme.fontSizeNormal
                onClicked: {
                    bridge.conversations.select(model.convId)
                    sidebar.conversationSelected(model.convId)
                }
            }
        }
    }
}
