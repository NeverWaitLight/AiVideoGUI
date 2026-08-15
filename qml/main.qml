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
    width: Screen.width * 0.75
    height: Screen.height * 0.75
    minimumWidth: 960
    minimumHeight: 640
    visible: true
    title: "AI Video GUI"
    flags: Qt.Window | Qt.FramelessWindowHint

    property int resizeBorderWidth: 5

    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border.width: 1
        border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
        z: 1000
    }

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
                currentIndex: {
                    if (mainPanel.currentPage === "library") return 1
                    if (mainPanel.currentPage === "visualStyles") return 2
                    if (mainPanel.currentPage === "tasks" || mainPanel.currentPage === "taskDetail") return 3
                    return 0
                }
                onSettingsClicked: {
                    tabBar.settingsActive = true
                    settingsDialog.open()
                }
                onLibraryClicked: {
                    mainPanel.currentPage = "library"
                    mainPanel.mediaLibraryPage.projectId = -1
                    bridge.media.load_files()
                }
                onVisualStylesClicked: {
                    mainPanel.currentPage = "visualStyles"
                    bridge.visualStyles.load_styles()
                }
                onTasksClicked: {
                    mainPanel.currentPage = "tasks"
                }
                onTabChanged: {
                    mainPanel.currentPage = "project"
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
                    }
                }
            }
        }
    }

    Dialogs.SettingsDialog {
        id: settingsDialog
        onClosed: tabBar.settingsActive = false
    }

    Dialogs.ConfirmDialog {
        id: confirmDialog
    }

    Dialogs.AlertDialog {
        id: alertDialog
    }

    Dialogs.UpdateDialog {
        id: updateDialog
    }

    Connections {
        target: bridge
        function onNavigate_requested(projectId, module, entityId) {
            mainPanel.currentPage = "project"
            if (projectId > 0) {
                mainPanel.projectModePage.openDataPage(projectId, module, entityId || "")
            }
        }
    }

    Component.onCompleted: {
        x = (Screen.width - width) / 2
        y = (Screen.height - height) / 2

        bridge.projects.load_projects()

        bridge.update.update_available.connect(function(version, downloadUrl, releaseNotes, htmlUrl) {
            updateDialog.newVersion = version
            updateDialog.downloadUrl = downloadUrl
            updateDialog.releaseNotes = releaseNotes
            updateDialog.htmlUrl = htmlUrl
            updateDialog.open()
        })
    }
}
