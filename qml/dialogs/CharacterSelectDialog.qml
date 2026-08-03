import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects
import "../components" as Comp

Dialog {
    id: characterSelectDialog
    modal: true
    width: 560
    height: 480
    anchors.centerIn: parent
    padding: 0

    property int projectId: 0
    property var onCharacterSelected: null

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
                text: "选择角色生成封面图"
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
                anchors.right: parent.right
                anchors.rightMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                spacing: 12

                Button {
                    text: "取消"
                    flat: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 80
                    onClicked: characterSelectDialog.reject()
                }
            }
        }
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: characterGridView.count === 0 ? 1 : 0

        ScrollView {
            contentWidth: availableWidth
            clip: true

            GridView {
                id: characterGridView
                width: parent.width
                cellWidth: (width - 40) / 2
                cellHeight: 220
                leftMargin: 20
                rightMargin: 20
                topMargin: 12
                bottomMargin: 12
                model: bridge.characters.model

                delegate: Rectangle {
                    width: characterGridView.cellWidth - 12
                    height: 200
                    radius: Theme.radiusMedium
                    color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.05)
                    border.width: cardMouseArea.containsMouse ? 2 : 1
                    border.color: cardMouseArea.containsMouse ? Material.accent : Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                    visible: model.designImagePath && model.designImagePath !== ""

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 120
                            radius: Theme.radiusSmall
                            color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.03)

                            Image {
                                anchors.fill: parent
                                anchors.margins: 2
                                source: model.designImagePath ? "file:///" + model.designImagePath : ""
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true

                                layer.enabled: true
                                layer.effect: OpacityMask {
                                    maskSource: Rectangle {
                                        width: 200
                                        height: 120
                                        radius: Theme.radiusSmall
                                    }
                                }
                            }
                        }

                        Label {
                            text: model.name || ""
                            font.pixelSize: Theme.fontSizeMedium
                            font.bold: true
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }

                        Label {
                            text: model.refCode ? "代号: " + model.refCode : ""
                            font.pixelSize: Theme.fontSizeSmall
                            opacity: 0.7
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            visible: model.refCode !== ""
                        }
                    }

                    MouseArea {
                        id: cardMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (onCharacterSelected) {
                                onCharacterSelected(
                                    model.characterId || 0,
                                    model.name || "",
                                    model.description || "",
                                    model.designImagePath || ""
                                )
                            }
                            characterSelectDialog.accept()
                        }
                    }
                }
            }
        }

        Item {
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 16

                Label {
                    text: "还没有角色"
                    font.pixelSize: Theme.fontSizeLarge
                    font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                    opacity: 0.7
                }

                Label {
                    text: "请先在角色管理页面创建角色并生成设计图"
                    font.pixelSize: Theme.fontSizeMedium
                    Layout.alignment: Qt.AlignHCenter
                    opacity: 0.5
                }

                Button {
                    text: "前往创建角色"
                    highlighted: true
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredHeight: 40
                    onClicked: {
                        characterSelectDialog.reject()
                    }
                }
            }
        }
    }

    function open() {
        if (projectId > 0) {
            bridge.characters.load_for_project(projectId)
        }
        characterSelectDialog.visible = true
    }
}
