import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs as QtDialogs
import "../components" as Comp

Dialog {
    id: projectDialog
    modal: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    width: 450
    height: 380
    anchors.centerIn: parent

    property bool isEdit: false
    property int editProjectId: 0
    property string coverImagePath: ""

    title: isEdit ? "编辑项目" : "新建项目"

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        // 项目名称
        RowLayout {
            Label { text: "项目名称:"; Layout.preferredWidth: 80 }
            Comp.AppTextField { id: nameField; Layout.fillWidth: true; placeholderText: "输入项目名称" }
        }

        // 封面图
        RowLayout {
            Label { text: "封面图:"; Layout.preferredWidth: 80 }
            Label {
                text: coverImagePath ? coverImagePath.split("/").pop() : "未选择"
                color: coverImagePath ? Theme.textAI : "#999"
                font.pixelSize: Theme.fontSizeSmall
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }
            Button {
                text: "选择图片"
                onClicked: coverFileDialog.open()
            }
            Button {
                text: "清除"
                visible: coverImagePath !== ""
                onClicked: coverImagePath = ""
            }
        }

        // 画面比例
        RowLayout {
            Label { text: "画面比例:"; Layout.preferredWidth: 80 }
            ComboBox {
                id: ratioCombo
                model: ["16:9", "9:16", "1:1", "4:3", "3:4"]
                Layout.fillWidth: true
            }
        }

        // 分辨率
        RowLayout {
            Label { text: "分辨率:"; Layout.preferredWidth: 80 }
            ComboBox {
                id: resCombo
                model: ["480P", "720P", "1080P", "2K", "4K"]
                currentIndex: 1
                Layout.fillWidth: true
            }
        }

        Item { Layout.fillHeight: true }
    }

    onAccepted: {
        if (isEdit) {
            bridge.projects.update_project(editProjectId, nameField.text, resCombo.currentText, ratioCombo.currentText, coverImagePath)
        } else {
            bridge.projects.create_project(nameField.text, resCombo.currentText, ratioCombo.currentText, coverImagePath)
        }
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
