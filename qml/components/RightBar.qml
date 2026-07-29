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
            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            flat: true
            display: AbstractButton.IconOnly
            icon.source: "qrc:/resources/icons/info.svg"
            icon.width: 22
            icon.height: 22
            ToolTip.text: "关于"
            ToolTip.visible: hovered

            background: Rectangle {
                radius: 2
                color: parent.hovered
                    ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.08)
                    : "transparent"
            }
        }

        Item { Layout.preferredHeight: 6 }
    }

    // 左侧分割线已移除
}
