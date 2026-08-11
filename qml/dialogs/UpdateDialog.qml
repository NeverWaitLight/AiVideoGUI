import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: updateDialog
    title: "发现新版本"
    modal: true
    anchors.centerIn: parent
    width: 500
    closePolicy: downloading ? Dialog.NoAutoClose : Dialog.CloseOnEscape | Dialog.CloseOnPressOutside

    property string newVersion: ""
    property string downloadUrl: ""
    property string releaseNotes: ""
    property string htmlUrl: ""
    property bool downloading: false
    property int downloadedBytes: 0
    property int totalBytes: 0
    property string installerPath: ""
    property string progressText: ""

    function formatBytes(bytes) {
        if (bytes < 1024) return bytes + " B"
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB"
        return (bytes / (1024 * 1024)).toFixed(1) + " MB"
    }

    function updateProgressText() {
        if (totalBytes > 0) {
            progressText = formatBytes(downloadedBytes) + " / " + formatBytes(totalBytes)
        } else {
            progressText = "准备下载..."
        }
    }

    onDownloadedBytesChanged: updateProgressText()
    onTotalBytesChanged: updateProgressText()

    ColumnLayout {
        width: parent.width
        spacing: 16

        Label {
            text: downloading ? "正在下载更新..." : "有新版本可用！"
            font.pixelSize: 16
            font.bold: true
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: !downloading

            RowLayout {
                spacing: 8
                Label {
                    text: "当前版本："
                    font.pixelSize: 14
                }
                Label {
                    text: Qt.application.version || "0.0.1"
                    font.pixelSize: 14
                    color: "#9E9E9E"
                }
            }

            RowLayout {
                spacing: 8
                Label {
                    text: "最新版本："
                    font.pixelSize: 14
                }
                Label {
                    text: updateDialog.newVersion
                    font.pixelSize: 14
                    font.bold: true
                    color: Material.accent
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: Qt.rgba(0, 0, 0, 0.12)
            }

            Label {
                text: "更新内容："
                font.pixelSize: 14
                font.bold: true
                visible: updateDialog.releaseNotes !== ""
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: 200
                visible: updateDialog.releaseNotes !== ""
                clip: true

                TextArea {
                    text: updateDialog.releaseNotes
                    readOnly: true
                    wrapMode: TextArea.Wrap
                    selectByMouse: true
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: downloading

            ProgressBar {
                Layout.fillWidth: true
                from: 0
                to: updateDialog.totalBytes
                value: updateDialog.downloadedBytes
                indeterminate: updateDialog.totalBytes === 0
            }

            Label {
                text: updateDialog.progressText
                font.pixelSize: 12
                color: Material.hintTextColor
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }

    footer: DialogButtonBox {
        Button {
            text: "立即下载"
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            highlighted: true
            visible: !downloading
        }
        Button {
            text: "稍后提醒"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            visible: !downloading
        }
        Button {
            text: "忽略此版本"
            DialogButtonBox.buttonRole: DialogButtonBox.NoRole
            flat: true
            visible: !downloading
            onClicked: {
                bridge.update.ignore_version(updateDialog.newVersion)
                updateDialog.close()
            }
        }
        Button {
            text: "后台下载"
            DialogButtonBox.buttonRole: DialogButtonBox.NoRole
            flat: true
            visible: !downloading
            onClicked: {
                updateDialog.close()
                bridge.update.download_update(updateDialog.downloadUrl)
            }
        }
    }

    onAccepted: {
        downloading = true
        bridge.update.download_update(updateDialog.downloadUrl)
    }

    Connections {
        target: bridge.update

        function onDownload_progress(downloaded, total) {
            updateDialog.downloadedBytes = downloaded
            updateDialog.totalBytes = total
        }

        function onDownload_finished(path) {
            updateDialog.installerPath = path
            updateDialog.downloading = false

            confirmInstallDialog.installerPath = path
            confirmInstallDialog.open()
            updateDialog.close()
        }

        function onDownload_failed(error) {
            updateDialog.downloading = false
            alertDialog.warning("下载失败", error)
            updateDialog.close()
        }
    }

    Dialog {
        id: confirmInstallDialog
        title: "准备安装"
        modal: true
        anchors.centerIn: parent
        width: 400

        property string installerPath: ""

        ColumnLayout {
            width: parent.width
            spacing: 16

            Label {
                text: "更新已下载完成"
                font.pixelSize: 16
                font.bold: true
            }

            Label {
                text: "是否立即安装？安装程序启动后，当前应用将自动关闭。"
                font.pixelSize: 14
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }

        footer: DialogButtonBox {
            Button {
                text: "立即安装"
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
                highlighted: true
            }
            Button {
                text: "稍后安装"
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }

        onAccepted: {
            if (bridge.update.install_update(confirmInstallDialog.installerPath)) {
                Qt.callLater(Qt.quit)
            } else {
                alertDialog.warning("启动安装程序失败", "无法启动安装程序，请手动运行：" + confirmInstallDialog.installerPath)
            }
        }
    }
}
