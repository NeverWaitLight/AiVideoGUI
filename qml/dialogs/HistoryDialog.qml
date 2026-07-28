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
    padding: 0

    property var model: null

    signal restoreRequested(int historyId)

    background: Rectangle {
        color: Theme.bgChat
        radius: Theme.cardRadius
        border.color: Theme.border
        border.width: 1
    }

    header: Rectangle {
        height: Theme.headerHeight
        color: Theme.bgSidebar
        border.color: Theme.border
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Label {
                text: "历史版本"
                font.pixelSize: Theme.fontSizeTitle
                font.bold: true
                color: Theme.textAI
                Layout.fillWidth: true
            }
        }
    }

    footer: Rectangle {
        height: 48
        color: Theme.bgSidebar
        border.color: Theme.border
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 12

            Label {
                text: "选择一个历史版本进行恢复"
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.textSecondary
                Layout.fillWidth: true
            }

            Button {
                text: "关闭"
                implicitHeight: 28
                implicitWidth: 64
                background: Rectangle {
                    radius: Theme.borderRadius
                    color: parent.hovered ? Theme.bubbleAI : Theme.bgChat
                    border.color: Theme.border
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: Theme.fontSizeSmall
                    color: Theme.textAI
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: historyDialog.reject()
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 4

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 4
            model: historyDialog.model

            delegate: Pane {
                width: ListView.view.width
                height: 56
                padding: 8

                background: Rectangle {
                    radius: Theme.borderRadius
                    color: parent.hovered ? Theme.bgSidebar : Theme.bgChat
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
                        implicitHeight: 28
                        background: Rectangle {
                            radius: Theme.borderRadius
                            color: parent.hovered ? Theme.primaryHover : Theme.primary
                        }
                        contentItem: Text {
                            text: parent.text
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.textUser
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
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
