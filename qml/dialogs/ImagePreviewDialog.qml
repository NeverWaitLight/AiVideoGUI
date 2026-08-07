import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: dialog
    property string imageSource: ""

    modal: true
    closePolicy: Popup.NoAutoClose

    anchors.centerIn: parent
    width: Math.min(parent.width * 0.9, 1200)
    height: Math.min(parent.height * 0.9, 900)

    padding: 0

    background: Rectangle {
        color: Material.background
        radius: Theme.radiusMedium
    }

    contentItem: Item {
        anchors.fill: parent

        // 图片显示区域
        Image {
            id: previewImage
            anchors.fill: parent
            anchors.margins: 8
            source: imageSource ? "file:///" + imageSource : ""
            fillMode: Image.PreserveAspectFit
            cache: false

            Rectangle {
                visible: previewImage.status === Image.Loading
                anchors.centerIn: parent
                width: 100
                height: 100
                color: "transparent"

                BusyIndicator {
                    anchors.centerIn: parent
                    running: true
                }
            }

            Label {
                visible: previewImage.status === Image.Error
                anchors.centerIn: parent
                text: "图片加载失败"
                font.pixelSize: Theme.fontSizeMedium
                opacity: 0.5
            }
        }

        // 关闭按钮
        Button {
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 16
            anchors.rightMargin: 16
            width: 40
            height: 40
            display: AbstractButton.IconOnly
            icon.source: "qrc:/resources/icons/close.svg"
            icon.width: 24
            icon.height: 24
            icon.color: "white"
            z: 10

            topPadding: 8
            bottomPadding: 8
            leftPadding: 8
            rightPadding: 8

            background: Rectangle {
                radius: parent.width / 2
                color: parent.pressed
                    ? Qt.rgba(0, 0, 0, 0.8)
                    : (parent.hovered ? Qt.rgba(0, 0, 0, 0.7) : Qt.rgba(0, 0, 0, 0.6))
            }

            onClicked: dialog.close()
        }
    }

    function show(imagePath) {
        imageSource = imagePath
        open()
    }
}
