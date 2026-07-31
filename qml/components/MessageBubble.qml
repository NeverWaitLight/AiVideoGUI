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

        Item { Layout.preferredWidth: 40 }

        Rectangle {
            Layout.maximumWidth: parent.width * 0.7
            Layout.minimumWidth: 80
            implicitHeight: contentCol.implicitHeight + 16
            radius: Theme.cardRadius

            ColumnLayout {
                id: contentCol
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 8
                spacing: 4

                Label {
                    visible: messageText.length > 0
                    text: messageText
                    wrapMode: Text.Wrap
                    font.pixelSize: Theme.fontSizeNormal
                    Layout.fillWidth: true
                }

                VideoStatusCard {
                    visible: !isUser && msgStatus !== ""
                    Layout.fillWidth: true
                    status: msgStatus
                    videoPath: localPath
                    errorMsg: errorMessage
                }

                Label {
                    text: timeText
                    font.pixelSize: Theme.fontSizeTiny
                    Layout.alignment: isUser ? Qt.AlignRight : Qt.AlignLeft
                }
            }
        }

        Item { Layout.fillWidth: true }
    }
}
