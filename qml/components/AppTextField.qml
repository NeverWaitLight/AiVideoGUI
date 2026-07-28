import QtQuick 2.15
import QtQuick.Controls 2.15

TextField {
    color: Theme.textAI
    font.pixelSize: Theme.fontSizeMedium
    padding: 8
    leftPadding: 12
    rightPadding: 12
    selectByMouse: true

    background: Rectangle {
        radius: Theme.borderRadius
        color: "#F5F5F5"
        border.color: parent.activeFocus ? Theme.primary : Theme.border
        border.width: 1
    }
}
