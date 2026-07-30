import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Pane {
    id: card
    padding: 0

    background: Rectangle {
        radius: Theme.cardRadius
        color: Qt.rgba(0, 0, 0, 0.08)  // 比透明背景稍深一点
        border.width: 0  // 无边框
    }

    property int projectId: 0
    property string projectName: ""
    property string resolution: ""
    property string aspectRatio: ""
    property string coverPath: ""
    property string createdAt: ""
    property bool isGeneratingCover: false  // 是否正在生成封面

    signal clicked()
    signal editClicked(int projectId)
    signal deleteClicked(int projectId)

    // 判断是否为竖屏视频 (9:16)
    readonly property bool isVerticalVideo: aspectRatio === "9:16"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        // 上部容器：根据比例切换布局（固定高度）
        Loader {
            Layout.fillWidth: true
            Layout.preferredHeight: 208  // 增加上部容器高度
            sourceComponent: isVerticalVideo ? verticalVideoLayout : horizontalVideoLayout
        }

        // 下部容器：操作按钮（固定高度）
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 40  // 减小下部容器高度
            spacing: 8

            Button {
                Layout.fillWidth: true
                Layout.fillHeight: true
                flat: true
                text: "编辑"
                icon.source: "qrc:/resources/icons/edit.svg"
                icon.width: 20
                icon.height: 20
                onClicked: card.editClicked(card.projectId)

                background: Rectangle {
                    radius: Theme.radiusSmall
                    color: parent.hovered
                        ? Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.15)
                        : "transparent"
                }
            }

            Button {
                Layout.fillWidth: true
                Layout.fillHeight: true
                flat: true
                text: "删除"
                icon.source: "qrc:/resources/icons/delete.svg"
                icon.width: 20
                icon.height: 20
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

    // 竖屏视频布局（9:16）：左右布局
    Component {
        id: verticalVideoLayout
        RowLayout {
            spacing: 12

            // 左侧：封面图
            Rectangle {
                Layout.preferredWidth: 80
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

                // 加载动画
                BusyIndicator {
                    anchors.centerIn: parent
                    width: 40
                    height: 40
                    running: card.isGeneratingCover
                    visible: card.isGeneratingCover
                }

                // 加载提示文字
                Label {
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: 35
                    text: "生成中..."
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                    visible: card.isGeneratingCover
                }
            }

            // 右侧：信息区域
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 6

                Label {
                    text: projectName
                    font.pixelSize: Theme.fontSizeMedium
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                Label {
                    text: aspectRatio
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                    Layout.fillWidth: true
                }

                Label {
                    text: resolution
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                    Layout.fillWidth: true
                }

                Label {
                    text: createdAt
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.5
                    Layout.fillWidth: true
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    // 横屏视频布局：上下布局
    Component {
        id: horizontalVideoLayout
        ColumnLayout {
            spacing: 8

            // 上侧：封面图
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 120
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
                    sourceSize.width: 48
                    sourceSize.height: 48
                    visible: !coverPath && !card.isGeneratingCover
                }

                // 加载动画
                BusyIndicator {
                    anchors.centerIn: parent
                    width: 60
                    height: 60
                    running: card.isGeneratingCover
                    visible: card.isGeneratingCover
                }

                // 加载提示文字
                Label {
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: 50
                    text: "生成封面中..."
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                    visible: card.isGeneratingCover
                }
            }

            // 下侧：信息区域
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                Label {
                    text: projectName
                    font.pixelSize: Theme.fontSizeMedium
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                Label {
                    text: aspectRatio
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                    Layout.fillWidth: true
                }

                Label {
                    text: resolution
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.7
                    Layout.fillWidth: true
                }

                Label {
                    text: createdAt
                    font.pixelSize: Theme.fontSizeSmall
                    opacity: 0.5
                    Layout.fillWidth: true
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
