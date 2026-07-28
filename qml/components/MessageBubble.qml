import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: bubble
    height: layout.implicitHeight + 8

    property bool isUser: false
    property string messageText: ""
    property string timeText: ""
    property string msgStatus: ""
    property string localPath: ""
    property string errorMessage: ""
    property string msgId: ""

    RowLayout {
        id: layout
        width: parent.width
        spacing: 8
        layoutDirection: isUser ? Qt.RightToLeft : Qt.LeftToRight

        Item { Layout.preferredWidth: 40 }  // 留空对齐

        Rectangle {
            Layout.maximumWidth: parent.width * 0.7
            Layout.minimumWidth: 80
            implicitHeight: contentCol.implicitHeight + 16
            radius: 10
            color: isUser ? Theme.bubbleUser : Theme.bubbleAI

            ColumnLayout {
                id: contentCol
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 8
                spacing: 4

                // 文本内容
                Label {
                    visible: messageText.length > 0
                    text: messageText
                    wrapMode: Text.Wrap
                    font.pixelSize: Theme.fontSizeNormal
                    color: isUser ? Theme.textUser : Theme.textAI
                    Layout.fillWidth: true
                }

                // 视频状态卡片
                VideoStatusCard {
                    visible: !isUser && msgStatus !== ""
                    Layout.fillWidth: true
                    status: msgStatus
                    videoPath: localPath
                    errorMsg: errorMessage
                }

                // 时间标签
                Label {
                    text: timeText
                    font.pixelSize: 10
                    color: isUser ? Qt.lighter(Theme.textUser, 1.3) : Theme.textSecondary
                    Layout.alignment: isUser ? Qt.AlignRight : Qt.AlignLeft
                }
            }
        }

        Item { Layout.fillWidth: true }
    }
}
