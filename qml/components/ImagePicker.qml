import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Item {
    id: root

    property string imageSource: ""
    property bool busy: false
    property int cacheKey: 0

    signal aiGenerateClicked()
    signal uploadClicked()
    signal deleteClicked()

    Rectangle {
        id: container
        anchors.fill: parent
        radius: Theme.radiusMedium
        clip: true
        color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.03)
        border.width: 1
        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.15)

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 12
            visible: !root.imageSource && !root.busy

            Button {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredHeight: 34
                text: "AI 生成"
                font.pixelSize: Theme.fontSizeSmall
                onClicked: root.aiGenerateClicked()
            }

            Button {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredHeight: 34
                text: "上传"
                font.pixelSize: Theme.fontSizeSmall
                onClicked: root.uploadClicked()
            }
        }

        BusyIndicator {
            anchors.centerIn: parent
            visible: root.busy
            running: root.busy
        }

        Image {
            id: displayImage
            anchors.fill: parent
            anchors.margins: 2
            source: root.imageSource ? "file:///" + root.imageSource + "?v=" + root.cacheKey : ""
            fillMode: Image.PreserveAspectFit
            visible: source !== "" && !root.busy
            asynchronous: true
            cache: false
        }

        MouseArea {
            anchors.fill: parent
            enabled: root.imageSource !== "" && !root.busy
            cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: (mouse) => {
                if (mouse.button === Qt.LeftButton) {
                    fullscreenOverlay.open()
                }
            }
            onReleased: (mouse) => {
                if (mouse.button === Qt.RightButton && root.imageSource) {
                    contextMenu.popup()
                }
            }
        }

        Menu {
            id: contextMenu
            MenuItem {
                text: "AI 生成"
                icon.source: "qrc:/resources/icons/auto_awesome.svg"
                icon.width: 18
                icon.height: 18
                onClicked: root.aiGenerateClicked()
            }
            MenuItem {
                text: "上传"
                icon.source: "qrc:/resources/icons/image.svg"
                icon.width: 18
                icon.height: 18
                onClicked: root.uploadClicked()
            }
            MenuItem {
                text: "删除"
                icon.source: "qrc:/resources/icons/delete.svg"
                icon.width: 18
                icon.height: 18
                onClicked: root.deleteClicked()
            }
        }
    }

    Popup {
        id: fullscreenOverlay
        parent: Overlay.overlay
        modal: true
        padding: 0
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        implicitWidth: Overlay.overlay ? Overlay.overlay.width - 120 : 680
        implicitHeight: Overlay.overlay ? Overlay.overlay.height - 120 : 480
        x: Overlay.overlay ? 60 : 40
        y: Overlay.overlay ? 60 : 40

        background: Rectangle {
            color: Qt.rgba(0.9, 0.9, 0.9, 0.85)
            border.width: 1
            border.color: Qt.rgba(0, 0, 0, 0.15)
            radius: Theme.radiusMedium
        }

        contentItem: Item {
            Image {
                id: previewImage
                anchors.fill: parent
                anchors.margins: 16
                fillMode: Image.PreserveAspectFit
                source: root.imageSource ? "file:///" + root.imageSource + "?v=" + root.cacheKey : ""
                asynchronous: true
                cache: false
            }

            Button {
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.topMargin: 8
                anchors.rightMargin: 8
                width: 28
                height: 28
                display: AbstractButton.IconOnly
                icon.source: "qrc:/resources/icons/close.svg"
                icon.width: 20
                icon.height: 20
                icon.color: Qt.rgba(0, 0, 0, 0.87)
                topPadding: 0
                bottomPadding: 0
                leftPadding: 0
                rightPadding: 0
                z: 1

                background: Rectangle {
                    anchors.fill: parent
                    radius: parent.width / 2
                    color: parent.hovered ? Qt.rgba(0, 0, 0, 0.12) : Qt.rgba(1, 1, 1, 0.8)
                }

                onClicked: fullscreenOverlay.close()
            }

            Keys.onEscapePressed: fullscreenOverlay.close()
            focus: true
        }
    }
}
