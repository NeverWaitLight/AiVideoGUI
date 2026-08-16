import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: videoGenerateDialog
    modal: true
    width: 480
    height: Math.min(contentColumn.implicitHeight + header.implicitHeight + footer.implicitHeight + 24, 420)
    anchors.centerIn: parent
    padding: 0

    property int shotCount: 1
    property bool promptExtendEnabled: true
    property bool useStoryboardDesign: true
    property bool useCharacterDesign: true
    property bool hasStoryboardDesign: false
    property bool hasCharacterDesign: false
    property var onGenerate: null

    title: ""

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
                            onGenerate(
                                promptExtendEnabled,
                                useStoryboardDesign,
                                useCharacterDesign,
                                negativePromptInput.text.trim()
                            )
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
                spacing: 4

                CheckBox {
                    id: storyboardDesignCheck
                    text: "引用分镜设计图"
                    checked: useStoryboardDesign
                    enabled: hasStoryboardDesign
                    onCheckedChanged: useStoryboardDesign = checked
                }

                Label {
                    Layout.fillWidth: true
                    Layout.leftMargin: 32
                    text: hasStoryboardDesign
                        ? "使用当前分镜的设计图作为构图与氛围参考"
                        : "暂无分镜设计图"
                    font.pixelSize: Theme.fontSizeSmall
                    color: hasStoryboardDesign ? Material.foreground : Material.hintTextColor
                    opacity: hasStoryboardDesign ? 0.7 : 1.0
                    wrapMode: Text.Wrap
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                CheckBox {
                    id: characterDesignCheck
                    text: "引用角色设计图"
                    checked: useCharacterDesign
                    enabled: hasCharacterDesign
                    onCheckedChanged: useCharacterDesign = checked
                }

                Label {
                    Layout.fillWidth: true
                    Layout.leftMargin: 32
                    text: hasCharacterDesign
                        ? "使用分镜内容中出现的角色设计图作为外观参考"
                        : "暂无匹配的角色设计图"
                    font.pixelSize: Theme.fontSizeSmall
                    color: hasCharacterDesign ? Material.foreground : Material.hintTextColor
                    opacity: hasCharacterDesign ? 0.7 : 1.0
                    wrapMode: Text.Wrap
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    text: "负向提示词"
                    font.pixelSize: Theme.fontSizeNormal
                    color: Material.foreground
                }

                Label {
                    Layout.fillWidth: true
                    text: "描述不希望出现在视频中的内容，批量生成时所有分镜共用"
                    font.pixelSize: Theme.fontSizeSmall
                    color: Material.foreground
                    opacity: 0.7
                    wrapMode: Text.Wrap
                }

                TextArea {
                    id: negativePromptInput
                    Layout.fillWidth: true
                    Layout.preferredHeight: 72
                    placeholderText: "低质量、模糊、水印、文字…"
                    wrapMode: TextArea.Wrap
                    font.pixelSize: Theme.fontSizeNormal
                    selectByMouse: true
                }
            }
        }
    }

    function _loadDesignAvailability(projectId, shotIds) {
        hasStoryboardDesign = false
        hasCharacterDesign = false

        var previewJson = bridge.storyboard.get_video_generate_preview(
            projectId,
            JSON.stringify(shotIds)
        )
        if (!previewJson)
            return

        var preview = JSON.parse(previewJson)
        hasStoryboardDesign = (preview.storyboardDesigns || []).length > 0
        hasCharacterDesign = (preview.characterDesigns || []).length > 0
    }

    function show(projectId, shotIds, callback) {
        var ids = shotIds || []
        shotCount = ids.length > 0 ? ids.length : 1
        promptExtendEnabled = true
        promptExtendSwitch.checked = true
        negativePromptInput.text = ""
        onGenerate = callback

        _loadDesignAvailability(projectId, ids)

        useStoryboardDesign = hasStoryboardDesign
        useCharacterDesign = hasCharacterDesign
        storyboardDesignCheck.checked = useStoryboardDesign
        characterDesignCheck.checked = useCharacterDesign

        open()
    }
}
