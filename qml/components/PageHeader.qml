import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

Item {
    id: header
    implicitHeight: Theme.headerHeight

    property string title: ""
    property string subtitle: ""
    property bool showBack: true

    signal backClicked()

    default property alias rightContent: rightArea.data

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 5
        anchors.rightMargin: 5
        spacing: 12

        Button {
            visible: header.showBack
            Layout.preferredWidth: 34
            Layout.preferredHeight: 34
            flat: true
            display: AbstractButton.IconOnly
            icon.source: "qrc:/resources/icons/arrow_back.svg"
            icon.width: 20
            icon.height: 20
            topPadding: 7
            bottomPadding: 7
            leftPadding: 7
            rightPadding: 7
            onClicked: header.backClicked()
            ToolTip.text: "返回"
            ToolTip.visible: hovered

            background: Rectangle {
                anchors.fill: parent
                radius: Theme.radiusSmall
                color: parent.hovered
                    ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                    : "transparent"
            }
        }

        ColumnLayout {
            spacing: 2
            Label {
                text: header.title
                font.pixelSize: Theme.fontSizeMedium
                font.bold: true
            }
            Label {
                visible: header.subtitle !== ""
                text: header.subtitle
                font.pixelSize: Theme.fontSizeSmall
            }
        }

        Item { Layout.fillWidth: true }

        RowLayout {
            id: rightArea
            spacing: 8
        }
    }

    // 底部分割线
    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: "white"
    }
}
