import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

// 空白状态 - 无消息时显示的居中提示
Item {
    id: root

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 16
        width: Math.min(parent.width * 0.8, 400)

        // AI 助手图标
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            width: 64
            height: 64
            radius: 32
            color: Qt.rgba(Material.accent.r, Material.accent.g, Material.accent.b, 0.1)

            Label {
                anchors.centerIn: parent
                text: "✨"
                font.pixelSize: 32
            }
        }

        // 标题
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: "AI 视频生成助手"
            font.pixelSize: Theme.fontSizeLarge
            font.bold: true
            color: Material.foreground
        }

        // 提示文字
        Label {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            text: "描述你想要的视频内容，AI 将为你生成专业的视频作品"
            font.pixelSize: Theme.fontSizeNormal
            color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.6)
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
        }

        // 功能提示（可选）
        ColumnLayout {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 8
            spacing: 4

            Label {
                Layout.alignment: Qt.AlignHCenter
                text: "• 支持多种分辨率和宽高比"
                font.pixelSize: Theme.fontSizeSmall
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.5)
            }

            Label {
                Layout.alignment: Qt.AlignHCenter
                text: "• 自动优化提示词"
                font.pixelSize: Theme.fontSizeSmall
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.5)
            }

            Label {
                Layout.alignment: Qt.AlignHCenter
                text: "• 实时查看生成进度"
                font.pixelSize: Theme.fontSizeSmall
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.5)
            }
        }
    }
}
