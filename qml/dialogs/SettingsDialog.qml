import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp

Dialog {
    id: settingsDialog
    title: "设置"
    modal: true
    width: 640
    height: 560
    anchors.centerIn: parent

    property string videoProvider: "dashscope"
    property string videoApiKey: ""
    property string videoBaseUrl: ""
    property string videoModel: "wan2.7-t2v"

    property string chatProvider: "dashscope"
    property string chatApiKey: ""
    property string chatBaseUrl: ""
    property string chatModel: ""

    property string imageProvider: "dashscope_image"
    property string imageApiKey: ""
    property string imageBaseUrl: ""
    property string imageModel: ""

    property string workspacePath: ""

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TabBar {
            id: tabBar
            Layout.fillWidth: true
            Layout.preferredHeight: 44

            TabButton {
                text: "视频模型"
                width: implicitWidth
            }

            TabButton {
                text: "对话模型"
                width: implicitWidth
            }

            TabButton {
                text: "图片模型"
                width: implicitWidth
            }

            TabButton {
                text: "工作目录"
                width: implicitWidth
            }

            TabButton {
                text: "外观"
                width: implicitWidth
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex

            // 视频模型配置
            ScrollView {
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                clip: true

                ColumnLayout {
                    width: parent.width
                    spacing: 16

                    Item { Layout.preferredHeight: 16 }

                    Label {
                        text: "视频生成模型配置"
                        font.pixelSize: Theme.fontSizeLarge
                        font.bold: true
                        Layout.leftMargin: 24
                    }

                    GridLayout {
                        columns: 2
                        columnSpacing: 12
                        rowSpacing: 12
                        Layout.fillWidth: true
                        Layout.leftMargin: 24
                        Layout.rightMargin: 24

                        Label {
                            text: "Provider:"
                            font.pixelSize: Theme.fontSizeNormal
                            Layout.preferredWidth: 80
                        }
                        ComboBox {
                            id: videoProviderCombo
                            model: ["dashscope", "seedance"]
                            Layout.fillWidth: true
                        }

                        Label {
                            text: "API Key:"
                            font.pixelSize: Theme.fontSizeNormal
                        }
                        Comp.AppTextField {
                            id: videoApiKeyField
                            echoMode: TextInput.Password
                            Layout.fillWidth: true
                            placeholderText: "输入 API Key"
                        }

                        Label {
                            text: "Base URL:"
                            font.pixelSize: Theme.fontSizeNormal
                        }
                        Comp.AppTextField {
                            id: videoBaseUrlField
                            Layout.fillWidth: true
                            placeholderText: "API 基础地址（可选）"
                        }

                        Label {
                            text: "默认模型:"
                            font.pixelSize: Theme.fontSizeNormal
                        }
                        ComboBox {
                            id: videoModelCombo
                            model: ["wan2.7-t2v"]
                            Layout.fillWidth: true
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            // 对话模型配置
            ScrollView {
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                clip: true

                ColumnLayout {
                    width: parent.width
                    spacing: 16

                    Item { Layout.preferredHeight: 16 }

                    Label {
                        text: "对话模型配置"
                        font.pixelSize: Theme.fontSizeLarge
                        font.bold: true
                        Layout.leftMargin: 24
                    }

                    GridLayout {
                        columns: 2
                        columnSpacing: 12
                        rowSpacing: 12
                        Layout.fillWidth: true
                        Layout.leftMargin: 24
                        Layout.rightMargin: 24

                        Label {
                            text: "Provider:"
                            font.pixelSize: Theme.fontSizeNormal
                            Layout.preferredWidth: 80
                        }
                        ComboBox {
                            id: chatProviderCombo
                            model: ["dashscope"]
                            Layout.fillWidth: true
                        }

                        Label {
                            text: "API Key:"
                            font.pixelSize: Theme.fontSizeNormal
                        }
                        Comp.AppTextField {
                            id: chatApiKeyField
                            echoMode: TextInput.Password
                            Layout.fillWidth: true
                            placeholderText: "输入 API Key"
                        }

                        Label {
                            text: "Base URL:"
                            font.pixelSize: Theme.fontSizeNormal
                        }
                        Comp.AppTextField {
                            id: chatBaseUrlField
                            Layout.fillWidth: true
                            placeholderText: "API 基础地址（可选）"
                        }

                        Label {
                            text: "默认模型:"
                            font.pixelSize: Theme.fontSizeNormal
                        }
                        Comp.AppTextField {
                            id: chatModelField
                            Layout.fillWidth: true
                            placeholderText: "模型名称（可选）"
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            // 图片模型配置
            ScrollView {
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                clip: true

                ColumnLayout {
                    width: parent.width
                    spacing: 16

                    Item { Layout.preferredHeight: 16 }

                    Label {
                        text: "图片生成模型配置"
                        font.pixelSize: Theme.fontSizeLarge
                        font.bold: true
                        Layout.leftMargin: 24
                    }

                    GridLayout {
                        columns: 2
                        columnSpacing: 12
                        rowSpacing: 12
                        Layout.fillWidth: true
                        Layout.leftMargin: 24
                        Layout.rightMargin: 24

                        Label {
                            text: "Provider:"
                            font.pixelSize: Theme.fontSizeNormal
                            Layout.preferredWidth: 80
                        }
                        ComboBox {
                            id: imageProviderCombo
                            model: ["dashscope_image"]
                            Layout.fillWidth: true
                        }

                        Label {
                            text: "API Key:"
                            font.pixelSize: Theme.fontSizeNormal
                        }
                        Comp.AppTextField {
                            id: imageApiKeyField
                            echoMode: TextInput.Password
                            Layout.fillWidth: true
                            placeholderText: "输入 API Key"
                        }

                        Label {
                            text: "Base URL:"
                            font.pixelSize: Theme.fontSizeNormal
                        }
                        Comp.AppTextField {
                            id: imageBaseUrlField
                            Layout.fillWidth: true
                            placeholderText: "API 基础地址（可选）"
                        }

                        Label {
                            text: "默认模型:"
                            font.pixelSize: Theme.fontSizeNormal
                        }
                        Comp.AppTextField {
                            id: imageModelField
                            Layout.fillWidth: true
                            placeholderText: "模型名称（可选）"
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            // 工作目录配置
            ScrollView {
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                clip: true

                ColumnLayout {
                    width: parent.width
                    spacing: 16

                    Item { Layout.preferredHeight: 16 }

                    Label {
                        text: "工作目录配置"
                        font.pixelSize: Theme.fontSizeLarge
                        font.bold: true
                        Layout.leftMargin: 24
                    }

                    ColumnLayout {
                        spacing: 8
                        Layout.fillWidth: true
                        Layout.leftMargin: 24
                        Layout.rightMargin: 24

                        Label {
                            text: "媒体文件工作区目录（视频、图片等文件的存储位置）"
                            font.pixelSize: Theme.fontSizeSmall
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }

                        RowLayout {
                            spacing: 8
                            Layout.fillWidth: true

                            Comp.AppTextField {
                                id: workspaceDirField
                                text: workspacePath
                                Layout.fillWidth: true
                                readOnly: true
                                font.pixelSize: Theme.fontSizeSmall
                            }

                            Button {
                                text: "浏览..."
                                implicitHeight: 32
                                implicitWidth: 80
                                onClicked: {
                                    var path = bridge.settings.browse_workspace_dir()
                                    workspaceDirField.text = path
                                    workspacePath = path
                                }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            // 外观配置
            ScrollView {
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                clip: true

                ColumnLayout {
                    width: parent.width
                    spacing: 16

                    Item { Layout.preferredHeight: 16 }

                    Label {
                        text: "界面样式"
                        font.pixelSize: Theme.fontSizeLarge
                        font.bold: true
                    }

                    Label {
                        text: "选择 Qt Quick Controls 2 样式（需要重启应用生效）"
                        font.pixelSize: Theme.fontSizeSmall
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                    }

                    ComboBox {
                        id: styleCombo
                        model: ["Default", "Fusion", "Material", "Universal"]
                        Layout.fillWidth: true
                        Layout.maximumWidth: 300
                    }

                    Label {
                        text: "• Default: 轻量级默认样式\n• Fusion: 桌面风格\n• Material: Google Material Design\n• Universal: Microsoft Universal Design"
                        font.pixelSize: Theme.fontSizeSmall
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                    }

                    Item { Layout.preferredHeight: 16 }

                    Label {
                        text: "颜色方案"
                        font.pixelSize: Theme.fontSizeLarge
                        font.bold: true
                    }

                    Label {
                        text: "选择界面颜色方案（需要重启应用生效）"
                        font.pixelSize: Theme.fontSizeSmall
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                    }

                    ButtonGroup {
                        id: colorSchemeGroup
                    }

                    ColumnLayout {
                        spacing: 8

                        RadioButton {
                            id: colorSchemeLight
                            text: "亮色模式"
                            ButtonGroup.group: colorSchemeGroup
                        }

                        RadioButton {
                            id: colorSchemeDark
                            text: "暗色模式"
                            ButtonGroup.group: colorSchemeGroup
                        }

                        RadioButton {
                            id: colorSchemeSystem
                            text: "跟随系统"
                            ButtonGroup.group: colorSchemeGroup
                            checked: true
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }
        }
    }

    footer: DialogButtonBox {
        Button {
            text: "取消"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
        }
        Button {
            text: "保存"
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
        }
        onAccepted: {
            saveAll()
            settingsDialog.accept()
        }
        onRejected: settingsDialog.reject()
    }

    onAboutToShow: {
        videoProvider = bridge.settings.get_default_video_provider()
        videoApiKeyField.text = bridge.settings.get_api_key(videoProvider)
        videoBaseUrlField.text = bridge.settings.get_base_url(videoProvider)
        videoModel = bridge.settings.get_default_model(videoProvider)

        chatProvider = bridge.settings.get_default_chat_provider()
        chatApiKeyField.text = bridge.settings.get_api_key(chatProvider)
        chatBaseUrlField.text = bridge.settings.get_base_url(chatProvider)
        chatModelField.text = bridge.settings.get_default_model(chatProvider)

        imageProvider = bridge.settings.get_default_image_provider()
        imageApiKeyField.text = bridge.settings.get_api_key(imageProvider)
        imageBaseUrlField.text = bridge.settings.get_base_url(imageProvider)
        imageModelField.text = bridge.settings.get_default_model(imageProvider)

        workspacePath = bridge.settings.get_workspace_dir()
        workspaceDirField.text = workspacePath

        // 加载样式设置
        var currentStyle = bridge.settings.get_style()
        var styleIndex = styleCombo.model.indexOf(currentStyle)
        if (styleIndex >= 0) {
            styleCombo.currentIndex = styleIndex
        }

        // 加载颜色方案设置
        var currentColorScheme = bridge.settings.get_color_scheme()
        if (currentColorScheme === "Light") {
            colorSchemeLight.checked = true
        } else if (currentColorScheme === "Dark") {
            colorSchemeDark.checked = true
        } else {
            colorSchemeSystem.checked = true
        }
    }

    function saveAll() {
        bridge.settings.save_provider("video", videoProviderCombo.currentText,
            videoApiKeyField.text, videoBaseUrlField.text, videoModelCombo.currentText)

        bridge.settings.save_provider("chat", chatProviderCombo.currentText,
            chatApiKeyField.text, chatBaseUrlField.text, chatModelField.text)

        bridge.settings.save_provider("image", imageProviderCombo.currentText,
            imageApiKeyField.text, imageBaseUrlField.text, imageModelField.text)

        if (workspacePath !== bridge.settings.get_workspace_dir()) {
            bridge.settings.set_workspace_dir(workspacePath)
        }

        // 保存样式设置
        var oldStyle = bridge.settings.get_style()
        var newStyle = styleCombo.currentText
        var oldColorScheme = bridge.settings.get_color_scheme()
        var newColorScheme = colorSchemeLight.checked ? "Light" : (colorSchemeDark.checked ? "Dark" : "System")

        var needRestart = false

        if (oldStyle !== newStyle) {
            bridge.settings.set_style(newStyle)
            needRestart = true
        }

        if (oldColorScheme !== newColorScheme) {
            bridge.settings.set_color_scheme(newColorScheme)
            needRestart = true
        }

        if (needRestart) {
            // 显示提示信息
            Qt.callLater(function() {
                alertDialog.info("设置已保存", "样式或颜色方案的更改需要重启应用才能生效。")
            })
        }
    }
}
