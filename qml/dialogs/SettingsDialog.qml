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
    property string chatProvider: "dashscope"
    property string chatModel: ""
    property string imageProvider: "dashscope"
    property string imageModel: ""
    property string imageModelT2I: ""
    property string imageModelI2I: ""
    property string imageModelR2I: ""
    property string workspacePath: ""

    function providerIdFromCombo(combo) {
        if (!combo || combo.currentIndex < 0 || !combo.model)
            return ""
        var item = combo.model[combo.currentIndex]
        if (!item)
            return ""
        return item.id || ""
    }

    function findProviderIndex(combo, providerId) {
        if (!combo || !combo.model || !providerId)
            return -1
        for (var i = 0; i < combo.count; i++) {
            var item = combo.model[i]
            if (item && item.id === providerId)
                return i
        }
        return -1
    }

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
            TabButton {
                text: "关于"
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
            Loader {
                id: aboutLoader
                active: tabBar.currentIndex >= 5
                sourceComponent: aboutTabComponent
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

        chatProvider = bridge.settings.get_default_chat_provider()
        chatModel = bridge.settings.get_default_model(chatProvider, "chat")

        imageProvider = bridge.settings.get_default_image_provider()
        imageModelT2I = bridge.settings.get_model_for_task_type(imageProvider, "image", "t2i")
            || bridge.settings.get_default_model(imageProvider, "image")
        imageModelI2I = bridge.settings.get_model_for_task_type(imageProvider, "image", "i2i")
        imageModelR2I = bridge.settings.get_model_for_task_type(imageProvider, "image", "r2i")
        imageModel = imageModelT2I

        workspacePath = bridge.settings.get_workspace_dir()
    }

    function saveAll() {
        var chat = chatLoader.item
        var img = imageLoader.item
        var vid = videoLoader.item

        // Validate chat
        if (chat) {
            var chatError = bridge.settings.validate_provider_config(
                "chat", providerIdFromCombo(chat.chatProviderCombo),
                chat.chatApiKeyField.text, chat.chatBaseUrlField.text,
                chat.getChatModelValue())
            if (chatError) {
                alertDialog.warning("文本配置错误", chatError)
                tabBar.currentIndex = 0
                return
            }
        }

        // Validate image
        if (img) {
            var imageDefaultModel = ""
            if (img.imageModelT2ICombo.visible)
                imageDefaultModel = img.imageModelT2ICombo.currentText || img.imageModelT2ICombo.editText
            else if (img.imageModelI2ICombo.visible)
                imageDefaultModel = img.imageModelI2ICombo.currentText || img.imageModelI2ICombo.editText
            else if (img.imageModelR2ICombo.visible)
                imageDefaultModel = img.imageModelR2ICombo.currentText || img.imageModelR2ICombo.editText
            var imageError = bridge.settings.validate_provider_config(
                "image", providerIdFromCombo(img.imageProviderCombo),
                img.imageApiKeyField.text, img.imageBaseUrlField.text,
                imageDefaultModel)
            if (imageError) {
                alertDialog.warning("图片配置错误", imageError)
                tabBar.currentIndex = 1
                return
            }
        }

        // Validate video
        if (vid) {
            var videoDefaultModel = ""
            if (vid.videoModelT2VCombo.visible)
                videoDefaultModel = vid.videoModelT2VCombo.currentText || vid.videoModelT2VCombo.editText
            else if (vid.videoModelI2VCombo.visible)
                videoDefaultModel = vid.videoModelI2VCombo.currentText || vid.videoModelI2VCombo.editText
            else if (vid.videoModelR2VCombo.visible)
                videoDefaultModel = vid.videoModelR2VCombo.currentText || vid.videoModelR2VCombo.editText
            var videoError = bridge.settings.validate_provider_config(
                "video", providerIdFromCombo(vid.videoProviderCombo),
                vid.videoApiKeyField.text, vid.videoBaseUrlField.text,
                videoDefaultModel)
            if (videoError) {
                alertDialog.warning("视频配置错误", videoError)
                tabBar.currentIndex = 2
                return
            }
        }

        // Batch save providers (re-read after validation switched tabs)
        chat = chatLoader.item
        img = imageLoader.item
        vid = videoLoader.item

        if (chat) {
            bridge.settings.batch_save_provider("chat",
                providerIdFromCombo(chat.chatProviderCombo),
                chat.chatApiKeyField.text, chat.chatBaseUrlField.text,
                chat.getChatModelValue(), {})
        }
        if (img) {
            var imageMappings = {}
            var imageDefault = ""
            if (img.imageModelT2ICombo.visible) {
                imageMappings["t2i"] = img.imageModelT2ICombo.currentText || img.imageModelT2ICombo.editText
                imageDefault = imageMappings["t2i"]
            }
            if (img.imageModelI2ICombo.visible) {
                imageMappings["i2i"] = img.imageModelI2ICombo.currentText || img.imageModelI2ICombo.editText
                if (!imageDefault)
                    imageDefault = imageMappings["i2i"]
            }
            if (img.imageModelR2ICombo.visible) {
                imageMappings["r2i"] = img.imageModelR2ICombo.currentText || img.imageModelR2ICombo.editText
                if (!imageDefault)
                    imageDefault = imageMappings["r2i"]
            }
            bridge.settings.batch_save_provider("image",
                providerIdFromCombo(img.imageProviderCombo),
                img.imageApiKeyField.text, img.imageBaseUrlField.text,
                imageDefault, imageMappings)
        }
        if (vid) {
            var modelMappings = {}
            var videoDefault = ""
            if (vid.videoModelT2VCombo.visible) {
                modelMappings["t2v"] = vid.videoModelT2VCombo.currentText || vid.videoModelT2VCombo.editText
                videoDefault = modelMappings["t2v"]
            }
            if (vid.videoModelI2VCombo.visible) {
                modelMappings["i2v"] = vid.videoModelI2VCombo.currentText || vid.videoModelI2VCombo.editText
                if (!videoDefault)
                    videoDefault = modelMappings["i2v"]
            }
            if (vid.videoModelR2VCombo.visible) {
                modelMappings["r2v"] = vid.videoModelR2VCombo.currentText || vid.videoModelR2VCombo.editText
                if (!videoDefault)
                    videoDefault = modelMappings["r2v"]
            }
            bridge.settings.batch_save_provider("video",
                providerIdFromCombo(vid.videoProviderCombo),
                vid.videoApiKeyField.text, vid.videoBaseUrlField.text,
                videoDefault, modelMappings)
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
            property alias chatModelCombo: chatModelCombo
            property alias chatModelField: chatModelField

            function isOpenAICompatible(provider) {
                return provider === "openai"
            }

            function getChatModelValue() {
                if (chatModelField.visible)
                    return chatModelField.text
                return chatModelCombo.currentText || chatModelCombo.editText
            }

            function loadChatProviderState() {
                var provider = settingsDialog.providerIdFromCombo(chatProviderCombo)
                if (!provider)
                    return
                chatBaseUrlField.placeholderText = bridge.settings.get_provider_base_url("chat", provider) || "API 基础地址（可选）"
                chatApiKeyField.text = bridge.settings.get_api_key(provider, "chat")
                chatBaseUrlField.text = bridge.settings.get_base_url(provider, "chat")

                var useTextField = isOpenAICompatible(provider)
                chatModelCombo.visible = !useTextField
                chatModelField.visible = useTextField

                if (useTextField) {
                    chatModelField.text = bridge.settings.get_default_model(provider, "chat") || ""
                } else {
                    chatModelCombo.model = bridge.settings.list_models("chat", provider)
                    if (chatModelCombo.count > 0)
                        chatModelCombo.currentIndex = 0
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
                                model: bridge.settings.list_providers("chat")
                                textRole: "name"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                Material.elevation: 0
                                onActivated: loadChatProviderState()
                            }

                            Label {
                                text: "Base URL"
                                font.pixelSize: Theme.fontSizeNormal
                                color: chatBaseUrlField.text.length > 0 ? Material.foreground : Material.hintTextColor
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
                                text: "默认模型"
                                font.pixelSize: Theme.fontSizeNormal
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                            }
                            Item {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36

                                ComboBox {
                                    id: chatModelCombo
                                    anchors.fill: parent
                                    editable: true
                                    Material.elevation: 0
                                    visible: true
                                }
                                Comp.AppTextField {
                                    id: chatModelField
                                    anchors.fill: parent
                                    placeholderText: "输入模型名称"
                                    visible: false
                                }
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            Component.onCompleted: {
                var pIdx = settingsDialog.findProviderIndex(chatProviderCombo, settingsDialog.chatProvider)
                if (pIdx >= 0)
                    chatProviderCombo.currentIndex = pIdx
                chatApiKeyField.text = bridge.settings.get_api_key(settingsDialog.chatProvider, "chat")
                chatBaseUrlField.text = bridge.settings.get_base_url(settingsDialog.chatProvider, "chat")
                chatBaseUrlField.placeholderText = bridge.settings.get_provider_base_url("chat", settingsDialog.chatProvider) || "API 基础地址（可选）"

                var useTextField = isOpenAICompatible(settingsDialog.chatProvider)
                chatModelCombo.visible = !useTextField
                chatModelField.visible = useTextField

                if (useTextField) {
                    chatModelField.text = settingsDialog.chatModel || bridge.settings.get_default_model(settingsDialog.chatProvider, "chat") || ""
                    settingsDialog.chatModel = ""
                } else {
                    chatModelCombo.model = bridge.settings.list_models("chat", settingsDialog.chatProvider)
                    if (settingsDialog.chatModel) {
                        var idx = chatModelCombo.find(settingsDialog.chatModel)
                        if (idx >= 0)
                            chatModelCombo.currentIndex = idx
                        else
                            chatModelCombo.editText = settingsDialog.chatModel
                        settingsDialog.chatModel = ""
                    }
                }
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
            property alias imageModelT2ICombo: imageModelT2ICombo
            property alias imageModelI2ICombo: imageModelI2ICombo
            property alias imageModelR2ICombo: imageModelR2ICombo

            function selectModelInCombo(combo, value) {
                if (!value)
                    return
                var idx = combo.find(value)
                if (idx >= 0)
                    combo.currentIndex = idx
                else
                    combo.editText = value
            }

            function loadImageProviderState(preserveModels) {
                var provider = settingsDialog.providerIdFromCombo(imageProviderCombo)
                if (!provider)
                    return
                imageBaseUrlField.placeholderText = bridge.settings.get_provider_base_url("image", provider) || "API 基础地址（可选）"
                imageApiKeyField.text = bridge.settings.get_api_key(provider, "image")
                imageBaseUrlField.text = bridge.settings.get_base_url(provider, "image")

                var t2iModels = bridge.settings.list_image_models(provider, "t2i")
                var i2iModels = bridge.settings.list_image_models(provider, "i2i")
                var r2iModels = bridge.settings.list_image_models(provider, "r2i")
                imageModelT2ICombo.model = t2iModels
                imageModelI2ICombo.model = i2iModels
                imageModelR2ICombo.model = r2iModels
                imageModelT2ICombo.visible = t2iModels.length > 0
                imageModelI2ICombo.visible = i2iModels.length > 0
                imageModelR2ICombo.visible = r2iModels.length > 0

                if (preserveModels) {
                    if (imageModelT2ICombo.visible)
                        selectModelInCombo(imageModelT2ICombo, settingsDialog.imageModelT2I || t2iModels[0])
                    if (imageModelI2ICombo.visible)
                        selectModelInCombo(imageModelI2ICombo, settingsDialog.imageModelI2I || i2iModels[0])
                    if (imageModelR2ICombo.visible)
                        selectModelInCombo(imageModelR2ICombo, settingsDialog.imageModelR2I || r2iModels[0])
                } else {
                    if (imageModelT2ICombo.visible && imageModelT2ICombo.count > 0)
                        imageModelT2ICombo.currentIndex = 0
                    if (imageModelI2ICombo.visible && imageModelI2ICombo.count > 0)
                        imageModelI2ICombo.currentIndex = 0
                    if (imageModelR2ICombo.visible && imageModelR2ICombo.count > 0)
                        imageModelR2ICombo.currentIndex = 0
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
                                model: bridge.settings.list_providers("image")
                                textRole: "name"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                Material.elevation: 0
                                onActivated: loadImageProviderState(false)
                            }

                            Label {
                                text: "Base URL"
                                font.pixelSize: Theme.fontSizeNormal
                                color: imageBaseUrlField.text.length > 0 ? Material.foreground : Material.hintTextColor
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
                                text: "文生图模型"
                                font.pixelSize: Theme.fontSizeNormal
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                                visible: imageModelT2ICombo.visible
                            }
                            ComboBox {
                                id: imageModelT2ICombo
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                editable: true
                                Material.elevation: 0
                                visible: false
                            }

                            Label {
                                text: "图生图模型"
                                font.pixelSize: Theme.fontSizeNormal
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                                visible: imageModelI2ICombo.visible
                            }
                            ComboBox {
                                id: imageModelI2ICombo
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                editable: true
                                Material.elevation: 0
                                visible: false
                            }

                            Label {
                                text: "依赖生图模型"
                                font.pixelSize: Theme.fontSizeNormal
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                                visible: imageModelR2ICombo.visible
                            }
                            ComboBox {
                                id: imageModelR2ICombo
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                editable: true
                                Material.elevation: 0
                                visible: false
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            Component.onCompleted: {
                var pIdx = settingsDialog.findProviderIndex(imageProviderCombo, settingsDialog.imageProvider)
                if (pIdx >= 0)
                    imageProviderCombo.currentIndex = pIdx
                loadImageProviderState(true)
                settingsDialog.imageModelT2I = ""
                settingsDialog.imageModelI2I = ""
                settingsDialog.imageModelR2I = ""
                settingsDialog.imageModel = ""
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

            function selectModelInCombo(combo, value) {
                if (!value)
                    return
                var idx = combo.find(value)
                if (idx >= 0)
                    combo.currentIndex = idx
                else
                    combo.editText = value
            }

            function loadVideoProviderState(preserveModels) {
                var provider = settingsDialog.providerIdFromCombo(videoProviderCombo)
                if (!provider)
                    return
                videoBaseUrlField.placeholderText = bridge.settings.get_provider_base_url("video", provider) || "API 基础地址（可选）"
                videoApiKeyField.text = bridge.settings.get_api_key(provider, "video")
                videoBaseUrlField.text = bridge.settings.get_base_url(provider, "video")

                var t2vModels = bridge.settings.list_video_models(provider, "t2v")
                var i2vModels = bridge.settings.list_video_models(provider, "i2v")
                var r2vModels = bridge.settings.list_video_models(provider, "r2v")
                videoModelT2VCombo.model = t2vModels
                videoModelI2VCombo.model = i2vModels
                videoModelR2VCombo.model = r2vModels
                videoModelT2VCombo.visible = t2vModels.length > 0
                videoModelI2VCombo.visible = i2vModels.length > 0
                videoModelR2VCombo.visible = r2vModels.length > 0

                if (preserveModels) {
                    if (videoModelT2VCombo.visible)
                        selectModelInCombo(videoModelT2VCombo, settingsDialog.videoModelT2V || t2vModels[0])
                    if (videoModelI2VCombo.visible)
                        selectModelInCombo(videoModelI2VCombo, settingsDialog.videoModelI2V || i2vModels[0])
                    if (videoModelR2VCombo.visible)
                        selectModelInCombo(videoModelR2VCombo, settingsDialog.videoModelR2V || r2vModels[0])
                } else {
                    if (videoModelT2VCombo.visible && videoModelT2VCombo.count > 0)
                        videoModelT2VCombo.currentIndex = 0
                    if (videoModelI2VCombo.visible && videoModelI2VCombo.count > 0)
                        videoModelI2VCombo.currentIndex = 0
                    if (videoModelR2VCombo.visible && videoModelR2VCombo.count > 0)
                        videoModelR2VCombo.currentIndex = 0
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
                                model: bridge.settings.list_providers("video")
                                textRole: "name"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                Material.elevation: 0
                                onActivated: loadVideoProviderState(false)
                            }

                            Label {
                                text: "Base URL"
                                font.pixelSize: Theme.fontSizeNormal
                                color: videoBaseUrlField.text.length > 0 ? Material.foreground : Material.hintTextColor
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
                                text: "文生视频模型"
                                font.pixelSize: Theme.fontSizeNormal
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                                visible: videoModelT2VCombo.visible
                            }
                            ComboBox {
                                id: videoModelT2VCombo
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                Material.elevation: 0
                                editable: true
                                visible: false
                            }

                            Label {
                                text: "图生视频模型"
                                font.pixelSize: Theme.fontSizeNormal
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                                visible: videoModelI2VCombo.visible
                            }
                            ComboBox {
                                id: videoModelI2VCombo
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                Material.elevation: 0
                                editable: true
                                visible: false
                            }

                            Label {
                                text: "依赖生视频模型"
                                font.pixelSize: Theme.fontSizeNormal
                                Layout.alignment: Qt.AlignTop
                                topPadding: 6
                                visible: videoModelR2VCombo.visible
                            }
                            ComboBox {
                                id: videoModelR2VCombo
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                Material.elevation: 0
                                editable: true
                                visible: false
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            Component.onCompleted: {
                var pIdx = settingsDialog.findProviderIndex(videoProviderCombo, settingsDialog.videoProvider)
                if (pIdx >= 0)
                    videoProviderCombo.currentIndex = pIdx
                loadVideoProviderState(true)
                settingsDialog.videoModelT2V = ""
                settingsDialog.videoModelI2V = ""
                settingsDialog.videoModelR2V = ""
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
            }
        }
    }

    Component {
        id: aboutTabComponent

        ScrollView {
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            clip: true
            contentWidth: availableWidth

            property bool checkingUpdate: false

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
                                text: "关于"
                                font.pixelSize: Theme.fontSizeLarge
                                font.bold: true
                            }

                            Label {
                                text: "应用版本信息和更新"
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

                            RowLayout {
                                spacing: 12
                                Layout.fillWidth: true

                                Label {
                                    text: ""
                                    font.family: "Material Icons"
                                    font.pixelSize: 48
                                    color: Material.accent
                                }

                                ColumnLayout {
                                    spacing: 4
                                    Layout.fillWidth: true

                                    Label {
                                        text: "AI Video GUI"
                                        font.pixelSize: 18
                                        font.bold: true
                                    }

                                    Label {
                                        text: "版本 " + (Qt.application.version || "0.0.1")
                                        font.pixelSize: Theme.fontSizeNormal
                                        color: Material.hintTextColor
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: Material.frameColor
                            }

                            ColumnLayout {
                                spacing: 8
                                Layout.fillWidth: true

                                Label {
                                    text: "检查更新"
                                    font.pixelSize: Theme.fontSizeNormal
                                    font.bold: true
                                }

                                Label {
                                    text: "检查是否有新版本可用"
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Material.hintTextColor
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }

                                Button {
                                    text: checkingUpdate ? "检查中..." : "检查更新"
                                    enabled: !checkingUpdate
                                    implicitHeight: 36
                                    Material.elevation: 1
                                    highlighted: true
                                    onClicked: {
                                        checkingUpdate = true
                                        bridge.update.check_update()
                                        Qt.callLater(function() {
                                            checkingUpdate = false
                                        })
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: Material.frameColor
                            }

                            ColumnLayout {
                                spacing: 8
                                Layout.fillWidth: true

                                Label {
                                    text: "项目信息"
                                    font.pixelSize: Theme.fontSizeNormal
                                    font.bold: true
                                }

                                Label {
                                    text: "GitHub: <a href='https://github.com/NeverWaitLight/AiVideoGUI'>NeverWaitLight/AiVideoGUI</a>"
                                    font.pixelSize: Theme.fontSizeSmall
                                    color: Material.hintTextColor
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                    onLinkActivated: Qt.openUrlExternally(link)
                                    MouseArea {
                                        anchors.fill: parent
                                        acceptedButtons: Qt.NoButton
                                        cursorShape: parent.hoveredLink ? Qt.PointingHandCursor : Qt.ArrowCursor
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
