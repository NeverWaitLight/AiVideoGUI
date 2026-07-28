import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components" as Comp
import "pages" as Pages
import "dialogs" as Dialogs

ApplicationWindow {
    id: root
    width: 1100
    height: 700
    minimumWidth: 960
    minimumHeight: 640
    visible: true
    title: "AI 视频生成"
    color: Theme.bgChat

    property int currentMode: 0  // 0: 直接生成, 1: 项目管理

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // 左侧 Tab 栏
        Comp.TabBar {
            id: tabBar
            Layout.fillHeight: true
            Layout.preferredWidth: Theme.tabBarWidth
            onTabChanged: function(index) {
                root.currentMode = index
            }
            onSettingsClicked: settingsDialog.open()
        }

        // 右侧内容区域
        StackLayout {
            id: contentStack
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: root.currentMode

            // 直接生成模式
            Pages.DirectModePage {
                id: directModePage
            }

            // 项目管理模式
            Pages.ProjectModePage {
                id: projectModePage
            }
        }
    }

    // 全局信号监听
    Connections {
        target: bridge

        function onTask_finished(messageId, localPath, storyboardId) {
            bridge.conversations.set_completed(messageId, localPath)
        }

        function onTask_failed(messageId, error) {
            bridge.conversations.set_failed(messageId, error)
        }

        function onTask_status_changed(messageId, status) {
            bridge.conversations.update_status(messageId, status)
        }

        function onTitle_ready(convId, title) {
            bridge.conversations.update_title(convId, title)
        }
    }

    // 设置对话框
    Dialogs.SettingsDialog {
        id: settingsDialog
    }

    // 通用确认对话框
    Dialogs.ConfirmDialog {
        id: confirmDialog
    }

    // 通用提示对话框
    Dialogs.AlertDialog {
        id: alertDialog
    }

    Component.onCompleted: {
        bridge.conversations.load_all()
        bridge.projects.load_projects()
    }
}
