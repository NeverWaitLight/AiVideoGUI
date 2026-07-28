import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Pane {
    id: card
    height: 100
    padding: 10

    property int shotId: 0
    property int sceneNumber: 0
    property int shotNumber: 0
    property string visualContent: ""
    property string designImage: ""
    property string cameraMovement: ""
    property real duration: 0
    property bool selected: false

    signal clicked()
    signal generateVideoClicked()

    background: Rectangle {
        radius: Theme.borderRadius
        color: selected ? "#F0F5FF" : (card.isHovered ? "#FAFAFA" : "#FFFFFF")
        border.color: selected ? Theme.primary : Theme.border
        border.width: selected ? 2 : 1
    }

    RowLayout {
        anchors.fill: parent
        spacing: 12

        // 设计图缩略图
        Rectangle {
            width: 100; height: 72; radius: 6
            color: "#E8E8E8"
            clip: true
            Image {
                anchors.fill: parent
                source: designImage ? "file:///" + designImage : ""
                fillMode: Image.PreserveAspectCrop
                visible: source !== ""
            }
            Label {
                anchors.centerIn: parent
                text: "🖼"
                visible: !designImage
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            RowLayout {
                spacing: 8
                Label {
                    text: "场" + sceneNumber + " 镜" + shotNumber
                    font.pixelSize: Theme.fontSizeMedium
                    font.bold: true
                }
                Rectangle {
                    width: sizeLabel.implicitWidth + 12; height: 18; radius: 9
                    color: "#E3F2FD"
                    Label {
                        id: sizeLabel
                        anchors.centerIn: parent
                        text: cameraMovement || "固定"
                        font.pixelSize: 10; color: Theme.primary
                    }
                }
            }
            Label {
                text: "运镜：" + (cameraMovement || "固定") + "  |  时长：" + duration + "秒"
                font.pixelSize: Theme.fontSizeSmall
                color: "#606060"
            }
            Label {
                text: visualContent
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.textAI
                elide: Text.ElideRight
                maximumLineCount: 2
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }

        // 生成视频按钮
        Button {
            text: "生成视频"
            highlighted: true
            implicitWidth: 80
            Layout.alignment: Qt.AlignVCenter
            onClicked: generateVideoClicked()
        }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: card.clicked()
    }

    property bool isHovered: hoverHandler.hovered
    HoverHandler { id: hoverHandler }
}
