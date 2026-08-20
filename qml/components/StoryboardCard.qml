import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." as Comp

Pane {
    id: card
    height: 100
    padding: 0

    property int shotId: 0
    property int sceneNumber: 0
    property int shotNumber: 0
    property string visualContent: ""
    property string designImage: ""
    property int designImageRevision: 0
    property bool designImageBusy: false
    property bool videoGenerationBusy: false
    property string cameraMovement: ""
    property real duration: 0
    property bool multiSelect: false
    property bool selected: false

    signal clicked()

    background: Rectangle {
        radius: Theme.cardRadius
        color: card.selected ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(0, 0, 0, 0.08)
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: multiSelect ? 48 : 16
        anchors.topMargin: 12
        anchors.bottomMargin: 12
        spacing: 12

        Comp.ImagePreview {
            width: 100; height: 72
            imageSource: designImage
            cacheKey: designImageRevision
            busy: designImageBusy || videoGenerationBusy
            placeholderIcon: "qrc:/resources/icons/image.svg"
            placeholderIconSize: 32
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            RowLayout {
                spacing: 8
                Label {
                    text: sceneNumber + "场" + shotNumber + "镜"
                    font.pixelSize: Theme.fontSizeMedium
                    font.bold: true
                }
                Rectangle {
                    width: sizeLabel.implicitWidth + 12; height: 18; radius: 9
                    Label {
                        id: sizeLabel
                        anchors.centerIn: parent
                        text: cameraMovement || "固定"
                        font.pixelSize: Theme.fontSizeTiny
                    }
                }
            }
            Label {
                text: "运镜：" + (cameraMovement || "固定") + "  |  时长：" + duration + "秒"
                font.pixelSize: Theme.fontSizeSmall
            }
            Label {
                text: visualContent
                font.pixelSize: Theme.fontSizeSmall
                elide: Text.ElideRight
                maximumLineCount: 2
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }

    }

    CheckBox {
        visible: multiSelect
        checked: selected
        anchors.right: parent.right
        anchors.rightMargin: 16
        anchors.verticalCenter: parent.verticalCenter
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: card.clicked()
    }

    property bool isHovered: hoverHandler.hovered
    HoverHandler { id: hoverHandler }
}
