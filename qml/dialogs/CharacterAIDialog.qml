import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: root
    modal: true
    width: 480
    height: 360
    anchors.centerIn: parent
    padding: 0
    closePolicy: Popup.NoAutoClose

    property int currentTab: 0
    property bool isWorking: false

    signal refineRequested(string userInput)
    signal generateDesignRequested(string userInput)

    title: ""

    background: Rectangle {
        color: Material.dialogColor
        radius: Theme.radiusMedium
    }

    header: Item {
        implicitHeight: 100

        Rectangle {
            anchors.fill: parent
            color: "transparent"

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                anchors.topMargin: 12
                spacing: 0

                Label {
                    text: "Ai"
                    font.pixelSize: Theme.fontSizeLarge
                    font.bold: true
                    Layout.bottomMargin: 8
                }

                TabBar {
                    id: tabBar
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    currentIndex: root.currentTab

                    background: Rectangle {
                        color: "transparent"
                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            height: 1
                            color: Qt.rgba(Material.foreground.r, Material.foreground.g, Material.foreground.b, 0.12)
                        }
                    }

                    TabButton {
                        text: "修改描述"
                        font.pixelSize: Theme.fontSizeSmall
                        topPadding: 6
                        bottomPadding: 6
                        leftPadding: 16
                        rightPadding: 16
                        background: Item {
                            Rectangle {
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.bottom: parent.bottom
                                height: 2
                                color: tabBar.currentIndex === 0 ? Material.accent : "transparent"
                            }
                        }
                    }

                    TabButton {
                        text: "生成设计图"
                        font.pixelSize: Theme.fontSizeSmall
                        topPadding: 6
                        bottomPadding: 6
                        leftPadding: 16
                        rightPadding: 16
                        background: Item {
                            Rectangle {
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.bottom: parent.bottom
                                height: 2
                                color: tabBar.currentIndex === 1 ? Material.accent : "transparent"
                            }
                        }
                    }

                    onCurrentIndexChanged: root.currentTab = currentIndex
                }
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
                    enabled: !root.isWorking
                    onClicked: root.close()
                }

                Button {
                    id: sendBtn
                    text: root.isWorking ? "处理中..." : "发送"
                    highlighted: true
                    Layout.preferredHeight: 40
                    Layout.preferredWidth: 100
                    enabled: !root.isWorking && _currentInput().length > 0
                    onClicked: {
                        var input = _currentInput()
                        if (input.length === 0) return
                        root.isWorking = true
                        if (root.currentTab === 0) {
                            root.refineRequested(input)
                        } else {
                            root.generateDesignRequested(input)
                        }
                    }
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        spacing: 8

        Label {
            text: root.currentTab === 0 ? "描述修改要求" : "补充设计要求（可选）"
            font.pixelSize: Theme.fontSizeSmall
            opacity: 0.7
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: root.currentTab

            ScrollView {
                contentWidth: availableWidth
                clip: true
                TextArea {
                    id: refineInput
                    placeholderText: "例如：增加身高描述、改为古装造型、添加武器..."
                    wrapMode: TextArea.Wrap
                    font.pixelSize: Theme.fontSizeNormal
                    selectByMouse: true
                    enabled: !root.isWorking
                }
            }

            ScrollView {
                contentWidth: availableWidth
                clip: true
                TextArea {
                    id: designInput
                    placeholderText: "例如：赛博朋克风格、Q版形象、穿运动装..."
                    wrapMode: TextArea.Wrap
                    font.pixelSize: Theme.fontSizeNormal
                    selectByMouse: true
                    enabled: !root.isWorking
                }
            }
        }
    }

    onOpened: {
        refineInput.text = ""
        designInput.text = ""
        root.isWorking = false
        root.currentTab = 0
        tabBar.currentIndex = 0
        refineInput.forceActiveFocus()
    }

    function finishWork() {
        root.isWorking = false
        root.close()
    }

    function _currentInput() {
        if (root.currentTab === 0) {
            return refineInput.text.trim()
        }
        return designInput.text.trim()
    }
}
