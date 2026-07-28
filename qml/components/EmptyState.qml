import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ColumnLayout {
    id: emptyState
    spacing: 16

    property string text: "暂无数据"
    property string buttonText: ""

    signal buttonClicked()

    Label {
        text: emptyState.text
        font.pixelSize: Theme.fontSizeMedium
        color: Theme.textSecondary
        horizontalAlignment: Text.AlignHCenter
        Layout.alignment: Qt.AlignHCenter
    }

    Button {
        visible: buttonText !== ""
        text: buttonText
        highlighted: true
        Layout.alignment: Qt.AlignHCenter
        onClicked: emptyState.buttonClicked()
    }
}
