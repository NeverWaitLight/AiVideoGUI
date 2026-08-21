import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import "../pages" as Pages

Control {
    id: mainPanel
    padding: 0

    property string currentPage: "project"

    background: Rectangle {
        color: "transparent"
    }

    contentItem: StackLayout {
        currentIndex: {
            if (mainPanel.currentPage === "project") return 0
            if (mainPanel.currentPage === "library") return 1
            if (mainPanel.currentPage === "visualStyles") return 2
            if (mainPanel.currentPage === "tasks") return 3
            if (mainPanel.currentPage === "taskDetail") return 4
            return 0
        }

        Pages.ProjectModePage {
            id: projectModePage
            onOpenTaskDetail: function(taskId) {
                mainPanel.openTaskDetail(taskId)
            }
        }

        Pages.MediaLibraryPage {
            id: globalMediaPage
            onBackClicked: {
                mainPanel.currentPage = "project"
            }
        }

        Pages.VisualStyleListPage {
            id: visualStylePage
            onBackClicked: {
                mainPanel.currentPage = "project"
            }
        }

        Pages.TaskListPage {
            id: taskListPage
            onTaskClicked: function(taskId) {
                taskDetailPage.taskId = taskId
                mainPanel.currentPage = "taskDetail"
            }
        }

        Pages.TaskDetailPage {
            id: taskDetailPage
            onBackClicked: {
                mainPanel.currentPage = "tasks"
            }
        }
    }

    readonly property alias projectModePage: projectModePage
    readonly property alias mediaLibraryPage: globalMediaPage
    readonly property alias visualStylePage: visualStylePage
    readonly property alias taskListPage: taskListPage
    readonly property alias taskDetailPage: taskDetailPage

    function openTaskDetail(taskId) {
        if (!taskId || taskId <= 0)
            return
        taskDetailPage.taskId = taskId
        mainPanel.currentPage = "taskDetail"
    }
}
