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
        anchors.margins: 12
        spacing: 12

        Button {
            text: "新建对话"
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            highlighted: true
            font.pixelSize: Theme.fontSizeMedium
            icon.source: "qrc:/resources/icons/filled/add.svg"
            icon.width: 18
            icon.height: 18
            display: AbstractButton.TextBesideIcon
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
