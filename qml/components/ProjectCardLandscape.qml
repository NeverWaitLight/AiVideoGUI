import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import "." as Comp

Pane {
    id: card
    padding: 0

    background: Rectangle {
        radius: Theme.cardRadius
        color: Qt.rgba(0, 0, 0, 0.08)
        border.width: 0
    }

    property int projectId: 0
    property string projectName: ""
    property string resolution: ""
    property string aspectRatio: ""
    property string coverPath: ""
    property string createdAt: ""
    property bool isGeneratingCover: false
    property int visualStyleId: 0
    property string visualStyleName: ""
    property string visualStyleImage: ""

    signal clicked()

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Comp.ImagePreview {
            Layout.fillWidth: true
            Layout.preferredHeight: 180
            imageSource: coverPath
            fillMode: Image.PreserveAspectFit
            placeholderIcon: "qrc:/resources/icons/movie.svg"
            placeholderIconSize: 48
            busy: card.isGeneratingCover
            busyText: "生成封面中..."
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: 12
            spacing: 2

            Label {
                text: projectName
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    text: resolution
                    font.pixelSize: Theme.fontSizeNormal
                    opacity: 0.7
                }

                Label {
                    text: aspectRatio
                    font.pixelSize: Theme.fontSizeNormal
                    opacity: 0.7
                }

                Label {
                    text: createdAt
                    font.pixelSize: Theme.fontSizeNormal
                    opacity: 0.5
                }

                Item { Layout.fillWidth: true }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                visible: visualStyleId > 0

                Image {
                    Layout.preferredWidth: 20
                    Layout.preferredHeight: 20
                    source: visualStyleImage ? "file:///" + visualStyleImage : ""
                    fillMode: Image.PreserveAspectCrop

                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                        border.width: 1
                        radius: 3
                    }
                }

                Label {
                    text: visualStyleName
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.6
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }
        }

    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        z: -1
        onClicked: card.clicked()
    }

    property bool isHovered: hoverHandler.hovered
    HoverHandler { id: hoverHandler }
}
