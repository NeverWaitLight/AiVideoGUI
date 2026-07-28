import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Pane {
    id: card
    height: statusStack.implicitHeight + 16

    property string status: ""  // generating, downloading, completed, failed
    property string videoPath: ""
    property string errorMsg: ""

    ColumnLayout {
        id: statusStack
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        // Generating
        ColumnLayout {
            visible: status === "generating" || status === ""
            Layout.fillWidth: true
            spacing: 8
            ProgressBar { indeterminate: true; Layout.fillWidth: true }
            Label { text: "视频生成中..."; font.pixelSize: Theme.fontSizeSmall }
        }

        // Downloading
        ColumnLayout {
            visible: status === "downloading"
            Layout.fillWidth: true
            spacing: 8
            ProgressBar { indeterminate: true; Layout.fillWidth: true }
            Label { text: "正在下载视频..."; font.pixelSize: Theme.fontSizeSmall }
        }

        // Completed
        ColumnLayout {
            visible: status === "completed"
            Layout.fillWidth: true
            spacing: 8

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 120
                radius: Theme.radiusMedium
                Label {
                    anchors.centerIn: parent
                    text: "▶"
                    font.pixelSize: 36
                }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: bridge.play_video(videoPath)
                }
            }

            RowLayout {
                spacing: 8
                Button { text: "播放"; flat: true; onClicked: bridge.play_video(videoPath) }
                Button { text: "打开文件夹"; flat: true; onClicked: bridge.open_folder(videoPath) }
            }
        }

        // Failed
        ColumnLayout {
            visible: status === "failed"
            Layout.fillWidth: true
            spacing: 8
            Label { text: "❌ 生成失败"; font.pixelSize: Theme.fontSizeNormal }
            Label {
                visible: errorMsg !== ""
                text: errorMsg
                font.pixelSize: Theme.fontSizeSmall
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }
    }
}
