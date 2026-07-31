import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

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

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 130
            radius: Theme.radiusMedium
            clip: true
            color: "transparent"

            Image {
                anchors.fill: parent
                source: coverPath ? "file:///" + coverPath : ""
                fillMode: Image.PreserveAspectFit
                visible: source !== "" && !card.isGeneratingCover
            }

            Image {
                anchors.centerIn: parent
                source: "qrc:/resources/icons/movie.svg"
                sourceSize.width: 48
                sourceSize.height: 48
                visible: !coverPath && !card.isGeneratingCover
            }

            BusyIndicator {
                anchors.centerIn: parent
                width: 60
                height: 60
                running: card.isGeneratingCover
                visible: card.isGeneratingCover
            }

            Label {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: 50
                text: "生成封面中..."
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.7
                visible: card.isGeneratingCover
            }
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
