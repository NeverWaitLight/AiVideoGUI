import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import "../components" as Comp

Dialog {
    id: settingsDialog
    title: ""
    modal: true
    width: 720
    height: 640
    anchors.centerIn: parent

    topPadding: 0
    leftPadding: 0
    rightPadding: 0
    bottomPadding: 0

    background: Rectangle {
        color: Material.dialogColor
        radius: 12
    }

    property string videoProvider: "dashscope"
    property string videoApiKey: ""
    property string videoBaseUrl: ""
    property string videoModel: "wan2.7-t2v"

    property string chatProvider: "dashscope"
    property string chatApiKey: ""
    property string chatBaseUrl: ""
    property string chatModel: ""
    property var chatModelList: []
    property bool chatModelsLoading: false

    property string imageProvider: "dashscope_image"
    property string imageApiKey: ""
    property string imageBaseUrl: ""
    property string imageModel: ""

    property string workspacePath: ""

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            color: Qt.rgba(0.45, 0.55, 0.82, 0.9)

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 24
                spacing: 16

                Label {
                    text: ""
                    font.family: "Material Icons"
                    font.pixelSize: 28
                    color: "white"
                }

                Label {
                    text: "应用设置"
                    font.pixelSize: 20
                    font.bold: true
                    color: "white"
                    Layout.fillWidth: true
                }
            }
        }

        TabBar {
            id: tabBar
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Material.elevation: 0

            TabButton {
                text: "文本模型"
                implicitWidth: 144
                font.pixelSize: Theme.fontSizeNormal
            }

            TabButton {
                text: "图片模型"
                implicitWidth: 144
                font.pixelSize: Theme.fontSizeNormal
            }

            TabButton {
                text: "视频模型"
                implicitWidth: 144
                font.pixelSize: Theme.fontSizeNormal
            }

            TabButton {
                text: "工作目录"
                implicitWidth: 144
                font.pixelSize: Theme.fontSizeNormal
            }

            TabButton {
                text: "外观"
                implicitWidth: 144
                font.pixelSize: Theme.fontSizeNormal
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex

            ScrollView {
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                clip: true
                contentWidth: availableWidth

                ColumnLayout {
                    width: parent.parent.width
                    spacing: 20

                    Item { Layout.preferredHeight: 8 }

                    Pane {
                        Layout.fillWidth: true
                        Layout.leftMargin: 0
                        Layout.rightMargin: 0
                        Material.elevation: 2
                        padding: 24

                        background: Rectangle {
                            color: Material.dialogColor
                            radius: 8
                            border.width: 0
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 16

                            ColumnLayout {
                                spacing: 4
                                Layout.fillWidth: true

                                Label {
                                    text: "文本模型"
                                    font.pixelSize: Theme.fontSizeLarge
                                    font.bold: true
                                }

                                Label {
                                    text: "配置用于 AI 对话和内容生成的模型"
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Material.hintTextColor
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: Material.frameColor
                            }

                            GridLayout {
                                columns: 2
                                columnSpacing: 16
                                rowSpacing: 16
                                Layout.fillWidth: true

                                Label {
                                    text: "Provider"
                                    font.pixelSize: Theme.fontSizeNormal
                                    Layout.preferredWidth: 100
                                    Layout.alignment: Qt.AlignTop
                                    topPadding: 6
                                }
                                ComboBox {
                                    id: chatProviderCombo
                                    model: ["dashscope"]
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    Material.elevation: 0
                                }

                                Label {
                                    text: "API Key"
                                    font.pixelSize: Theme.fontSizeNormal
                                    Layout.alignment: Qt.AlignTop
                                    topPadding: 6
                                }
                                Comp.AppTextField {
                                    id: chatApiKeyField
                                    echoMode: TextInput.Password
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    placeholderText: "输入 API Key"
                                }

                                Label {
                                    text: "Base URL"
                                    font.pixelSize: Theme.fontSizeNormal
                                    color: Material.hintTextColor
                                    Layout.alignment: Qt.AlignTop
                                    topPadding: 6
                                }
                                Comp.AppTextField {
                                    id: chatBaseUrlField
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    placeholderText: "API 基础地址（可选）"
                                }

                                Label {
                                    text: "默认模型"
                                    font.pixelSize: Theme.fontSizeNormal
                                    Layout.alignment: Qt.AlignTop
                                    topPadding: 6
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8

                                    ComboBox {
                                        id: chatModelCombo
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 36
                                        editable: true
                                        enabled: !chatModelsLoading
                                        model: chatModelList
                                        Material.elevation: 0
                                    }

                                    Button {
                                        implicitHeight: 36
                                        implicitWidth: 36
                                        enabled: chatApiKeyField.text.length > 0 && !chatModelsLoading
                                        Material.elevation: 0
                                        padding: 6
                                        onClicked: fetchChatModels()

                                        Image {
                                            anchors.centerIn: parent
                                            width: 20; height: 20
                                            source: "qrc:/resources/icons/autorenew.svg"
                                            sourceSize: Qt.size(20, 20)
                                            fillMode: Image.PreserveAspectFit

                                            RotationAnimation on rotation {
                                                running: chatModelsLoading
                                                from: 0; to: 360
                                                duration: 1000
                                                loops: Animation.Infinite
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            ScrollView {
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                clip: true
                contentWidth: availableWidth

                ColumnLayout {
                    width: parent.parent.width
                    spacing: 20

                    Item { Layout.preferredHeight: 8 }

                    Pane {
                        Layout.fillWidth: true
                        Layout.leftMargin: 0
                        Layout.rightMargin: 0
                        Material.elevation: 2
                        padding: 24

                        background: Rectangle {
                            color: Material.dialogColor
                            radius: 8
                            border.width: 0
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 16

                            ColumnLayout {
                                spacing: 4
                                Layout.fillWidth: true

                                Label {
                                    text: "图片生成模型"
                                    font.pixelSize: Theme.fontSizeLarge
                                    font.bold: true
                                }

                                Label {
                                    text: "配置用于生成分镜设计图的模型"
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Material.hintTextColor
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: Material.frameColor
                            }

                            GridLayout {
                                columns: 2
                                columnSpacing: 16
                                rowSpacing: 16
                                Layout.fillWidth: true

                                Label {
                                    text: "Provider"
                                    font.pixelSize: Theme.fontSizeNormal
                                    Layout.preferredWidth: 100
                                    Layout.alignment: Qt.AlignTop
                                    topPadding: 6
                                }
                                ComboBox {
                                    id: imageProviderCombo
                                    model: ["dashscope_image"]
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    Material.elevation: 0
                                }

                                Label {
                                    text: "API Key"
                                    font.pixelSize: Theme.fontSizeNormal
                                    Layout.alignment: Qt.AlignTop
                                    topPadding: 6
                                }
                                Comp.AppTextField {
                                    id: imageApiKeyField
                                    echoMode: TextInput.Password
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    placeholderText: "输入 API Key"
                                }

                                Label {
                                    text: "Base URL"
                                    font.pixelSize: Theme.fontSizeNormal
                                    color: Material.hintTextColor
                                    Layout.alignment: Qt.AlignTop
                                    topPadding: 6
                                }
                                Comp.AppTextField {
                                    id: imageBaseUrlField
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    placeholderText: "API 基础地址（可选）"
                                }

                                Label {
                                    text: "默认模型"
                                    font.pixelSize: Theme.fontSizeNormal
                                    color: Material.hintTextColor
                                    Layout.alignment: Qt.AlignTop
                                    topPadding: 6
                                }
                                Comp.AppTextField {
                                    id: imageModelField
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    placeholderText: "模型名称（可选）"
                                }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }
            ScrollView {
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                clip: true
                contentWidth: availableWidth

                ColumnLayout {
                    width: parent.parent.width
                    spacing: 20

                    Item { Layout.preferredHeight: 8 }

                    Pane {
                        Layout.fillWidth: true
                        Layout.leftMargin: 0
                        Layout.rightMargin: 0
                        Material.elevation: 2
                        padding: 24

                        background: Rectangle {
                            color: Material.dialogColor
                            radius: 8
                            border.width: 0
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 16

                            ColumnLayout {
                                spacing: 4
                                Layout.fillWidth: true

                                Label {
                                    text: "视频生成模型"
                                    font.pixelSize: Theme.fontSizeLarge
                                    font.bold: true
                                }

                                Label {
                                    text: "配置用于生成 AI 视频的模型和凭证"
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Material.hintTextColor
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: Material.frameColor
                            }

                            GridLayout {
                                columns: 2
                                columnSpacing: 16
                                rowSpacing: 16
                                Layout.fillWidth: true

                                Label {
                                    text: "Provider"
                                    font.pixelSize: Theme.fontSizeNormal
                                    Layout.preferredWidth: 100
                                    Layout.alignment: Qt.AlignTop
                                    topPadding: 6
                                }
                                ComboBox {
                                    id: videoProviderCombo
                                    model: ["dashscope", "seedance"]
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    Material.elevation: 0
                                }

                                Label {
                                    text: "API Key"
                                    font.pixelSize: Theme.fontSizeNormal
                                    Layout.alignment: Qt.AlignTop
                                    topPadding: 6
                                }
                                Comp.AppTextField {
                                    id: videoApiKeyField
                                    echoMode: TextInput.Password
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    placeholderText: "输入 API Key"
                                }

                                Label {
                                    text: "Base URL"
                                    font.pixelSize: Theme.fontSizeNormal
                                    color: Material.hintTextColor
                                    Layout.alignment: Qt.AlignTop
                                    topPadding: 6
                                }
                                Comp.AppTextField {
                                    id: videoBaseUrlField
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    placeholderText: "API 基础地址（可选）"
                                }

                                Label {
                                    text: "默认模型"
                                    font.pixelSize: Theme.fontSizeNormal
                                    Layout.alignment: Qt.AlignTop
                                    topPadding: 6
                                }
                                ComboBox {
                                    id: videoModelCombo
                                    model: ["wan2.7-t2v"]
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    Material.elevation: 0
                                }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }


            ScrollView {
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                clip: true
                contentWidth: availableWidth

                ColumnLayout {
                    width: parent.parent.width
                    spacing: 20

                    Item { Layout.preferredHeight: 8 }

                    Pane {
                        Layout.fillWidth: true
                        Layout.leftMargin: 0
                        Layout.rightMargin: 0
                        Material.elevation: 2
                        padding: 24

                        background: Rectangle {
                            color: Material.dialogColor
                            radius: 8
                            border.width: 0
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 16

                            ColumnLayout {
                                spacing: 4
                                Layout.fillWidth: true

                                Label {
                                    text: "工作目录"
                                    font.pixelSize: Theme.fontSizeLarge
                                    font.bold: true
                                }

                                Label {
                                    text: "设置媒体文件的存储位置"
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Material.hintTextColor
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: Material.frameColor
                            }

                            ColumnLayout {
                                spacing: 12
                                Layout.fillWidth: true

                                Label {
                                    text: "媒体工作区"
                                    font.pixelSize: Theme.fontSizeNormal
                                    font.bold: true
                                }

                                Label {
                                    text: "所有生成的视频、图片等文件将保存到此目录"
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Material.hintTextColor
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }

                                RowLayout {
                                    spacing: 12
                                    Layout.fillWidth: true

                                    Comp.AppTextField {
                                        id: workspaceDirField
                                        text: workspacePath
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 36
                                        readOnly: true
                                        font.pixelSize: Theme.fontSizeSmall
                                    }

                                    Button {
                                        text: "浏览..."
                                        implicitHeight: 36
                                        implicitWidth: 90
                                        Material.elevation: 1
                                        onClicked: {
                                            var path = bridge.settings.browse_workspace_dir()
                                            workspaceDirField.text = path
                                            workspacePath = path
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            ScrollView {
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                clip: true
                contentWidth: availableWidth

                ColumnLayout {
                    width: parent.parent.width
                    spacing: 20

                    Item { Layout.preferredHeight: 8 }

                    Pane {
                        Layout.fillWidth: true
                        Layout.leftMargin: 0
                        Layout.rightMargin: 0
                        Material.elevation: 2
                        padding: 24

                        background: Rectangle {
                            color: Material.dialogColor
                            radius: 8
                            border.width: 0
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 16

                            ColumnLayout {
                                spacing: 4
                                Layout.fillWidth: true

                                Label {
                                    text: "外观设置"
                                    font.pixelSize: Theme.fontSizeLarge
                                    font.bold: true
                                }

                                Label {
                                    text: "自定义应用的外观和主题"
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Material.hintTextColor
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: Material.frameColor
                            }

                            ColumnLayout {
                                spacing: 16
                                Layout.fillWidth: true

                                Label {
                                    text: "颜色方案"
                                    font.pixelSize: Theme.fontSizeNormal
                                    font.bold: true
                                }

                                Label {
                                    text: "选择界面的外观主题（需要重启应用生效）"
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Material.hintTextColor
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }

                                ButtonGroup {
                                    id: colorSchemeGroup
                                }

                                ColumnLayout {
                                    spacing: 12
                                    Layout.fillWidth: true

                                    Pane {
                                        Layout.fillWidth: true
                                        Material.elevation: 0
                                        padding: 12

                                        background: Rectangle {
                                            color: colorSchemeLight.checked ? Material.color(Material.Blue, Material.Shade50) : "transparent"
                                            radius: 6
                                            border.color: colorSchemeLight.checked ? Material.accent : Material.frameColor
                                            border.width: colorSchemeLight.checked ? 2 : 1
                                        }

                                        RowLayout {
                                            anchors.fill: parent
                                            spacing: 12

                                            RadioButton {
                                                id: colorSchemeLight
                                                ButtonGroup.group: colorSchemeGroup
                                            }

                                            Label {
                                                text: ""
                                                font.family: "Material Icons"
                                                font.pixelSize: 24
                                                color: Material.accent
                                            }

                                            ColumnLayout {
                                                spacing: 2
                                                Layout.fillWidth: true

                                                Label {
                                                    text: "亮色模式"
                                                    font.pixelSize: Theme.fontSizeNormal
                                                    font.bold: true
                                                }

                                                Label {
                                                    text: "清新明亮的界面风格"
                                                    font.pixelSize: Theme.fontSizeSmall
                                                    color: Material.hintTextColor
                                                }
                                            }
                                        }
                                    }

                                    Pane {
                                        Layout.fillWidth: true
                                        Material.elevation: 0
                                        padding: 12

                                        background: Rectangle {
                                            color: colorSchemeDark.checked ? Material.color(Material.Blue, Material.Shade50) : "transparent"
                                            radius: 6
                                            border.color: colorSchemeDark.checked ? Material.accent : Material.frameColor
                                            border.width: colorSchemeDark.checked ? 2 : 1
                                        }

                                        RowLayout {
                                            anchors.fill: parent
                                            spacing: 12

                                            RadioButton {
                                                id: colorSchemeDark
                                                ButtonGroup.group: colorSchemeGroup
                                            }

                                            Label {
                                                text: ""
                                                font.family: "Material Icons"
                                                font.pixelSize: 24
                                                color: Material.accent
                                            }

                                            ColumnLayout {
                                                spacing: 2
                                                Layout.fillWidth: true

                                                Label {
                                                    text: "暗色模式"
                                                    font.pixelSize: Theme.fontSizeNormal
                                                    font.bold: true
                                                }

                                                Label {
                                                    text: "护眼舒适的暗色主题"
                                                    font.pixelSize: Theme.fontSizeSmall
                                                    color: Material.hintTextColor
                                                }
                                            }
                                        }
                                    }

                                    Pane {
                                        Layout.fillWidth: true
                                        Material.elevation: 0
                                        padding: 12

                                        background: Rectangle {
                                            color: colorSchemeSystem.checked ? Material.color(Material.Blue, Material.Shade50) : "transparent"
                                            radius: 6
                                            border.color: colorSchemeSystem.checked ? Material.accent : Material.frameColor
                                            border.width: colorSchemeSystem.checked ? 2 : 1
                                        }

                                        RowLayout {
                                            anchors.fill: parent
                                            spacing: 12

                                            RadioButton {
                                                id: colorSchemeSystem
                                                ButtonGroup.group: colorSchemeGroup
                                                checked: true
                                            }

                                            Label {
                                                text: ""
                                                font.family: "Material Icons"
                                                font.pixelSize: 24
                                                color: Material.accent
                                            }

                                            ColumnLayout {
                                                spacing: 2
                                                Layout.fillWidth: true

                                                Label {
                                                    text: "跟随系统"
                                                    font.pixelSize: Theme.fontSizeNormal
                                                    font.bold: true
                                                }

                                                Label {
                                                    text: "自动适配系统主题设置"
                                                    font.pixelSize: Theme.fontSizeSmall
                                                    color: Material.hintTextColor
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }
        }
    }

    footer: DialogButtonBox {
        padding: 16
        Material.elevation: 0

        background: Rectangle {
            color: Material.dialogColor

            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: 1
                color: Material.frameColor
            }
        }

        Button {
            text: "取消"
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            flat: true
            Material.elevation: 0
        }
        Button {
            text: "保存"
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            Material.elevation: 1
            highlighted: true
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
        chatModel = bridge.settings.get_default_model(chatProvider)
        if (chatApiKeyField.text.length > 0) {
            fetchChatModels()
        } else {
            chatModelCombo.currentIndex = chatModelCombo.find(chatModel)
            if (chatModelCombo.currentIndex === -1) {
                chatModelCombo.editText = chatModel
            }
        }

        imageProvider = bridge.settings.get_default_image_provider()
        imageApiKeyField.text = bridge.settings.get_api_key(imageProvider)
        imageBaseUrlField.text = bridge.settings.get_base_url(imageProvider)
        imageModelField.text = bridge.settings.get_default_model(imageProvider)

        workspacePath = bridge.settings.get_workspace_dir()
        workspaceDirField.text = workspacePath

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
        bridge.settings.batch_save_provider("video", videoProviderCombo.currentText,
            videoApiKeyField.text, videoBaseUrlField.text, videoModelCombo.currentText)

        bridge.settings.batch_save_provider("chat", chatProviderCombo.currentText,
            chatApiKeyField.text, chatBaseUrlField.text, chatModelCombo.currentText)

        bridge.settings.batch_save_provider("image", imageProviderCombo.currentText,
            imageApiKeyField.text, imageBaseUrlField.text, imageModelField.text)

        if (workspacePath !== bridge.settings.get_workspace_dir()) {
            bridge.settings.batch_set("workspace_dir", workspacePath)
        }

        var oldColorScheme = bridge.settings.get_color_scheme()
        var newColorScheme = colorSchemeLight.checked ? "Light" : (colorSchemeDark.checked ? "Dark" : "System")

        var needRestart = false

        if (oldColorScheme !== newColorScheme) {
            bridge.settings.batch_set("color_scheme", newColorScheme)
            needRestart = true
        }

        bridge.settings.commit_batch()

        if (needRestart) {
            Qt.callLater(function() {
                alertDialog.info("设置已保存", "颜色方案的更改需要重启应用才能生效。")
            })
        }
    }

    Timer {
        id: fetchModelsTimer
        interval: 50
        repeat: false
        onTriggered: {
            var models = bridge.settings.list_chat_models(
                chatApiKeyField.text, chatBaseUrlField.text, chatProviderCombo.currentText)
            chatModelList = models
            chatModelsLoading = false
            if (chatModel) {
                var idx = chatModelCombo.find(chatModel)
                if (idx >= 0) {
                    chatModelCombo.currentIndex = idx
                } else {
                    chatModelCombo.editText = chatModel
                }
                chatModel = ""
            }
        }
    }

    function fetchChatModels() {
        var apiKey = chatApiKeyField.text
        if (!apiKey) return
        chatModelsLoading = true
        fetchModelsTimer.start()
    }
}
