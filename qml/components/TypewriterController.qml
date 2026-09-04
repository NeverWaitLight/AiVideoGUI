import QtQuick 2.15

Item {
    id: root
    width: 0
    height: 0
    visible: false

    property var target: null
    property string pending: ""
    readonly property bool active: pending.length > 0
    property int interval: 16

    signal drained()
    signal textUpdated()

    function beginReplace() {
        pending = ""
        if (target)
            target.text = ""
        textUpdated()
    }

    function feed(delta) {
        if (!delta)
            return
        pending += delta
    }

    function flush() {
        if (target && pending.length > 0)
            target.text += pending
        pending = ""
        textUpdated()
        drained()
    }

    function stop() {
        pending = ""
    }

    function _charsThisTick() {
        if (pending.length > 80)
            return 6
        if (pending.length > 20)
            return 3
        return 1
    }

    function _tick() {
        if (!target || pending.length === 0)
            return
        var n = _charsThisTick()
        if (n > pending.length)
            n = pending.length
        target.text += pending.substring(0, n)
        pending = pending.substring(n)
        textUpdated()
        if (pending.length === 0)
            drained()
    }

    Timer {
        interval: root.interval
        running: root.pending.length > 0
        repeat: true
        onTriggered: root._tick()
    }
}
