import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs as QtDialogs
import "../components" as Comp

Dialog {
    id: projectDialog
    modal: true
    width: 480
    height: 440
    anchors.centerIn: parent
    padding: 0

    property bool isEdit: false
    property int editProjectId: 0
    property string coverImagePath: ""

    title: ""

    background: Rectangle {
        color: Material.dialogColor
        radius: Theme.radiusMedium
    }

    header: Item {
        implicitHeight: 56

        Rectangle {
            anchors.fill: parent
            color: "transparent"

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
            }

            Label {
                anchors.left: parent.left
                anchors.leftMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                text: projectDialog.isEdit ? "编辑" : "新建"
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
            }
        }
    }

    footer: Item {
        implicitHeight: 72

        Rectangle {
            anchors.fill: parent
            color: "transparent"

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
            }

            RowLayout {
                anchors.right: parent.right
                anchors.rightMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                spacing: 12

                Button {
                    text: "取消"
                    flat: true
                    implicitHeight: 36
                    implicitWidth: 80
                    onClicked: projectDialog.reject()
                }

                Button {
                    text: "确定"
                    highlighted: true
                    implicitHeight: 36
                    implicitWidth: 80
                    onClicked: {
                        if (isEdit) {
                            bridge.projects.update_project(editProjectId, nameField.text, resCombo.currentText, ratioCombo.currentText, coverImagePath)
                        } else {
                            bridge.projects.create_project(nameField.text, resCombo.currentText, ratioCombo.currentText, coverImagePath)
                        }
                        projectDialog.accept()
                    }
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 20

        // 项目名称
        ColumnLayout {
            spacing: 8
            Layout.fillWidth: true

            Label {
                text: "项目名称"
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.7
            }
            Comp.AppTextField {
                id: nameField
                Layout.fillWidth: true
                placeholderText: "输入项目名称"
            }
        }

        // 封面图
        ColumnLayout {
            spacing: 8
            Layout.fillWidth: true

            Label {
                text: "封面图"
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.7
            }

            RowLayout {
                spacing: 8
                Layout.fillWidth: true

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    radius: Theme.radiusSmall
                    color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.05)
                    border.width: 1
                    border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)

                    Label {
                        anchors.left: parent.left
                        anchors.leftMargin: 12
                        anchors.verticalCenter: parent.verticalCenter
                        text: coverImagePath ? coverImagePath.split("/").pop() : "未选择图片"
                        font.pixelSize: Theme.fontSizeSmall
                        opacity: coverImagePath ? 1.0 : 0.5
                        elide: Text.ElideMiddle
                        width: parent.width - 24
                    }
                }

                Button {
                    text: "选择"
                    flat: true
                    implicitHeight: 36
                    implicitWidth: 72
                    onClicked: coverFileDialog.open()
                }

                Button {
                    text: "清除"
                    flat: true
                    implicitHeight: 36
                    implicitWidth: 72
                    visible: coverImagePath !== ""
                    onClicked: coverImagePath = ""
                }
            }
        }

        // 画面比例
        ColumnLayout {
            spacing: 8
            Layout.fillWidth: true

            Label {
                text: "画面比例"
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.7
            }
            ComboBox {
                id: ratioCombo
                model: ["16:9", "9:16", "1:1", "4:3", "3:4"]
                Layout.fillWidth: true
            }
        }

        // 分辨率
        ColumnLayout {
            spacing: 8
            Layout.fillWidth: true

            Label {
                text: "分辨率"
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.7
            }
            ComboBox {
                id: resCombo
                model: ["480P", "720P", "1080P", "2K", "4K"]
                currentIndex: 1
                Layout.fillWidth: true
            }
        }

        Item { Layout.fillHeight: true }
    }

    function openForCreate() {
        isEdit = false
        editProjectId = 0
        nameField.text = ""
        coverImagePath = ""
        resCombo.currentIndex = 1
        ratioCombo.currentIndex = 0
        open()
    }

    function openForEdit(projectId) {
        isEdit = true
        editProjectId = projectId
        var info = JSON.parse(bridge.projects.get_project_info(projectId))
        nameField.text = info.name || ""
        coverImagePath = info.coverImage || ""
        // 设置宽高比
        var ratioIdx = ratioCombo.model.indexOf(info.aspectRatio)
        if (ratioIdx >= 0) ratioCombo.currentIndex = ratioIdx
        // 设置分辨率
        var resIdx = resCombo.model.indexOf(info.resolution)
        if (resIdx >= 0) resCombo.currentIndex = resIdx
        open()
    }

    // 封面图选择对话框
    QtDialogs.FileDialog {
        id: coverFileDialog
        title: "选择封面图片"
        fileMode: QtDialogs.FileDialog.OpenFile
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.bmp *.svg)", "所有文件 (*)"]
        onAccepted: {
            var p = selectedFile.toString()
            if (p.startsWith("file:///")) p = p.substring(8)
            coverImagePath = p
        }
    }
}
