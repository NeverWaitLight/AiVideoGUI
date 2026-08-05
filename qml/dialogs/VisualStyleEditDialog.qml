import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs

Dialog {
    id: editDialog
    modal: true
    width: 500
    height: 400
    anchors.centerIn: parent
    padding: 0

    property int editingStyleId: -1
    property bool isCreateMode: true

    title: isCreateMode ? "新建视觉风格" : "编辑视觉风格"

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
                text: editDialog.title
                font.pixelSize: Theme.fontSizeLarge
                font.bold: true
            }
        }
    }

    footer: Item {
        implicitHeight: 64

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
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 80
                    onClicked: editDialog.reject()
                }

                Button {
                    text: "保存"
                    highlighted: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 80
                    enabled: nameField.text.trim() !== ""
                    onClicked: editDialog.accept()
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        Label {
            text: "风格名称"
            font.pixelSize: Theme.fontSizeNormal
        }

        TextField {
            id: nameField
            Layout.fillWidth: true
            placeholderText: "请输入风格名称"
            font.pixelSize: Theme.fontSizeNormal
        }

        Label {
            text: "示例图片"
            font.pixelSize: Theme.fontSizeNormal
            Layout.topMargin: 8
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Qt.rgba(0, 0, 0, 0.05)
            radius: Theme.radiusSmall
            border.width: 1
            border.color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                Image {
                    id: previewImage
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    fillMode: Image.PreserveAspectFit
                    visible: source != ""
                    source: imagePathField.text ? "file:///" + imagePathField.text : ""
                }

                Label {
                    visible: previewImage.source == ""
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "未选择图片"
                    opacity: 0.5
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    TextField {
                        id: imagePathField
                        Layout.fillWidth: true
                        placeholderText: "图片路径"
                        font.pixelSize: Theme.fontSizeSmall
                        readOnly: true
                    }

                    Button {
                        text: "选择"
                        onClicked: fileDialog.open()
                    }
                }
            }
        }
    }

    FileDialog {
        id: fileDialog
        title: "选择示例图片"
        nameFilters: ["图片文件 (*.png *.jpg *.jpeg *.bmp)"]
        onAccepted: {
            var path = fileDialog.selectedFile.toString()
            if (path.startsWith("file:///")) {
                path = path.substring(8)
            }
            imagePathField.text = path
        }
    }

    onAccepted: {
        if (nameField.text.trim() === "") {
            return
        }

        if (isCreateMode) {
            bridge.visualStyles.create_style(
                nameField.text.trim(),
                imagePathField.text
            )
        } else {
            bridge.visualStyles.update_style(
                editingStyleId,
                nameField.text.trim(),
                imagePathField.text
            )
        }
    }

    onRejected: {
        nameField.text = ""
        imagePathField.text = ""
    }

    function open(styleId, styleName, sampleImagePath) {
        editingStyleId = (styleId !== undefined && styleId !== null) ? styleId : -1
        isCreateMode = (editingStyleId === -1)

        if (isCreateMode) {
            nameField.text = ""
            imagePathField.text = ""
        } else {
            nameField.text = styleName
            imagePathField.text = sampleImagePath
        }

        editDialog.open()
    }
}
