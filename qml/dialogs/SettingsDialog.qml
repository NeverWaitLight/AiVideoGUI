import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: settingsDialog
    title: "设置"
    modal: true
    standardButtons: Dialog.Save | Dialog.Cancel
    width: 500
    height: 400
    anchors.centerIn: parent

    property string videoProvider: "dashscope"
    property string videoApiKey: ""
    property string videoBaseUrl: ""
    property string videoModel: "wan2.7-t2v"

    ColumnLayout {
        anchors.fill: parent
        spacing: 16

        // 视频模型
        GroupBox {
            title: "视频生成模型"
            Layout.fillWidth: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 8

                RowLayout {
                    Label { text: "Provider:"; Layout.preferredWidth: 80 }
                    ComboBox {
                        id: videoProviderCombo
                        model: ["dashscope", "seedance"]
                        Layout.fillWidth: true
                    }
                }
                RowLayout {
                    Label { text: "API Key:"; Layout.preferredWidth: 80 }
                    TextField {
                        id: apiKeyField
                        echoMode: TextInput.Password
                        Layout.fillWidth: true
                        placeholderText: "输入 API Key"
                    }
                }
                RowLayout {
                    Label { text: "Base URL:"; Layout.preferredWidth: 80 }
                    TextField {
                        id: baseUrlField
                        Layout.fillWidth: true
                        placeholderText: "API 基础地址（可选）"
                    }
                }
                RowLayout {
                    Label { text: "默认模型:"; Layout.preferredWidth: 80 }
                    ComboBox {
                        id: modelCombo
                        model: ["wan2.7-t2v"]
                        Layout.fillWidth: true
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }
    }

    onAboutToShow: {
        videoProvider = bridge.settings.get_default_video_provider()
        apiKeyField.text = bridge.settings.get_api_key(videoProvider)
        baseUrlField.text = bridge.settings.get_base_url(videoProvider)
    }

    onAccepted: {
        bridge.settings.save_provider(
            videoProviderCombo.currentText,
            apiKeyField.text,
            baseUrlField.text,
            modelCombo.currentText
        )
    }
}
