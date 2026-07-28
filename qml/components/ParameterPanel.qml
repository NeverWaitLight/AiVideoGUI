import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: panel
    height: layout.implicitHeight + 16
    color: "transparent"

    property string provider: "dashscope"
    property string modelName: "wan2.7-t2v"
    property string resolution: "720P"
    property string ratio: "16:9"
    property int duration: 5
    property bool promptExtend: true
    property bool watermark: false

    function getParams() {
        return {
            "resolution": resolution,
            "ratio": ratio,
            "duration": duration,
            "prompt_extend": promptExtend,
            "watermark": watermark
        }
    }

    component StyledComboBox: ComboBox {
        id: control

        background: Rectangle {
            implicitWidth: 80
            implicitHeight: 28
            radius: Theme.radiusSmall
            color: control.hovered ? Theme.bubbleAI : Theme.bgChat
            border.color: Theme.border
            border.width: 1
        }

        contentItem: Text {
            leftPadding: 8
            rightPadding: 24
            text: control.displayText
            font.pixelSize: Theme.fontSizeSmall
            color: Theme.textAI
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        indicator: Canvas {
            x: control.width - width - 8
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
            height: 28
            highlighted: control.highlightedIndex === index

            contentItem: Text {
                text: modelData
                font.pixelSize: Theme.fontSizeSmall
                color: Theme.textAI
                verticalAlignment: Text.AlignVCenter
                leftPadding: 8
            }

            background: Rectangle {
                color: parent.highlighted ? Theme.bgTag : "transparent"
                radius: Theme.radiusSmall
            }
        }
    }

    component StyledSwitch: Switch {
        id: sw

        indicator: Rectangle {
            implicitWidth: 36
            implicitHeight: 20
            x: sw.leftPadding
            y: (sw.height - height) / 2
            radius: 10
            color: sw.checked ? Theme.primary : Theme.switchOff
            border.color: sw.checked ? Theme.primary : Theme.border
            border.width: 1

            Behavior on color { ColorAnimation { duration: 150 } }

            Rectangle {
                width: 16
                height: 16
                radius: 8
                color: Theme.bgChat
                border.color: Theme.bgPlaceholder
                border.width: 1
                anchors.verticalCenter: parent.verticalCenter
                x: sw.checked ? parent.width - width - 2 : 2

                Behavior on x { NumberAnimation { duration: 150; easing.type: Easing.InOutQuad } }
            }
        }
    }

    ColumnLayout {
        id: layout
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        RowLayout {
            spacing: 10

            Label { text: "比例:"; font.pixelSize: Theme.fontSizeSmall; color: Theme.textSecondary }
            StyledComboBox {
                id: ratioCombo
                model: ["16:9", "9:16", "1:1", "4:3", "3:4"]
                onCurrentTextChanged: panel.ratio = currentText
            }

            Label { text: "分辨率:"; font.pixelSize: Theme.fontSizeSmall; color: Theme.textSecondary }
            StyledComboBox {
                id: resCombo
                model: ["720P", "1080P"]
                onCurrentTextChanged: panel.resolution = currentText
            }

            Label { text: "时长:"; font.pixelSize: Theme.fontSizeSmall; color: Theme.textSecondary }
            StyledComboBox {
                id: durationCombo
                model: ["5秒", "10秒", "15秒"]
                onCurrentTextChanged: {
                    var map = {"5秒": 5, "10秒": 10, "15秒": 15}
                    panel.duration = map[currentText] || 5
                }
            }

            Label { text: "自动优化:"; font.pixelSize: Theme.fontSizeSmall; color: Theme.textSecondary }
            StyledSwitch {
                id: promptExtendSwitch
                checked: true
                onCheckedChanged: panel.promptExtend = checked
            }

            Label { text: "水印:"; font.pixelSize: Theme.fontSizeSmall; color: Theme.textSecondary }
            StyledSwitch {
                id: watermarkSwitch
                checked: false
                onCheckedChanged: panel.watermark = checked
            }

            Item { Layout.fillWidth: true }
        }
    }
}
