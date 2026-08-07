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
        border.width: card.isDefault ? 2 : 0
        border.color: card.isDefault ? Material.accent : "transparent"
    }

    property int styleId: 0
    property string styleName: ""
    property bool isDefault: false
    property string sampleImagePath: ""
    property string createdAt: ""

    signal clicked()
    signal editClicked(int styleId)
    signal deleteClicked(int styleId)
    signal setDefaultClicked(int styleId)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        Comp.ImagePreview {
            Layout.fillWidth: true
            Layout.preferredHeight: 160
            imageSource: sampleImagePath
            fillMode: Image.PreserveAspectFit
            placeholderIcon: "qrc:/resources/icons/image.svg"
            placeholderIconSize: 48
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: styleName
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            Label {
                visible: card.isDefault
                text: "默认"
                font.pixelSize: Theme.fontSizeSmall
                color: Material.accent
                font.bold: true
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            spacing: 6
            visible: !card.isDefault

            Button {
                Layout.preferredWidth: 68
                Layout.fillHeight: true
                flat: true
                text: "设为默认"
                font.pixelSize: Theme.fontSizeSmall
                z: 1
                onClicked: card.setDefaultClicked(card.styleId)

                background: Rectangle {
                    radius: Theme.radiusSmall
                    color: parent.hovered
                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.15)
                        : "transparent"
                }
            }

            Item { Layout.fillWidth: true }

            Button {
                Layout.preferredWidth: 36
                Layout.fillHeight: true
                flat: true
                display: AbstractButton.IconOnly
                icon.source: "qrc:/resources/icons/delete.svg"
                icon.width: 18
                icon.height: 18
                topPadding: 9
                bottomPadding: 9
                leftPadding: 9
                rightPadding: 9
                z: 1
                ToolTip.visible: hovered
                ToolTip.text: "删除"
                onClicked: card.deleteClicked(card.styleId)

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
