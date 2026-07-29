import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

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
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        spacing: 12

        Button {
            visible: header.showBack
            flat: true
            icon.source: "qrc:/resources/icons/arrow_back.svg"
            icon.width: 24
            icon.height: 24
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
    }
}
