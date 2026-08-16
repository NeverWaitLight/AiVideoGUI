import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp

Dialog {
    id: videoGenerateDialog
    modal: true
    width: 520
    height: Math.min(contentColumn.implicitHeight + header.implicitHeight + footer.implicitHeight + 24, 580)
    anchors.centerIn: parent
    padding: 0

    property int shotCount: 1
    property bool promptExtendEnabled: true
    property bool useStoryboardDesign: true
    property bool useCharacterDesign: true
    property var onGenerate: null

    title: ""

    ListModel {
        id: storyboardDesignModel
    }

    ListModel {
        id: characterDesignModel
    }

    background: Rectangle {
        color: Material.dialogColor
        radius: Theme.radiusMedium
    }

    header: Item {
        id: header
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
                text: shotCount > 1 ? "批量生成视频" : "生成视频"
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
            }
        }
    }

    footer: Item {
        id: footer
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
                    onClicked: videoGenerateDialog.close()
                }

                Button {
                    text: "生成"
                    highlighted: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 100
                    onClicked: {
                        if (onGenerate)
                            onGenerate(promptExtendEnabled, useStoryboardDesign, useCharacterDesign)
                        videoGenerateDialog.close()
                    }
                }
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        clip: true
        contentWidth: availableWidth

        ColumnLayout {
            id: contentColumn
            width: videoGenerateDialog.availableWidth - 40
            spacing: 16

            Label {
                Layout.fillWidth: true
                text: shotCount > 1
                    ? "将为 " + shotCount + " 个分镜生成视频"
                    : "将为此分镜生成视频"
                font.pixelSize: Theme.fontSizeNormal
                color: Material.foreground
                wrapMode: Text.Wrap
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Label {
                        text: "服务商优化提示词"
                        font.pixelSize: Theme.fontSizeNormal
                        color: Material.foreground
                    }

                    Label {
                        Layout.fillWidth: true
                        text: "由视频服务商对提示词进行智能扩展与优化，提升生成效果"
                        font.pixelSize: Theme.fontSizeSmall
                        color: Material.foreground
                        opacity: 0.7
                        wrapMode: Text.Wrap
                    }
                }

                Switch {
                    id: promptExtendSwitch
                    checked: promptExtendEnabled
                    onCheckedChanged: promptExtendEnabled = checked
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Label {
                        Layout.fillWidth: true
                        text: "引用分镜设计图"
                        font.pixelSize: Theme.fontSizeNormal
                        color: Material.foreground
                    }

                    CheckBox {
                        id: storyboardDesignCheck
                        checked: useStoryboardDesign
                        enabled: storyboardDesignModel.count > 0
                        onCheckedChanged: useStoryboardDesign = checked
                    }
                }

                Label {
                    Layout.fillWidth: true
                    text: "使用当前分镜的设计图作为构图与氛围参考"
                    font.pixelSize: Theme.fontSizeSmall
                    color: Material.foreground
                    opacity: 0.7
                    wrapMode: Text.Wrap
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 12
                    rowSpacing: 12
                    visible: storyboardDesignModel.count > 0

                    Repeater {
                        model: storyboardDesignModel

                        Item {
                            Layout.fillWidth: true
                            Layout.preferredWidth: (contentColumn.width - 12) / 2
                            implicitHeight: thumbColumn.implicitHeight
                            opacity: useStoryboardDesign ? 1.0 : 0.45

                            ColumnLayout {
                                id: thumbColumn
                                anchors.fill: parent
                                spacing: 6

                                Comp.ImagePreview {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: Math.max(72, Math.round(width * 9 / 16))
                                    imageSource: model.imagePath
                                    placeholderIcon: "qrc:/resources/icons/image.svg"
                                    placeholderIconSize: 28
                                }

                                Label {
                                    Layout.fillWidth: true
                                    text: model.label
                                    font.pixelSize: Theme.fontSizeSmall
                                    horizontalAlignment: Text.AlignHCenter
                                    wrapMode: Text.Wrap
                                    maximumLineCount: 2
                                }
                            }
                        }
                    }
                }

                Label {
                    Layout.fillWidth: true
                    visible: storyboardDesignModel.count === 0
                    text: "暂无分镜设计图"
                    font.pixelSize: Theme.fontSizeSmall
                    color: Material.hintTextColor
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Label {
                        Layout.fillWidth: true
                        text: "引用角色设计图"
                        font.pixelSize: Theme.fontSizeNormal
                        color: Material.foreground
                    }

                    CheckBox {
                        id: characterDesignCheck
                        checked: useCharacterDesign
                        enabled: characterDesignModel.count > 0
                        onCheckedChanged: useCharacterDesign = checked
                    }
                }

                Label {
                    Layout.fillWidth: true
                    text: "使用分镜内容中出现的角色设计图作为外观参考"
                    font.pixelSize: Theme.fontSizeSmall
                    color: Material.foreground
                    opacity: 0.7
                    wrapMode: Text.Wrap
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 12
                    rowSpacing: 12
                    visible: characterDesignModel.count > 0

                    Repeater {
                        model: characterDesignModel

                        Item {
                            Layout.fillWidth: true
                            Layout.preferredWidth: (contentColumn.width - 12) / 2
                            implicitHeight: charThumbColumn.implicitHeight
                            opacity: useCharacterDesign ? 1.0 : 0.45

                            ColumnLayout {
                                id: charThumbColumn
                                anchors.fill: parent
                                spacing: 6

                                Comp.ImagePreview {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: Math.max(72, Math.round(width * 9 / 16))
                                    imageSource: model.imagePath
                                    placeholderIcon: "qrc:/resources/icons/person.svg"
                                    placeholderIconSize: 28
                                }

                                Label {
                                    Layout.fillWidth: true
                                    text: model.characterName
                                    font.pixelSize: Theme.fontSizeSmall
                                    horizontalAlignment: Text.AlignHCenter
                                    wrapMode: Text.Wrap
                                    maximumLineCount: 2
                                }
                            }
                        }
                    }
                }

                Label {
                    Layout.fillWidth: true
                    visible: characterDesignModel.count === 0
                    text: "暂无匹配的角色设计图"
                    font.pixelSize: Theme.fontSizeSmall
                    color: Material.hintTextColor
                }
            }
        }
    }

    function _loadPreview(projectId, shotIds) {
        storyboardDesignModel.clear()
        characterDesignModel.clear()

        var previewJson = bridge.storyboard.get_video_generate_preview(
            projectId,
            JSON.stringify(shotIds)
        )
        if (!previewJson)
            return

        var preview = JSON.parse(previewJson)
        var storyboardDesigns = preview.storyboardDesigns || []
        var characterDesigns = preview.characterDesigns || []

        for (var i = 0; i < storyboardDesigns.length; i++)
            storyboardDesignModel.append(storyboardDesigns[i])
        for (var j = 0; j < characterDesigns.length; j++)
            characterDesignModel.append(characterDesigns[j])
    }

    function show(projectId, shotIds, callback) {
        var ids = shotIds || []
        shotCount = ids.length > 0 ? ids.length : 1
        promptExtendEnabled = true
        useStoryboardDesign = true
        useCharacterDesign = true
        promptExtendSwitch.checked = true
        onGenerate = callback

        _loadPreview(projectId, ids)

        useStoryboardDesign = storyboardDesignModel.count > 0
        useCharacterDesign = characterDesignModel.count > 0
        storyboardDesignCheck.checked = useStoryboardDesign
        characterDesignCheck.checked = useCharacterDesign

        open()
    }
}
