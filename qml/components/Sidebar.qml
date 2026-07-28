import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: sidebar
    color: Theme.bgSidebar

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

            delegate: Rectangle {
                width: convList.width
                height: 52
                radius: Theme.radiusMedium
                color: selected ? Qt.darker(Theme.bgSidebar, 1.1) : (mouseArea.containsMouse ? Qt.darker(Theme.bgSidebar, 1.05) : "transparent")
                property bool selected: false

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 6
                    spacing: 4

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Label {
                            text: model.title
                            font.pixelSize: Theme.fontSizeNormal
                            font.bold: selected
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Label {
                            text: model.timeText
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.textSecondary
                        }
                    }

                    Button {
                        flat: true
                        text: "🗑"
                        font.pixelSize: Theme.fontSizeMedium
                        implicitWidth: 28
                        implicitHeight: 28
                        opacity: mouseArea.containsMouse ? 1 : 0
                        onClicked: confirmDialog.confirmDelete("对话", function() {
                            bridge.conversations.delete(model.convId)
                        })
                    }
                }

                MouseArea {
                    id: mouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        sidebar.conversationSelected(model.convId)
                        bridge.conversations.select(model.convId)
                    }
                }
            }
        }
    }
}
