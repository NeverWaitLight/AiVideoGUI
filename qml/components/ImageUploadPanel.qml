import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ColumnLayout {
    id: root

    property string imageSource: ""
    property string placeholderText: "暂无图片"
    property bool busy: false

    signal uploadClicked()
    signal clearClicked()

    spacing: 8

    Rectangle {
        Layout.fillWidth: true
        Layout.fillHeight: true
        radius: Theme.cardRadius
        color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.05)
        border.width: 1
        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
        clip: true

        Image {
            anchors.fill: parent
            anchors.margins: 2
            source: root.imageSource ? "file:///" + root.imageSource : ""
            fillMode: Image.PreserveAspectFit
            visible: source !== ""
            asynchronous: true
        }

        BusyIndicator {
            anchors.centerIn: parent
            visible: root.busy
            running: root.busy
        }

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 8
            visible: !root.imageSource && !root.busy

            Image {
                source: "qrc:/resources/icons/image.svg"
                sourceSize.width: 48
                sourceSize.height: 48
                Layout.alignment: Qt.AlignHCenter
                opacity: 0.3
            }

            Label {
                text: root.placeholderText
                font.pixelSize: Theme.fontSizeMedium
                opacity: 0.4
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 8

        Button {
            text: "上传"
            flat: true
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            onClicked: root.uploadClicked()
        }

        Button {
            text: "清除"
            flat: true
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            enabled: root.imageSource !== ""
            onClicked: root.clearClicked()
        }
    }
}
