import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Pane {
    id: sidebar

    signal newConversationClicked()
    signal conversationSelected(string convId)
    signal conversationDeleted(string convId)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        Button {
            text: "+ 新建对话"
            Layout.fillWidth: true
            highlighted: true
            onClicked: {
                bridge.conversations.create_new()
                sidebar.newConversationClicked()
            }
        }

        ListView {
            id: convList
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: bridge.conversations.model
            clip: true
            spacing: 2

            delegate: ItemDelegate {
                width: convList.width
                text: model.title || "新对话"
                onClicked: {
                    bridge.conversations.select(model.convId)
                    sidebar.conversationSelected(model.convId)
                }
            }
        }
    }
}
