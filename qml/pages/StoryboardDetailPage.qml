import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: detailPage
    property int projectId: -1
    property string projectName: ""
    property int shotId: -1

    signal backClicked()

    onShotIdChanged: {
        if (shotId > 0) {
            bridge.storyboard.load_shot(shotId)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Comp.PageHeader {
            projectName: detailPage.projectName
            title: bridge.storyboard.curSceneNumber + "场" + bridge.storyboard.curShotNumber + "镜"
            Layout.fillWidth: true
            onBackClicked: detailPage.backClicked()

            Button {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                display: AbstractButton.IconOnly
                icon.source: "qrc:/resources/icons/video_camera_back.svg"
                icon.width: 20
                icon.height: 20
                icon.color: "white"
                topPadding: 8
                bottomPadding: 8
                leftPadding: 8
                rightPadding: 8
                ToolTip.visible: hovered
                ToolTip.text: "生成视频"

                background: Rectangle {
                    anchors.fill: parent
                    radius: parent.width / 2
                    color: parent.pressed ? "#C62828" : (parent.hovered ? "#E53935" : "#F44336")
                }

                onClicked: confirmDialog.confirm(
                    "确定要为此分镜生成视频吗？",
                    function() { bridge.storyboard.batch_generate_videos(detailPage.projectId, JSON.stringify([bridge.storyboard.curShotId])) }
                )
            }

            Button {
                Layout.preferredWidth: 34
                Layout.preferredHeight: 34
                display: AbstractButton.IconOnly
                icon.source: "qrc:/resources/icons/save.svg"
                icon.width: 20
                icon.height: 20
                topPadding: 7
                bottomPadding: 7
                leftPadding: 7
                rightPadding: 7
                ToolTip.visible: hovered
                ToolTip.text: "保存"

                background: Rectangle {
                    anchors.fill: parent
                    radius: Theme.radiusSmall
                    color: parent.hovered
                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                        : "transparent"
                }

                onClicked: _saveCurrentShot()
            }
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            Layout.topMargin: 12
            columns: 2
            columnSpacing: 10
            rowSpacing: 6

            Label { text: "景别："; font.pixelSize: Theme.fontSizeSmall }
            ComboBox {
                id: shotSizeCombo
                model: ["特写", "近景", "中景", "全景", "远景", "大远景"]
                currentIndex: bridge.storyboard.curShotSizeIndex
                Layout.fillWidth: true
                Layout.preferredHeight: 32
                font.pixelSize: Theme.fontSizeSmall
            }

            Label { text: "运镜："; font.pixelSize: Theme.fontSizeSmall }
            Comp.AppTextField {
                id: cameraInput
                text: bridge.storyboard.curCameraMovement
                placeholderText: "固定、慢推、跟拍"
                Layout.fillWidth: true
                Layout.preferredHeight: 32
            }

            Label { text: "时长（秒）："; font.pixelSize: Theme.fontSizeSmall }
            SpinBox {
                id: durationSpin
                from: 0; to: 600; stepSize: 5
                value: Math.round(bridge.storyboard.curDuration * 10)
                property real realValue: value / 10.0
                textFromValue: function(v, l) { return (v / 10.0).toFixed(1) }
                valueFromText: function(t, l) { return parseFloat(t) * 10 }
                Layout.fillWidth: true
                Layout.preferredHeight: 32
            }

            Label { text: "种子："; font.pixelSize: Theme.fontSizeSmall }
            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Comp.AppTextField {
                    id: seedInput
                    text: bridge.storyboard.curSeed
                    placeholderText: "留空则随机"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
                    validator: IntValidator { bottom: 0; top: 2147483647 }
                }

                Button {
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    display: AbstractButton.IconOnly
                    icon.source: "qrc:/resources/icons/autorenew.svg"
                    icon.width: 18
                    icon.height: 18
                    topPadding: 7
                    bottomPadding: 7
                    leftPadding: 7
                    rightPadding: 7
                    ToolTip.visible: hovered
                    ToolTip.text: "随机种子"

                    background: Rectangle {
                        anchors.fill: parent
                        radius: Theme.radiusSmall
                        color: parent.hovered
                            ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                            : "transparent"
                    }

                    onClicked: seedInput.text = Math.floor(Math.random() * 2147483647).toString()
                }
            }
        }

        Item { Layout.fillHeight: true }
    }

    Dialogs.ConfirmDialog { id: confirmDialog }

    function _saveCurrentShot() {
        bridge.storyboard.save_shot(
            detailPage.shotId,
            shotSizeCombo.currentIndex,
            cameraInput.text,
            "",
            durationSpin.realValue,
            "",
            "",
            "",
            "",
            "",
            seedInput.text
        )
    }

}
