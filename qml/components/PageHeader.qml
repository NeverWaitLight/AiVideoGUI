import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: header
    height: Theme.headerHeight
    color: "transparent"

    property string title: ""
    property string subtitle: ""
    property bool showBack: true

    signal backClicked()

    default property alias rightContent: rightArea.data

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        spacing: 12

        Button {
            visible: header.showBack
            flat: true
            text: "←"
            font.pixelSize: Theme.fontSizeTitle
            onClicked: header.backClicked()
            ToolTip.text: "返回"
            ToolTip.visible: hovered
        }

        ColumnLayout {
            spacing: 2
            Label {
                text: header.title
                font.pixelSize: Theme.fontSizeTitle
                font.bold: true
                color: Theme.textAI
            }
            Label {
                visible: header.subtitle !== ""
                text: header.subtitle
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.textSecondary
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
        color: Theme.border
    }
}
