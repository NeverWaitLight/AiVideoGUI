import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root

    property int taskId: 0
    property bool isChildTask: false

    signal backClicked()

    onTaskIdChanged: {
        if (taskId > 0)
            resolvePage()
    }

    Component.onCompleted: {
        if (taskId > 0)
            resolvePage()
    }

    function resolvePage() {
        var task = bridge.tasks.get_task_detail(taskId)
        isChildTask = !!(task && task.parent_ids)
        if (isChildTask) {
            childPage.taskId = 0
            childPage.taskId = taskId
        } else {
            parentPage.taskId = 0
            parentPage.taskId = taskId
        }
    }

    function openTask(nextTaskId) {
        if (!nextTaskId || nextTaskId <= 0)
            return
        if (root.taskId === nextTaskId)
            resolvePage()
        else
            root.taskId = nextTaskId
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: root.isChildTask ? 1 : 0

        ParentTaskDetailPage {
            id: parentPage
            onBackClicked: root.backClicked()
            onOpenTask: function(nextTaskId) {
                root.openTask(nextTaskId)
            }
        }

        ChildTaskDetailPage {
            id: childPage
            onBackClicked: root.backClicked()
            onOpenTask: function(nextTaskId) {
                root.openTask(nextTaskId)
            }
        }
    }
}
