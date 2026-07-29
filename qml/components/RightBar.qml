import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Item {
    id: rightBar
    width: Theme.rightBarWidth

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 6
        spacing: 10

        Item { Layout.fillHeight: true }

        // 占位按钮
        Button {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 40
            Layout.preferredHeight: 40
            flat: true
            display: AbstractButton.IconOnly
            icon.source: "qrc:/resources/icons/info.svg"
            icon.width: 20
            icon.height: 20
            ToolTip.text: "关于"
            ToolTip.visible: hovered
        }

        Item { Layout.preferredHeight: 6 }
    }

    // 左侧分割线已移除
}
