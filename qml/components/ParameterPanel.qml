import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Pane {
    id: panel
    implicitHeight: layout.implicitHeight + 16

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

    ColumnLayout {
        id: layout
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        RowLayout {
            spacing: 10

            Label { text: "比例:"; font.pixelSize: Theme.fontSizeSmall }
            ComboBox {
                id: ratioCombo
                model: ["16:9", "9:16", "1:1", "4:3", "3:4"]
                onCurrentTextChanged: panel.ratio = currentText
            }

            Label { text: "分辨率:"; font.pixelSize: Theme.fontSizeSmall }
            ComboBox {
                id: resCombo
                model: ["720P", "1080P"]
                onCurrentTextChanged: panel.resolution = currentText
            }

            Label { text: "时长:"; font.pixelSize: Theme.fontSizeSmall }
            ComboBox {
                id: durationCombo
                model: ["5秒", "10秒", "15秒"]
                onCurrentTextChanged: {
                    var map = {"5秒": 5, "10秒": 10, "15秒": 15}
                    panel.duration = map[currentText] || 5
                }
            }

            Label { text: "自动优化:"; font.pixelSize: Theme.fontSizeSmall }
            Switch {
                id: promptExtendSwitch
                checked: true
                onCheckedChanged: panel.promptExtend = checked
            }

            Label { text: "水印:"; font.pixelSize: Theme.fontSizeSmall }
            Switch {
                id: watermarkSwitch
                checked: false
                onCheckedChanged: panel.watermark = checked
            }

            Item { Layout.fillWidth: true }
        }
    }
}
