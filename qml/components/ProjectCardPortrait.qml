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
    signal editClicked(int projectId)
    signal deleteClicked(int projectId)

    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        Comp.ImagePreview {
            Layout.minimumWidth: Math.max(0, (card.width - 24 - 12) * 0.5)
            Layout.fillWidth: true
            Layout.fillHeight: true
            imageSource: coverPath
            fillMode: Image.PreserveAspectFit
            placeholderIcon: "qrc:/resources/icons/movie.svg"
            placeholderIconSize: 32
            busy: card.isGeneratingCover
            busyText: "生成中..."
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 6

            Label {
                text: projectName
                font.pixelSize: Theme.fontSizeMedium
                font.bold: true
                wrapMode: Text.Wrap
                maximumLineCount: 3
                Layout.fillWidth: true
            }

            Label {
                text: resolution
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.7
                Layout.fillWidth: true
            }

            Label {
                text: aspectRatio
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.7
                Layout.fillWidth: true
            }

            Label {
                text: createdAt
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.5
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                visible: visualStyleId > 0

                Image {
                    Layout.preferredWidth: 18
                    Layout.preferredHeight: 18
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

            Item { Layout.fillHeight: true }

            Button {
                Layout.preferredHeight: 36
                Layout.fillWidth: true
                flat: true
                text: "编辑"
                icon.source: "qrc:/resources/icons/edit.svg"
                icon.width: 18
                icon.height: 18
                topPadding: 6
                bottomPadding: 6
                leftPadding: 8
                rightPadding: 8
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
                Layout.preferredHeight: 36
                Layout.fillWidth: true
                flat: true
                text: "删除"
                icon.source: "qrc:/resources/icons/delete.svg"
                icon.width: 18
                icon.height: 18
                topPadding: 6
                bottomPadding: 6
                leftPadding: 8
                rightPadding: 8
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
