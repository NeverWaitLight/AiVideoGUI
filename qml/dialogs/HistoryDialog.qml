import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: historyDialog
    modal: true
    width: 520
    anchors.centerIn: parent
    padding: 0

    property var model: null

    signal restoreRequested(int historyId)

    title: ""

    background: Rectangle {
        color: Material.dialogColor
        radius: Theme.radiusMedium
    }

    header: Item {
        implicitHeight: 56

        Rectangle {
            anchors.fill: parent
            color: "transparent"

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
            }

            Label {
                anchors.left: parent.left
                anchors.leftMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                text: "历史版本"
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
            }
        }
    }

    footer: Item {
        implicitHeight: 64

        Rectangle {
            anchors.fill: parent
            color: "transparent"

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                spacing: 12

                Label {
                    text: "选择一个历史版本进行恢复"
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                    Layout.fillWidth: true
                }

                Button {
                    text: "关闭"
                    flat: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 80
                    onClicked: historyDialog.reject()
                }
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        anchors.leftMargin: 18
        anchors.rightMargin: 18
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        contentWidth: availableWidth
        clip: true

        ColumnLayout {
            width: parent.parent.width - 36
            spacing: 8

            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 8
                model: historyDialog.model

                delegate: Pane {
                    width: ListView.view.width
                    padding: 12

                    background: Rectangle {
                        color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.05)
                        radius: Theme.radiusSmall
                        border.width: 1
                        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                    }

                    RowLayout {
                        anchors.fill: parent
                        spacing: 12

                        ColumnLayout {
                            spacing: 4
                            Layout.fillWidth: true

                            Label {
                                text: model.createdAt || ""
                                font.pixelSize: Theme.fontSizeSmall
                                font.bold: true
                            }

                            Label {
                                text: model.previewText || ""
                                font.pixelSize: Theme.fontSizeSmall
                                opacity: 0.7
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }

                        Button {
                            text: "恢复"
                            highlighted: true
                            implicitHeight: 32
                            implicitWidth: 64
                            onClicked: historyDialog.restoreRequested(model.historyId)
                        }
                    }
                }
            }

            Label {
                visible: !historyDialog.model || historyDialog.model.count === 0
                Layout.alignment: Qt.AlignCenter
                Layout.topMargin: 60
                text: "暂无历史版本"
                font.pixelSize: Theme.fontSizeNormal
                opacity: 0.5
            }
        }
    }
}
