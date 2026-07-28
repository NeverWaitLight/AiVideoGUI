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
        color: Theme.bgSidebar
        border.color: parent.activeFocus ? Theme.primary : Theme.border
        border.width: 1
    }
}
