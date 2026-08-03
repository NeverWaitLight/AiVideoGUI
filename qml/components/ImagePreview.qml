import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root

    property string imageSource: ""
    property int fillMode: Image.PreserveAspectCrop
    property string placeholderIcon: ""
    property int placeholderIconSize: 48
    property string placeholderText: ""
    property bool busy: false
    property string busyText: ""

    radius: Theme.radiusMedium
    color: "transparent"
    clip: true

    Image {
        anchors.fill: parent
        source: root.imageSource ? "file:///" + root.imageSource : ""
        fillMode: root.fillMode
        visible: source !== "" && !root.busy
        asynchronous: true
    }

    Image {
        anchors.centerIn: parent
        source: root.placeholderIcon
        sourceSize.width: root.placeholderIconSize
        sourceSize.height: root.placeholderIconSize
        visible: !root.imageSource && !root.busy && root.placeholderIcon !== ""
    }

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 4
        visible: root.busy

        BusyIndicator {
            Layout.alignment: Qt.AlignHCenter
            width: root.placeholderIconSize > 40 ? 60 : 40
            height: root.placeholderIconSize > 40 ? 60 : 40
            running: root.busy
        }

        Label {
            text: root.busyText
            font.pixelSize: Theme.fontSizeSmall
            opacity: 0.7
            visible: root.busyText !== ""
            Layout.alignment: Qt.AlignHCenter
        }
    }
}
