import QtQuick 2.15

Canvas {
    id: spinner
    width: 36
    height: 36

    property real angle: 0
    property color strokeColor: "#000000"

    Timer {
        interval: 40
        running: spinner.visible
        repeat: true
        onTriggered: {
            spinner.angle = (spinner.angle + 30) % 360
            spinner.requestPaint()
        }
    }

    onPaint: {
        var ctx = getContext("2d")
        ctx.clearRect(0, 0, width, height)
        ctx.lineWidth = 3
        ctx.lineCap = "round"
        ctx.strokeStyle = spinner.strokeColor.toString()
        ctx.beginPath()
        var cx = width / 2
        var cy = height / 2
        var r = Math.min(cx, cy) - 4
        var startAngle = (angle - 90) * Math.PI / 180
        var endAngle = (angle + 180 - 90) * Math.PI / 180
        ctx.arc(cx, cy, r, startAngle, endAngle)
        ctx.stroke()
    }
}
