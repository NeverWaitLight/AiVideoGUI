import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: historyDialog
    modal: true
    title: "历史版本"
    width: 420
    height: 400
    anchors.centerIn: parent

    property var model: null

    signal restoreRequested(int historyId)

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        Label {
            text: "选择一个历史版本进行恢复"
            font.pixelSize: Theme.fontSizeSmall
            color: Theme.textSecondary
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 4
            model: historyDialog.model

            delegate: Pane {
                width: ListView.view.width - 4
                height: 56
                padding: 8

                background: Rectangle {
                    radius: Theme.borderRadius
                    color: parent.hovered ? "#F5F5F5" : "#FFFFFF"
                    border.color: Theme.border
                    border.width: 1
                }

                RowLayout {
                    anchors.fill: parent
                    spacing: 12

                    Label {
                        text: model.createdAt || ""
                        font.pixelSize: Theme.fontSizeSmall
                        color: Theme.textSecondary
                        Layout.preferredWidth: 130
                    }

                    Label {
                        text: model.previewText || ""
                        font.pixelSize: Theme.fontSizeSmall
                        color: Theme.textAI
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Button {
                        text: "恢复"
                        flat: true
                        onClicked: historyDialog.restoreRequested(model.historyId)
                    }
                }
            }

            // 空状态
            Label {
                visible: !historyDialog.model || historyDialog.model.count === 0
                anchors.centerIn: parent
                text: "暂无历史版本"
                color: Theme.textSecondary
                font.pixelSize: Theme.fontSizeSmall
            }
        }
    }
}
