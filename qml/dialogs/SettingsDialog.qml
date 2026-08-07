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
    property string videoModelT2V: ""
    property string videoModelI2V: ""
    property string videoModelR2V: ""
    property string chatProvider: "deepseek"
    property string chatProviderId: "deepseek"
    property string chatModel: ""
    property var chatProviderPresets: []
    property string imageProvider: "dashscope_image"
    property string imageModel: ""
    property var imageModelList: []
    property bool imageModelsLoading: false
    property string workspacePath: ""

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header
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
                    text: ""
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

        // Tab bar
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

        // Lazy-loaded tab content: each tab's Loader only instantiates its
        // component when first activated (active: true).  The StackLayout
        // keeps all Loaders alive so saveAll() can read every tab at once.
        // Each Loader uses ">=" so that once a tab is visited, its component
        // stays alive (data is preserved even when switching to other tabs).
        // Only tabs the user has never clicked remain un-instantiated.
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex

            Loader {
                id: chatLoader
                active: tabBar.currentIndex >= 0
                sourceComponent: chatTabComponent
            }
            Loader {
                id: imageLoader
                active: tabBar.currentIndex >= 1
                sourceComponent: imageTabComponent
            }
            Loader {
                id: videoLoader
                active: tabBar.currentIndex >= 2
                sourceComponent: videoTabComponent
            }
            Loader {
                id: workspaceLoader
                active: tabBar.currentIndex >= 3
                sourceComponent: workspaceTabComponent
            }
            Loader {
                id: appearanceLoader
                active: tabBar.currentIndex >= 4
                sourceComponent: appearanceTabComponent
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
        // Read all settings (fast, synchronous)
        videoProvider = bridge.settings.get_default_video_provider()
        videoModelT2V = bridge.settings.get_model_for_task_type(videoProvider, "video", "t2v")
        videoModelI2V = bridge.settings.get_model_for_task_type(videoProvider, "video", "i2v")
        videoModelR2V = bridge.settings.get_model_for_task_type(videoProvider, "video", "r2v")

        // Load chat provider presets and active provider
        chatProviderPresets = bridge.settings.get_chat_provider_presets()
        chatProviderId = bridge.settings.get_active_chat_provider_id()

        imageProvider = bridge.settings.get_default_image_provider()
        imageModel = bridge.settings.get_default_model(imageProvider, "image")

        workspacePath = bridge.settings.get_workspace_dir()
    }

    function saveAll() {
        var chat = chatLoader.item
        var img = imageLoader.item
        var vid = videoLoader.item

        // Save chat provider
        if (chat) {
            var selectedPreset = chat.getSelectedPreset()
            if (!selectedPreset) {
                alertDialog.warning("配置错误", "请选择一个文本模型提供商")
                tabBar.currentIndex = 0
                return
            }

            if (selectedPreset.type === "custom") {
                // Custom provider needs all fields
                if (!chat.chatApiKeyField.text) {
                    alertDialog.warning("配置错误", "请输入 API Key")
                    tabBar.currentIndex = 0
                    return
                }
                if (!chat.chatBaseUrlField.text) {
                    alertDialog.warning("配置错误", "请输入 Base URL")
                    tabBar.currentIndex = 0
                    return
                }
                if (!chat.chatModelField.text) {
                    alertDialog.warning("配置错误", "请输入模型名称")
                    tabBar.currentIndex = 0
                    return
                }
                bridge.settings.update_chat_provider_credential(
                    selectedPreset.id,
                    chat.chatApiKeyField.text,
                    chat.chatBaseUrlField.text,
                    chat.chatModelField.text
                )
            } else {
                // Preset provider only needs API key
                if (!chat.chatApiKeyField.text) {
                    alertDialog.warning("配置错误", "请输入 API Key")
                    tabBar.currentIndex = 0
                    return
                }
                bridge.settings.update_chat_provider_credential(
                    selectedPreset.id,
                    chat.chatApiKeyField.text,
                    "",
                    ""
                )
            }

            // Set active provider
            bridge.settings.set_active_chat_provider_id(selectedPreset.id)
        }

        // Validate image
        if (img) {
            var imageError = bridge.settings.validate_provider_config(
                "image", img.imageProviderCombo.currentText,
                img.imageApiKeyField.text, img.imageBaseUrlField.text,
                img.imageModelCombo.currentText || img.imageModelCombo.editText)
            if (imageError) {
                alertDialog.warning("图片配置错误", imageError)
                tabBar.currentIndex = 1
                return
            }
        }

        // Validate video
        if (vid) {
            var videoError = bridge.settings.validate_provider_config(
                "video", vid.videoProviderCombo.currentText,
                vid.videoApiKeyField.text, vid.videoBaseUrlField.text,
                vid.videoModelT2VCombo.currentText || vid.videoModelT2VCombo.editText)
            if (videoError) {
                alertDialog.warning("视频配置错误", videoError)
                tabBar.currentIndex = 2
                return
            }
        }

        // Batch save providers (re-read after validation switched tabs)
        img = imageLoader.item
        vid = videoLoader.item

        if (img) {
            bridge.settings.batch_save_provider("image",
                img.imageProviderCombo.currentText,
                img.imageApiKeyField.text, img.imageBaseUrlField.text,
                img.imageModelCombo.currentText || img.imageModelCombo.editText, {})
        }
        if (vid) {
            var modelMappings = {
                "t2v": vid.videoModelT2VCombo.currentText || vid.videoModelT2VCombo.editText,
                "i2v": vid.videoModelI2VCombo.currentText || vid.videoModelI2VCombo.editText,
                "r2v": vid.videoModelR2VCombo.currentText || vid.videoModelR2VCombo.editText
            }
            bridge.settings.batch_save_provider("video",
                vid.videoProviderCombo.currentText,
                vid.videoApiKeyField.text, vid.videoBaseUrlField.text,
                vid.videoModelT2VCombo.currentText || vid.videoModelT2VCombo.editText,
                modelMappings)
        }

        // Workspace
        if (workspacePath !== bridge.settings.get_workspace_dir()) {
            bridge.settings.batch_set("workspace_dir", workspacePath)
        }

        // Color scheme & AI logging
        if (appearanceLoader.item) {
            var oldColorScheme = bridge.settings.get_color_scheme()
            var newColorScheme = appearanceLoader.item.colorSchemeLight.checked ? "Light"
                : (appearanceLoader.item.colorSchemeDark.checked ? "Dark" : "System")
            if (oldColorScheme !== newColorScheme) {
                bridge.settings.batch_set("color_scheme", newColorScheme)
                Qt.callLater(function() {
                    alertDialog.info("设置已保存", "颜色方案的更改需要重启应用才能生效。")
                })
            }

            var newAiLogging = appearanceLoader.item.aiLoggingSwitch.checked
            if (bridge.settings.get_enable_ai_request_logging() !== newAiLogging) {
                bridge.settings.batch_set_bool("enable_ai_request_logging", newAiLogging)
            }
        }

        bridge.settings.commit_batch()
    }

    // ==================== Tab Components (lazy-loaded) ====================

    Component {
        id: chatTabComponent

        ScrollView {
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            clip: true
            contentWidth: availableWidth

            property alias chatProviderCombo: chatProviderCombo
            property alias chatApiKeyField: chatApiKeyField
            property alias chatBaseUrlField: chatBaseUrlField
            property alias chatModelField: chatModelField

            // Get selected preset object
            function getSelectedPreset() {
                var idx = chatProviderCombo.currentIndex
                if (idx >= 0 && idx < settingsDialog.chatProviderPresets.length) {
                    return settingsDialog.chatProviderPresets[idx]
                }
                return null
            }

            // Update UI based on selected provider type
            function updateProviderUI() {
                var preset = getSelectedPreset()
                if (!preset) return

                var providerId = preset.id
                var credential = bridge.settings.get_chat_provider_credential(providerId)

                // Load credentials
                chatApiKeyField.text = credential.api_key || ""

                if (preset.type === "custom") {
                    // Custom provider: show Base URL and Model fields
                    chatBaseUrlField.visible = true
                    baseUrlLabel.visible = true
                    chatModelField.visible = true
                    modelLabel.visible = true

                    chatBaseUrlField.text = credential.base_url || ""
                    chatModelField.text = credential.model || ""
                } else {
                    // Preset provider: hide Base URL and Model fields
                    chatBaseUrlField.visible = false
                    baseUrlLabel.visible = false
                    chatModelField.visible = false
                    modelLabel.visible = false
                }
            }

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
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                Material.elevation: 0
                                textRole: "display_name"
                                model: settingsDialog.chatProviderPresets

                                onCurrentIndexChanged: {
                                    updateProviderUI()
                                }
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
                                id: baseUrlLabel
                                text: "Base URL"
                                font.pixelSize: Theme.fontSizeNormal
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                                visible: false
                            }
                            Comp.AppTextField {
                                id: chatBaseUrlField
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                placeholderText: "https://api.example.com/v1"
                                visible: false
                            }

                            Label {
                                id: modelLabel
                                text: "Model"
                                font.pixelSize: Theme.fontSizeNormal
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                                visible: false
                            }
                            Comp.AppTextField {
                                id: chatModelField
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                placeholderText: "模型名称（如 gpt-4o）"
                                visible: false
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            Component.onCompleted: {
                // Find and select the active provider
                for (var i = 0; i < settingsDialog.chatProviderPresets.length; i++) {
                    if (settingsDialog.chatProviderPresets[i].id === settingsDialog.chatProviderId) {
                        chatProviderCombo.currentIndex = i
                        break
                    }
                }
                updateProviderUI()
            }
        }
    }

    Component {
        id: imageTabComponent

        ScrollView {
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            clip: true
            contentWidth: availableWidth

            property alias imageProviderCombo: imageProviderCombo
            property alias imageApiKeyField: imageApiKeyField
            property alias imageBaseUrlField: imageBaseUrlField
            property alias imageModelCombo: imageModelCombo

            Timer {
                id: imageFetchTimer
                interval: 50
                repeat: false
                onTriggered: {
                    var models = bridge.settings.list_image_models(
                        imageApiKeyField.text, imageBaseUrlField.text,
                        imageProviderCombo.currentText)
                    settingsDialog.imageModelList = models
                    settingsDialog.imageModelsLoading = false
                    if (settingsDialog.imageModel) {
                        var idx = imageModelCombo.find(settingsDialog.imageModel)
                        if (idx >= 0) {
                            imageModelCombo.currentIndex = idx
                        } else {
                            imageModelCombo.editText = settingsDialog.imageModel
                        }
                        settingsDialog.imageModel = ""
                    }
                }
            }

            function fetchImageModels() {
                var provider = imageProviderCombo.currentText
                if (!provider) return
                settingsDialog.imageModelsLoading = true
                imageFetchTimer.start()
            }

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
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                ComboBox {
                                    id: imageModelCombo
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    editable: true
                                    enabled: !settingsDialog.imageModelsLoading
                                    model: settingsDialog.imageModelList
                                    Material.elevation: 0
                                }

                                Button {
                                    implicitHeight: 36
                                    implicitWidth: 36
                                    enabled: imageProviderCombo.currentText.length > 0 && !settingsDialog.imageModelsLoading
                                    Material.elevation: 0
                                    padding: 6
                                    onClicked: fetchImageModels()

                                    contentItem: Image {
                                        anchors.centerIn: parent
                                        width: 20
                                        height: 20
                                        source: "qrc:/resources/icons/autorenew.svg"
                                        sourceSize: Qt.size(20, 20)
                                        fillMode: Image.PreserveAspectFit

                                        RotationAnimation on rotation {
                                            running: settingsDialog.imageModelsLoading
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

            Component.onCompleted: {
                imageApiKeyField.text = bridge.settings.get_api_key(settingsDialog.imageProvider, "image")
                imageBaseUrlField.text = bridge.settings.get_base_url(settingsDialog.imageProvider, "image")
                if (settingsDialog.imageModelList.length > 0) {
                    var idx = imageModelCombo.find(settingsDialog.imageModel)
                    if (idx >= 0) {
                        imageModelCombo.currentIndex = idx
                    } else if (settingsDialog.imageModel) {
                        imageModelCombo.editText = settingsDialog.imageModel
                    }
                } else if (settingsDialog.imageModel) {
                    imageModelCombo.editText = settingsDialog.imageModel
                }
                fetchImageModels()
            }
        }
    }

    Component {
        id: videoTabComponent

        ScrollView {
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            clip: true
            contentWidth: availableWidth

            property alias videoProviderCombo: videoProviderCombo
            property alias videoApiKeyField: videoApiKeyField
            property alias videoBaseUrlField: videoBaseUrlField
            property alias videoModelT2VCombo: videoModelT2VCombo
            property alias videoModelI2VCombo: videoModelI2VCombo
            property alias videoModelR2VCombo: videoModelR2VCombo

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
                                text: "文生视频模型"
                                font.pixelSize: Theme.fontSizeNormal
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                            }
                            ComboBox {
                                id: videoModelT2VCombo
                                model: ["wan2.7-t2v-2026-06-12"]
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                Material.elevation: 0
                                editable: true
                            }

                            Label {
                                text: "图生视频模型"
                                font.pixelSize: Theme.fontSizeNormal
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                            }
                            ComboBox {
                                id: videoModelI2VCombo
                                model: ["wan2.7-i2v-2026-04-25"]
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                Material.elevation: 0
                                editable: true
                            }

                            Label {
                                text: "依赖生视频模型"
                                font.pixelSize: Theme.fontSizeNormal
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                            }
                            ComboBox {
                                id: videoModelR2VCombo
                                model: ["wan2.7-r2v-2026-06-12"]
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                Material.elevation: 0
                                editable: true
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            Component.onCompleted: {
                videoApiKeyField.text = bridge.settings.get_api_key(settingsDialog.videoProvider, "video")
                videoBaseUrlField.text = bridge.settings.get_base_url(settingsDialog.videoProvider, "video")

                // 如果配置为空，使用 ComboBox model 中的第一个选项作为默认值
                var t2v = settingsDialog.videoModelT2V || videoModelT2VCombo.model[0]
                var i2v = settingsDialog.videoModelI2V || videoModelI2VCombo.model[0]
                var r2v = settingsDialog.videoModelR2V || videoModelR2VCombo.model[0]

                // 尝试在 model 中查找匹配项，找不到则设置 editText（手动输入）
                var t2vIndex = videoModelT2VCombo.find(t2v)
                if (t2vIndex >= 0) {
                    videoModelT2VCombo.currentIndex = t2vIndex
                } else {
                    videoModelT2VCombo.editText = t2v
                }

                var i2vIndex = videoModelI2VCombo.find(i2v)
                if (i2vIndex >= 0) {
                    videoModelI2VCombo.currentIndex = i2vIndex
                } else {
                    videoModelI2VCombo.editText = i2v
                }

                var r2vIndex = videoModelR2VCombo.find(r2v)
                if (r2vIndex >= 0) {
                    videoModelR2VCombo.currentIndex = r2vIndex
                } else {
                    videoModelR2VCombo.editText = r2v
                }
            }
        }
    }

    Component {
        id: workspaceTabComponent

        ScrollView {
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            clip: true
            contentWidth: availableWidth

            property alias workspaceDirField: workspaceDirField

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
                                        settingsDialog.workspacePath = path
                                    }
                                }
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            Component.onCompleted: {
                workspaceDirField.text = settingsDialog.workspacePath
            }
        }
    }

    Component {
        id: appearanceTabComponent

        ScrollView {
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            clip: true
            contentWidth: availableWidth

            property alias colorSchemeLight: colorSchemeLight
            property alias colorSchemeDark: colorSchemeDark
            property alias colorSchemeSystem: colorSchemeSystem
            property alias aiLoggingSwitch: aiLoggingSwitch

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
                                text: "AI 请求日志"
                                font.pixelSize: Theme.fontSizeLarge
                                font.bold: true
                            }

                            Label {
                                text: "记录 AI 调用的请求参数和响应到 Markdown 日志文件"
                                font.pixelSize: Theme.fontSizeSmall
                                color: Material.hintTextColor
                                wrapMode: Text.Wrap
                                Layout.fillWidth: true
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Material.frameColor
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12

                            ColumnLayout {
                                spacing: 2
                                Layout.fillWidth: true

                                Label {
                                    text: "启用 AI 请求日志"
                                    font.pixelSize: Theme.fontSizeNormal
                                    font.bold: true
                                }

                                Label {
                                    text: "自动保存每次 AI 调用的请求参数到项目日志目录下的 .md 文件"
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Material.hintTextColor
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }
                            }

                            Switch {
                                id: aiLoggingSwitch
                                Layout.alignment: Qt.AlignVCenter
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            Component.onCompleted: {
                var currentColorScheme = bridge.settings.get_color_scheme()
                if (currentColorScheme === "Light") {
                    colorSchemeLight.checked = true
                } else if (currentColorScheme === "Dark") {
                    colorSchemeDark.checked = true
                } else {
                    colorSchemeSystem.checked = true
                }
                aiLoggingSwitch.checked = bridge.settings.get_enable_ai_request_logging()
            }
        }
    }
}
