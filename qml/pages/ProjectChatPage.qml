import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components" as Comp
import "../dialogs" as Dialogs

Item {
    id: page
    property int projectId: -1
    signal backClicked()

    onProjectIdChanged: {
        if (projectId > 0) {
            bridge.conversations.load_for_project(projectId)
        }
    }

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal

        handle: Rectangle {
            implicitWidth: 1
        }

        // 项目对话列表
        Pane {
            SplitView.preferredWidth: 260
            SplitView.minimumWidth: 200
            padding: 0


            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // 列表头
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 48

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8

                        Label {
                            text: "项目对话"
                            font.pixelSize: Theme.fontSizeMedium
                            font.bold: true
                            Layout.fillWidth: true
                        }

                        Button {
                            text: "+ 新建"
                            flat: true
                            onClicked: bridge.conversations.create_for_project(projectId)
                        }
                    }

                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: 1
                    }
                }

                // 对话列表
                ListView {
                    id: convList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: bridge.conversations.model
                    clip: true
                    spacing: 2


                    Comp.EmptyState {
                        visible: convList.count === 0
                        anchors.centerIn: parent
                        text: "暂无对话"
                        buttonText: "新建对话"
                        onButtonClicked: bridge.conversations.create_for_project(projectId)
                    }
                }
            }
        }

        // 聊天区域
        Comp.ChatArea {
            SplitView.fillWidth: true
        }
    }

    Dialogs.ConfirmDialog { id: confirmDialog }
}
