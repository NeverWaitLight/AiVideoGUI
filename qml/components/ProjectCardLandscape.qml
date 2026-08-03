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

    signal clicked()
    signal editClicked(int projectId)
    signal deleteClicked(int projectId)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        Comp.ImagePreview {
            Layout.fillWidth: true
            Layout.preferredHeight: 130
            imageSource: coverPath
            fillMode: Image.PreserveAspectFit
            placeholderIcon: "qrc:/resources/icons/movie.svg"
            placeholderIconSize: 48
            busy: card.isGeneratingCover
            busyText: "生成封面中..."
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 56
            spacing: 4

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
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            spacing: 8

            Button {
                Layout.fillWidth: true
                Layout.fillHeight: true
                flat: true
                text: "编辑"
                icon.source: "qrc:/resources/icons/edit.svg"
                icon.width: 20
                icon.height: 20
                z: 1
                onClicked: card.editClicked(card.projectId)

                background: Rectangle {
                    radius: Theme.radiusSmall
                    color: parent.hovered
                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.15)
                        : "transparent"
                }
            }

            Button {
                Layout.fillWidth: true
                Layout.fillHeight: true
                flat: true
                text: "删除"
                icon.source: "qrc:/resources/icons/delete.svg"
                icon.width: 20
                icon.height: 20
                z: 1
                onClicked: card.deleteClicked(card.projectId)

                background: Rectangle {
                    radius: Theme.radiusSmall
                    color: parent.hovered
                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.15)
                        : "transparent"
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
