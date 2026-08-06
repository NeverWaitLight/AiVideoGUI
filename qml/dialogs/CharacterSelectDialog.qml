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
    property var onCharactersSelected: null
    property var selectedCharacterIds: []

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

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                spacing: 12

                Label {
                    text: "选择角色生成封面图"
                    font.pixelSize: Theme.fontSizeLarge
                    font.bold: true
                    Layout.fillWidth: true
                }

                Label {
                    text: "已选 " + selectedCharacterIds.length + " 个"
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                    visible: selectedCharacterIds.length > 0
                }
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

                Button {
                    text: "确定"
                    highlighted: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 80
                    enabled: selectedCharacterIds.length > 0
                    onClicked: {
                        if (onCharactersSelected && selectedCharacterIds.length > 0) {
                            var selectedCharacters = []

                            for (var i = 0; i < characterGridView.contentItem.children.length; i++) {
                                var item = characterGridView.contentItem.children[i]
                                if (item && item._characterId !== undefined) {
                                    if (selectedCharacterIds.indexOf(item._characterId) >= 0) {
                                        selectedCharacters.push({
                                            characterId: item._characterId,
                                            name: item._characterName,
                                            description: item._characterDescription,
                                            designImagePath: item._characterDesignImagePath
                                        })
                                    }
                                }
                            }

                            if (selectedCharacters.length > 0) {
                                onCharactersSelected(selectedCharacters)
                            } else {
                                console.warn("无法获取选中的角色数据")
                            }
                        }
                        characterSelectDialog.accept()
                    }
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
                    border.width: _isSelected ? 2 : (cardMouseArea.containsMouse ? 2 : 1)
                    border.color: _isSelected ? Material.accent : (cardMouseArea.containsMouse ? Material.accent : Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12))
                    visible: model.designImagePath && model.designImagePath !== ""

                    property bool _isSelected: selectedCharacterIds.indexOf(model.characterId) >= 0
                    property int _characterId: model.characterId || 0
                    property string _characterName: model.name || ""
                    property string _characterDescription: model.description || ""
                    property string _characterDesignImagePath: model.designImagePath || ""

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

                            Rectangle {
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: 8
                                width: 24
                                height: 24
                                radius: 12
                                color: _isSelected ? Material.accent : Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.2)
                                border.width: _isSelected ? 0 : 2
                                border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.3)
                                visible: cardMouseArea.containsMouse || _isSelected

                                Label {
                                    anchors.centerIn: parent
                                    text: "✓"
                                    font.pixelSize: 16
                                    font.bold: true
                                    color: "white"
                                    visible: _isSelected
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
                            var charId = model.characterId || 0
                            var idx = selectedCharacterIds.indexOf(charId)
                            if (idx >= 0) {
                                var newList = []
                                for (var i = 0; i < selectedCharacterIds.length; i++) {
                                    if (selectedCharacterIds[i] !== charId) {
                                        newList.push(selectedCharacterIds[i])
                                    }
                                }
                                selectedCharacterIds = newList
                            } else {
                                var updatedList = selectedCharacterIds.slice()
                                updatedList.push(charId)
                                selectedCharacterIds = updatedList
                            }
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
        selectedCharacterIds = []
        if (projectId > 0) {
            bridge.characters.load_for_project(projectId)
        }
        characterSelectDialog.visible = true
    }
}
