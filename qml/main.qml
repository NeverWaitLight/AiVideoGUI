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
    property int resizeBorderWidth: 5


    MouseArea {
        id: resizeMouseArea
        anchors.fill: parent
        hoverEnabled: true
        propagateComposedEvents: true
        preventStealing: false
        acceptedButtons: Qt.LeftButton

        property int edges: 0

        onPositionChanged: {
            if (pressed) return

            var leftEdge = mouseX < resizeBorderWidth
            var rightEdge = mouseX > width - resizeBorderWidth
            var topEdge = mouseY < resizeBorderWidth
            var bottomEdge = mouseY > height - resizeBorderWidth

            edges = 0
            if (leftEdge) edges |= Qt.LeftEdge
            if (rightEdge) edges |= Qt.RightEdge
            if (topEdge) edges |= Qt.TopEdge
            if (bottomEdge) edges |= Qt.BottomEdge

            if ((topEdge && leftEdge) || (bottomEdge && rightEdge)) {
                cursorShape = Qt.SizeFDiagCursor
            } else if ((topEdge && rightEdge) || (bottomEdge && leftEdge)) {
                cursorShape = Qt.SizeBDiagCursor
            } else if (leftEdge || rightEdge) {
                cursorShape = Qt.SizeHorCursor
            } else if (topEdge || bottomEdge) {
                cursorShape = Qt.SizeVerCursor
            } else {
                cursorShape = Qt.ArrowCursor
            }
        }

        onPressed: function(mouse) {
            if (edges !== 0) {
                root.startSystemResize(edges)
            } else {
                mouse.accepted = false
            }
        }

        onExited: {
            cursorShape = Qt.ArrowCursor
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

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

                    Comp.MainPanel {
                        id: mainPanel
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        currentPage: root.currentPage
                        onCurrentPageChanged: root.currentPage = currentPage
                    }

                    Rectangle {
                        Layout.fillHeight: true
                        width: 1
                        color: "white"
                        visible: rightBar.aiChatVisible
                    }

                    Comp.AIChatPanel {
                        id: aiChatPanel
                        Layout.preferredWidth: 320
                        Layout.fillHeight: true
                        visible: rightBar.aiChatVisible
                    }
                }
            }

            Comp.RightBar {
                id: rightBar
                Layout.fillHeight: true
                Layout.preferredWidth: Theme.rightBarWidth
            }
        }

        Comp.BottomBar {
            Layout.fillWidth: true
        }
    }

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

    Dialogs.SettingsDialog {
        id: settingsDialog
    }

    Dialogs.ConfirmDialog {
        id: confirmDialog
    }

    Dialogs.AlertDialog {
        id: alertDialog
    }

    Component.onCompleted: {
        x = (Screen.width - width) / 2
        y = (Screen.height - height) / 2

        bridge.conversations.load_all()
        bridge.projects.load_projects()
    }
}
