import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: visualStyleListPage

    signal styleSelected(int styleId)
    signal backClicked()

    Component.onCompleted: {
        bridge.visualStyles.load_styles()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Pane {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            padding: 5

            background: Rectangle {
                color: "transparent"
                border.width: 0
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 1
                    color: "white"
                }
            }

            RowLayout {
                anchors.fill: parent
                spacing: 12

                Button {
                    width: 34
                    height: 34
                    flat: true
                    display: AbstractButton.IconOnly
                    icon.source: "qrc:/resources/icons/arrow_back.svg"
                    icon.width: 20
                    icon.height: 20
                    topPadding: 7
                    bottomPadding: 7
                    leftPadding: 7
                    rightPadding: 7
                    ToolTip.visible: hovered
                    ToolTip.text: "返回"
                    onClicked: visualStyleListPage.backClicked()

                    background: Rectangle {
                        anchors.fill: parent
                        radius: Theme.radiusSmall
                        color: parent.hovered
                            ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                            : "transparent"
                    }
                }

                Label {
                    text: "视觉风格"
                    font.pixelSize: Theme.fontSizeMedium
                    font.bold: true
                }

                Item { Layout.fillWidth: true }

                Button {
                    width: 34
                    height: 34
                    flat: true
                    display: AbstractButton.IconOnly
                    icon.source: "qrc:/resources/icons/add.svg"
                    icon.width: 20
                    icon.height: 20
                    topPadding: 7
                    bottomPadding: 7
                    leftPadding: 7
                    rightPadding: 7
                    ToolTip.visible: hovered
                    ToolTip.text: "新建"
                    onClicked: editDialog.open(-1, "", "")

                    background: Rectangle {
                        anchors.fill: parent
                        radius: Theme.radiusSmall
                        color: parent.hovered
                            ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                            : "transparent"
                    }
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: styleRepeater.count > 1

            ScrollView {
                anchors.fill: parent
                clip: true
                contentWidth: availableWidth

                Grid {
                    width: parent.width
                    columns: 4
                    rowSpacing: 12
                    columnSpacing: 12
                    padding: 20

                    Repeater {
                        id: styleRepeater
                        model: bridge.visualStyles.listModel
                        delegate: Comp.VisualStyleCard {
                            width: (parent.width - parent.padding * 2 - parent.columnSpacing * 3) / 4
                            height: 300
                            visible: model.styleId !== -1

                            styleId: model.styleId
                            styleName: model.name
                            isDefault: model.isDefault
                            sampleImagePath: model.sampleImagePath
                            createdAt: model.createdAt || ""

                            onClicked: visualStyleListPage.styleSelected(styleId)
                            onEditClicked: function(id) {
                                editDialog.open(id, styleName, sampleImagePath)
                            }
                            onDeleteClicked: function(id) {
                                confirmDialog.confirmDelete("风格", function() {
                                    bridge.visualStyles.delete_style(id)
                                })
                            }
                            onSetDefaultClicked: function(id) {
                                bridge.visualStyles.set_as_default(id)
                            }
                        }
                    }
                }
            }
        }

        Comp.EmptyState {
            visible: styleRepeater.count <= 1
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "还没有视觉风格，点击右上角创建"
            buttonText: "新建"
            onButtonClicked: editDialog.open(-1, "", "")
        }
    }

    Dialogs.ConfirmDialog {
        id: confirmDialog
    }

    Dialogs.VisualStyleEditDialog {
        id: editDialog
    }
}
