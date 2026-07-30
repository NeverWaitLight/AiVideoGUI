import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import "components" as Comp
import "pages" as Pages
import "dialogs" as Dialogs

ApplicationWindow {
    id: root
    width: Screen.width / 2
    height: Screen.height / 2
    minimumWidth: 960
    minimumHeight: 640
    visible: true
    title: "AI Video GUI"
    flags: Qt.Window | Qt.FramelessWindowHint

    property string currentPage: "project"

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ===== TopBar | 顶部标题栏 | 显示应用标题和窗口控制按钮 =====
        Comp.TopBar {
            id: titleBar
            Layout.fillWidth: true
            appWindow: root
            title: root.title
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // ===== LeftBar | 左侧边栏 | 项目/素材库标签页切换和设置入口 =====
            Comp.LeftBar {
                id: tabBar
                Layout.fillHeight: true
                Layout.preferredWidth: Theme.tabBarWidth
                currentIndex: root.currentPage === "library" ? 1 : 0
                onSettingsClicked: settingsDialog.open()
                onLibraryClicked: {
                    root.currentPage = "library"
                    mainPanel.mediaLibraryPage.projectId = -1
                    bridge.media.load_files()
                }
                onTabChanged: {
                    root.currentPage = "project"
                }
            }

            // ===== 主内容区统一容器 | 包裹 MainPanel 和 AIChatPanel，提供统一圆角背景 =====
            Control {
                Layout.fillWidth: true
                Layout.fillHeight: true
                padding: 4

                background: Rectangle {
                    radius: Theme.borderRadius
                    color: Qt.darker(Material.background, 1.05)
                }

                contentItem: RowLayout {
                    spacing: 0

                    // MainPanel - 主页面区域（项目管理/素材库）
                    Comp.MainPanel {
                        id: mainPanel
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        currentPage: root.currentPage
                        onCurrentPageChanged: root.currentPage = currentPage
                    }

                    // 竖线分隔符
                    Rectangle {
                        Layout.fillHeight: true
                        width: 1
                        color: "white"
                        visible: rightBar.aiChatVisible
                    }

                    // AIChatPanel - AI 助手对话面板
                    Comp.AIChatPanel {
                        id: aiChatPanel
                        Layout.preferredWidth: 320
                        Layout.fillHeight: true
                        visible: rightBar.aiChatVisible
                    }
                }
            }

            // ===== RightBar | 右侧边栏 | 功能按钮栏（AI 助手开关等） =====
            Comp.RightBar {
                id: rightBar
                Layout.fillHeight: true
                Layout.preferredWidth: Theme.rightBarWidth
            }
        }

        // ===== BottomBar | 底部状态栏 | 显示应用状态和版本信息 =====
        Comp.BottomBar {
            Layout.fillWidth: true
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
        // 居中显示窗口
        x = (Screen.width - width) / 2
        y = (Screen.height - height) / 2

        bridge.conversations.load_all()
        bridge.projects.load_projects()
    }
}
