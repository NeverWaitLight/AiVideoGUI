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
    padding: 0

    background: Rectangle {
        color: Theme.bgChat
        radius: Theme.cardRadius
        border.color: Theme.border
        border.width: 1
    }

    header: Rectangle {
        height: Theme.headerHeight
        color: Theme.bgSidebar
        border.color: Theme.border
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Label {
                text: "设置"
                font.pixelSize: Theme.fontSizeTitle
                font.bold: true
                color: Theme.textAI
                Layout.fillWidth: true
            }
        }
    }

    footer: Rectangle {
        height: 64
        color: Theme.bgSidebar
        border.color: Theme.border
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Item { Layout.fillWidth: true }

            Button {
                text: "取消"
                implicitHeight: 32
                implicitWidth: 80
                background: Rectangle {
                    radius: Theme.borderRadius
                    color: parent.hovered ? Theme.bubbleAI : Theme.bgChat
                    border.color: Theme.border
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: Theme.fontSizeNormal
                    color: Theme.textAI
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: settingsDialog.reject()
            }

            Button {
                text: "保存"
                implicitHeight: 32
                implicitWidth: 80
                background: Rectangle {
                    radius: Theme.borderRadius
                    color: parent.hovered ? Theme.primaryHover : Theme.primary
                }
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: Theme.fontSizeNormal
                    color: Theme.textUser
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: {
                    saveAll()
                    settingsDialog.accept()
                }
            }
        }
    }

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
    property string themeMode: "system"

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TabBar {
            id: tabBar
            Layout.fillWidth: true
            Layout.preferredHeight: 44

            background: Rectangle {
                color: Theme.bgChat
                border.color: Theme.border
                border.width: 1
            }

            TabButton {
                text: "视频模型"
                width: implicitWidth
                background: Rectangle {
                    color: parent.checked ? Theme.bgChat : Theme.bgSidebar
                    border.color: Theme.border
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: Theme.fontSizeMedium
                    color: parent.checked ? Theme.primary : Theme.textAI
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            TabButton {
                text: "对话模型"
                width: implicitWidth
                background: Rectangle {
                    color: parent.checked ? Theme.bgChat : Theme.bgSidebar
                    border.color: Theme.border
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: Theme.fontSizeMedium
                    color: parent.checked ? Theme.primary : Theme.textAI
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            TabButton {
                text: "图片模型"
                width: implicitWidth
                background: Rectangle {
                    color: parent.checked ? Theme.bgChat : Theme.bgSidebar
                    border.color: Theme.border
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: Theme.fontSizeMedium
                    color: parent.checked ? Theme.primary : Theme.textAI
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            TabButton {
                text: "工作目录"
                width: implicitWidth
                background: Rectangle {
                    color: parent.checked ? Theme.bgChat : Theme.bgSidebar
                    border.color: Theme.border
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: Theme.fontSizeMedium
                    color: parent.checked ? Theme.primary : Theme.textAI
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            TabButton {
                text: "外观"
                width: implicitWidth
                background: Rectangle {
                    color: parent.checked ? Theme.bgChat : Theme.bgSidebar
                    border.color: Theme.border
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: Theme.fontSizeMedium
                    color: parent.checked ? Theme.primary : Theme.textAI
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
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
                        color: Theme.textAI
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
                            color: Theme.textSecondary
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
                            color: Theme.textSecondary
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
                            color: Theme.textSecondary
                        }
                        Comp.AppTextField {
                            id: videoBaseUrlField
                            Layout.fillWidth: true
                            placeholderText: "API 基础地址（可选）"
                        }

                        Label {
                            text: "默认模型:"
                            font.pixelSize: Theme.fontSizeNormal
                            color: Theme.textSecondary
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
                        color: Theme.textAI
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
                            color: Theme.textSecondary
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
                            color: Theme.textSecondary
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
                            color: Theme.textSecondary
                        }
                        Comp.AppTextField {
                            id: chatBaseUrlField
                            Layout.fillWidth: true
                            placeholderText: "API 基础地址（可选）"
                        }

                        Label {
                            text: "默认模型:"
                            font.pixelSize: Theme.fontSizeNormal
                            color: Theme.textSecondary
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
                        color: Theme.textAI
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
                            color: Theme.textSecondary
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
                            color: Theme.textSecondary
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
                            color: Theme.textSecondary
                        }
                        Comp.AppTextField {
                            id: imageBaseUrlField
                            Layout.fillWidth: true
                            placeholderText: "API 基础地址（可选）"
                        }

                        Label {
                            text: "默认模型:"
                            font.pixelSize: Theme.fontSizeNormal
                            color: Theme.textSecondary
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
                        color: Theme.textAI
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
                            color: Theme.textSecondary
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
                                background: Rectangle {
                                    radius: Theme.borderRadius
                                    color: parent.hovered ? Theme.bubbleAI : Theme.bgChat
                                    border.color: Theme.border
                                    border.width: 1
                                }
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: Theme.fontSizeNormal
                                    color: Theme.textAI
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
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
                        text: "外观设置"
                        font.pixelSize: Theme.fontSizeLarge
                        font.bold: true
                        color: Theme.textAI
                        Layout.leftMargin: 24
                    }

                    ColumnLayout {
                        spacing: 12
                        Layout.fillWidth: true
                        Layout.leftMargin: 24
                        Layout.rightMargin: 24

                        Label {
                            text: "主题模式"
                            font.pixelSize: Theme.fontSizeMedium
                            color: Theme.textAI
                        }

                        ColumnLayout {
                            spacing: 8
                            Layout.fillWidth: true

                            RadioButton {
                                id: themeLightRadio
                                text: "亮色"
                                checked: themeMode === "light"
                                onCheckedChanged: {
                                    if (checked) themeMode = "light"
                                }
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: Theme.fontSizeNormal
                                    color: Theme.textAI
                                    leftPadding: parent.indicator.width + parent.spacing
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }

                            RadioButton {
                                id: themeDarkRadio
                                text: "暗色"
                                checked: themeMode === "dark"
                                onCheckedChanged: {
                                    if (checked) themeMode = "dark"
                                }
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: Theme.fontSizeNormal
                                    color: Theme.textAI
                                    leftPadding: parent.indicator.width + parent.spacing
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }

                            RadioButton {
                                id: themeSystemRadio
                                text: "跟随系统"
                                checked: themeMode === "system"
                                onCheckedChanged: {
                                    if (checked) themeMode = "system"
                                }
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: Theme.fontSizeNormal
                                    color: Theme.textAI
                                    leftPadding: parent.indicator.width + parent.spacing
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }

                        Label {
                            text: "选择 \"跟随系统\" 时，应用会自动适应系统的亮色/暗色主题设置"
                            font.pixelSize: Theme.fontSizeSmall
                            color: Theme.textSecondary
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                            Layout.topMargin: 4
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }
        }
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

        themeMode = bridge.settings.get_theme()
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

        if (themeMode !== bridge.settings.get_theme()) {
            bridge.settings.set_theme(themeMode)
            Theme.mode = themeMode
        }
    }
}
