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

    property string currentPage: "project"

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // 左侧 Tab 栏
        Comp.TabBar {
            id: tabBar
            Layout.fillHeight: true
            Layout.preferredWidth: Theme.tabBarWidth
            onSettingsClicked: settingsDialog.open()
            onLibraryClicked: {
                root.currentPage = "library"
                globalMediaPage.projectId = -1
                bridge.media.load_files()
            }
            onTabChanged: {
                root.currentPage = "project"
            }
        }

        // 右侧内容区域
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: root.currentPage === "project" ? 0 : 1

            Pages.ProjectModePage {
                id: projectModePage
            }

            Pages.MediaLibraryPage {
                id: globalMediaPage
                onBackClicked: {
                    root.currentPage = "project"
                    tabBar.currentIndex = 0
                }
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
