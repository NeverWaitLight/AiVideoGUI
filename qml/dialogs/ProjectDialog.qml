import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs as QtDialogs
import "../components" as Comp

Dialog {
    id: projectDialog
    modal: true
    width: 450
    height: 400
    anchors.centerIn: parent
    padding: 0

    property bool isEdit: false
    property int editProjectId: 0
    property string coverImagePath: ""

    title: isEdit ? "编辑项目" : "新建项目"

    background: Rectangle {
        color: Theme.bgChat
        radius: Theme.cardRadius
        border.color: Theme.border
        border.width: 1
    }

    header: Rectangle {
        height: Theme.headerHeight
        color: Theme.bgSidebar
        border.color: Theme.border
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Label {
                text: projectDialog.title
                font.pixelSize: Theme.fontSizeTitle
                font.bold: true
                color: Theme.textAI
                Layout.fillWidth: true
            }
        }
    }

    footer: Rectangle {
        height: 64
        color: Theme.bgSidebar
        border.color: Theme.border
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Item { Layout.fillWidth: true }

            Button {
                text: "取消"
                implicitHeight: 32
                implicitWidth: 80
                background: Rectangle {
                    radius: Theme.borderRadius
                    color: parent.hovered ? Theme.bubbleAI : Theme.bgChat
                    border.color: Theme.border
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: Theme.fontSizeNormal
                    color: Theme.textAI
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: projectDialog.reject()
            }

            Button {
                text: "确定"
                implicitHeight: 32
                implicitWidth: 80
                background: Rectangle {
                    radius: Theme.borderRadius
                    color: parent.hovered ? Theme.primaryHover : Theme.primary
                }
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: Theme.fontSizeNormal
                    color: Theme.textUser
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
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

    component StyledComboBox: ComboBox {
        id: control

        background: Rectangle {
            implicitHeight: 32
            radius: Theme.borderRadius
            color: control.hovered ? Theme.bubbleAI : Theme.bgChat
            border.color: Theme.border
            border.width: 1
        }

        contentItem: Text {
            leftPadding: 10
            rightPadding: 28
            text: control.displayText
            font.pixelSize: Theme.fontSizeMedium
            color: Theme.textAI
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        indicator: Canvas {
            x: control.width - width - 10
            y: (control.height - height) / 2
            width: 8
            height: 5
            contextType: "2d"
            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.strokeStyle = Theme.textSecondary
                ctx.lineWidth = 1.5
                ctx.beginPath()
                ctx.moveTo(0, 0)
                ctx.lineTo(width / 2, height)
                ctx.lineTo(width, 0)
                ctx.stroke()
            }
        }

        popup: Popup {
            y: control.height + 2
            width: control.width
            implicitHeight: contentItem.implicitHeight + 8
            padding: 4

            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: control.popup.visible ? control.delegateModel : null
                currentIndex: control.highlightedIndex
                ScrollIndicator.vertical: ScrollIndicator {}
            }

            background: Rectangle {
                radius: Theme.radiusSmall
                color: Theme.bgChat
                border.color: Theme.border
                border.width: 1
            }
        }

        delegate: ItemDelegate {
            width: ListView.view.width
            height: 32
            highlighted: control.highlightedIndex === index

            contentItem: Text {
                text: modelData
                font.pixelSize: Theme.fontSizeMedium
                color: Theme.textAI
                verticalAlignment: Text.AlignVCenter
                leftPadding: 10
            }

            background: Rectangle {
                color: parent.highlighted ? Theme.bgTag : "transparent"
                radius: Theme.radiusSmall
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        // 项目名称
        RowLayout {
            spacing: 12
            Label {
                text: "项目名称:"
                Layout.preferredWidth: 80
                font.pixelSize: Theme.fontSizeMedium
                color: Theme.textAI
            }
            Comp.AppTextField {
                id: nameField
                Layout.fillWidth: true
                placeholderText: "输入项目名称"
            }
        }

        // 封面图
        RowLayout {
            spacing: 12
            Label {
                text: "封面图:"
                Layout.preferredWidth: 80
                font.pixelSize: Theme.fontSizeMedium
                color: Theme.textAI
            }
            Label {
                text: coverImagePath ? coverImagePath.split("/").pop() : "未选择"
                color: coverImagePath ? Theme.textAI : Theme.textSecondary
                font.pixelSize: Theme.fontSizeSmall
                elide: Text.ElideMiddle
                Layout.fillWidth: true
            }
            Button {
                text: "选择图片"
                implicitHeight: 28
                background: Rectangle {
                    radius: Theme.borderRadius
                    color: parent.hovered ? Theme.bubbleAI : Theme.bgChat
                    border.color: Theme.border
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: Theme.fontSizeSmall
                    color: Theme.textAI
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: coverFileDialog.open()
            }
            Button {
                text: "清除"
                implicitHeight: 28
                visible: coverImagePath !== ""
                background: Rectangle {
                    radius: Theme.borderRadius
                    color: parent.hovered ? Theme.bubbleAI : Theme.bgChat
                    border.color: Theme.border
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: Theme.fontSizeSmall
                    color: Theme.textAI
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: coverImagePath = ""
            }
        }

        // 画面比例
        RowLayout {
            spacing: 12
            Label {
                text: "画面比例:"
                Layout.preferredWidth: 80
                font.pixelSize: Theme.fontSizeMedium
                color: Theme.textAI
            }
            StyledComboBox {
                id: ratioCombo
                model: ["16:9", "9:16", "1:1", "4:3", "3:4"]
                Layout.fillWidth: true
            }
        }

        // 分辨率
        RowLayout {
            spacing: 12
            Label {
                text: "分辨率:"
                Layout.preferredWidth: 80
                font.pixelSize: Theme.fontSizeMedium
                color: Theme.textAI
            }
            StyledComboBox {
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
