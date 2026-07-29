import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
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
                    globalMediaPage.projectId = -1
                    bridge.media.load_files()
                }
                onTabChanged: {
                    root.currentPage = "project"
                }
            }

            // ===== MainContent | 主内容容器 | 中间主页面区域（项目管理/素材库），带灰色圆角边框 =====
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 0

                Control {
                    anchors.fill: parent
                    padding: 4

                    background: Rectangle {
                        radius: Theme.borderRadius
                        color: Material.background
                        border.width: 1
                        border.color: "#d0d0d0"  // 浅灰色边框
                    }

                    contentItem: StackLayout {
                        currentIndex: root.currentPage === "project" ? 0 : 1

                        Pages.ProjectModePage {
                            id: projectModePage
                        }

                        Pages.MediaLibraryPage {
                            id: globalMediaPage
                            onBackClicked: {
                                root.currentPage = "project"
                            }
                        }
                    }
                }
            }

            // ===== AIChatPanel | AI 对话容器 | AI 助手对话面板（可展开/收起），左侧 4px 间距 =====
            Item {
                Layout.fillHeight: true
                Layout.preferredWidth: rightBar.aiChatVisible ? 324 : 0
                visible: rightBar.aiChatVisible

                Comp.AIChatPanel {
                    id: aiChatPanel
                    anchors.fill: parent
                    anchors.leftMargin: 4
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
        bridge.conversations.load_all()
        bridge.projects.load_projects()
    }
}
