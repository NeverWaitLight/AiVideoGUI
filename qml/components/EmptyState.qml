import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: emptyState

    property string text: "暂无数据"
    property string buttonText: ""

    signal buttonClicked()

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 16

        Label {
            text: emptyState.text
            font.pixelSize: Theme.fontSizeMedium
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
}
