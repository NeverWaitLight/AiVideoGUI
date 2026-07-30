import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Pane {
    id: card
    padding: 0

    background: Rectangle {
        radius: Theme.cardRadius
        color: Qt.rgba(0, 0, 0, 0.08)
        border.width: 0
    }

    property int projectId: 0
    property string projectName: ""
    property string resolution: ""
    property string aspectRatio: ""
    property string coverPath: ""
    property string createdAt: ""
    property bool isGeneratingCover: false

    signal clicked()
    signal editClicked(int projectId)
    signal deleteClicked(int projectId)

    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        // 左侧：封面图（背景透明，至少占卡片一半宽度）
        Rectangle {
            Layout.minimumWidth: Math.max(0, (card.width - 24 - 12) * 0.5)
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: Theme.radiusMedium
            clip: true
            color: "transparent"

            Image {
                anchors.fill: parent
                source: coverPath ? "file:///" + coverPath : ""
                fillMode: Image.PreserveAspectFit
                visible: source !== "" && !card.isGeneratingCover
            }

            Image {
                anchors.centerIn: parent
                source: "qrc:/resources/icons/movie.svg"
                sourceSize.width: 32
                sourceSize.height: 32
                visible: !coverPath && !card.isGeneratingCover
            }

            BusyIndicator {
                anchors.centerIn: parent
                width: 40
                height: 40
                running: card.isGeneratingCover
                visible: card.isGeneratingCover
            }

            Label {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: 35
                text: "生成中..."
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.7
                visible: card.isGeneratingCover
            }
        }

        // 右侧：信息 + 操作按钮
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 6

            // 项目名
            Label {
                text: projectName
                font.pixelSize: Theme.fontSizeMedium
                font.bold: true
                wrapMode: Text.Wrap
                maximumLineCount: 3
                Layout.fillWidth: true
            }

            // 分辨率
            Label {
                text: resolution
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.7
                Layout.fillWidth: true
            }

            // 视频比例
            Label {
                text: aspectRatio
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.7
                Layout.fillWidth: true
            }

            // 创建时间
            Label {
                text: createdAt
                font.pixelSize: Theme.fontSizeSmall
                opacity: 0.5
                Layout.fillWidth: true
            }

            Item { Layout.fillHeight: true }

            // 编辑按钮
            Button {
                Layout.preferredHeight: 36
                Layout.fillWidth: true
                flat: true
                text: "编辑"
                icon.source: "qrc:/resources/icons/edit.svg"
                icon.width: 18
                icon.height: 18
                topPadding: 6
                bottomPadding: 6
                leftPadding: 8
                rightPadding: 8
                onClicked: card.editClicked(card.projectId)

                background: Rectangle {
                    radius: Theme.radiusSmall
                    color: parent.hovered
                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.15)
                        : "transparent"
                }
            }

            // 删除按钮
            Button {
                Layout.preferredHeight: 36
                Layout.fillWidth: true
                flat: true
                text: "删除"
                icon.source: "qrc:/resources/icons/delete.svg"
                icon.width: 18
                icon.height: 18
                topPadding: 6
                bottomPadding: 6
                leftPadding: 8
                rightPadding: 8
                onClicked: card.deleteClicked(card.projectId)

                background: Rectangle {
                    radius: Theme.radiusSmall
                    color: parent.hovered
                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.15)
                        : "transparent"
                }
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        z: -1
        onClicked: card.clicked()
    }

    property bool isHovered: hoverHandler.hovered
    HoverHandler { id: hoverHandler }
}
