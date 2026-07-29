import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtMultimedia
import "../components" as Comp

Item {
    id: page
    signal backClicked()
    property int projectId: -1
    property var _playlist: []
    property var _currentVideo: ({})
    property bool _autoAdvance: true

    onProjectIdChanged: {
        if (projectId > 0) {
            bridge.videoPlayer.load_playlist(projectId)
            _playlist = JSON.parse(bridge.videoPlayer.get_playlist_json())
            _updateCurrentVideo()
        }
    }

    Connections {
        target: bridge.videoPlayer
        function onPlaylist_changed() {
            _playlist = JSON.parse(bridge.videoPlayer.get_playlist_json())
        }
        function onCurrent_index_changed() {
            _updateCurrentVideo()
        }
    }

    function _updateCurrentVideo() {
        var json = bridge.videoPlayer.get_current_video()
        _currentVideo = JSON.parse(json)
        if (_currentVideo.filePath) {
            mediaPlayer.source = Qt.url(_currentVideo.filePath)
            mediaPlayer.play()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header
        Comp.PageHeader {
            title: "项目视频播放"
            subtitle: bridge.videoPlayer.playlistCount > 0
                ? (bridge.videoPlayer.currentIndex + 1) + " / " + bridge.videoPlayer.playlistCount
                : ""
            Layout.fillWidth: true
            onBackClicked: {
                mediaPlayer.stop()
                page.backClicked()
            }
        }

        // 视频容器
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true

            VideoOutput {
                id: videoOutput
                anchors.fill: parent
            }

            // 叠加层标签
            Rectangle {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.margins: 16
                width: overlayLabel.implicitWidth + 24
                height: overlayLabel.implicitHeight + 12
                radius: 4
                visible: _currentVideo.label !== undefined

                Label {
                    id: overlayLabel
                    anchors.centerIn: parent
                    text: _currentVideo.label || ""
                    font.pixelSize: Theme.fontSizeMedium
                    font.bold: true
                }
            }

            // 空状态
            Label {
                anchors.centerIn: parent
                text: "没有可播放的分镜视频"
                font.pixelSize: Theme.fontSizeLarge
                visible: _playlist.length === 0
            }
        }

        // ── 时间轴（分段显示）──
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 32

            Row {
                anchors.fill: parent
                anchors.margins: 4
                spacing: 2

                Repeater {
                    model: _playlist
                }
            }
        }

        // ── 控制栏 ──
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60

            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                // 上一个
                Button {
                    flat: true
                    icon.source: "qrc:/icons/outlined/skip_previous.svg"
                    icon.width: 28
                    icon.height: 28
                    enabled: bridge.videoPlayer.currentIndex > 0
                    onClicked: bridge.videoPlayer.play_previous()
                    ToolTip.text: "上一个"
                    ToolTip.visible: hovered
                }

                // 播放/暂停
                Button {
                    flat: true
                    icon.source: mediaPlayer.playbackState === MediaPlayer.PlayingState
                        ? "qrc:/icons/round/pause.svg"
                        : "qrc:/icons/round/play_arrow.svg"
                    icon.width: 32
                    icon.height: 32
                    enabled: _playlist.length > 0
                    onClicked: {
                        if (mediaPlayer.playbackState === MediaPlayer.PlayingState)
                            mediaPlayer.pause()
                        else
                            mediaPlayer.play()
                    }
                }

                // 下一个
                Button {
                    flat: true
                    icon.source: "qrc:/icons/outlined/skip_next.svg"
                    icon.width: 28
                    icon.height: 28
                    enabled: bridge.videoPlayer.currentIndex < _playlist.length - 1
                    onClicked: bridge.videoPlayer.play_next()
                    ToolTip.text: "下一个"
                    ToolTip.visible: hovered
                }

                // 当前时间
                Label {
                    text: _formatTime(mediaPlayer.position)
                    font.pixelSize: Theme.fontSizeSmall
                    Layout.preferredWidth: 40
                }

                // 进度条
                Slider {
                    id: positionSlider
                    Layout.fillWidth: true
                    from: 0
                    to: mediaPlayer.duration > 0 ? mediaPlayer.duration : 1
                    value: mediaPlayer.position
                    enabled: mediaPlayer.duration > 0
                    onMoved: mediaPlayer.position = value
                }

                // 总时长
                Label {
                    text: _formatTime(mediaPlayer.duration)
                    font.pixelSize: Theme.fontSizeSmall
                    Layout.preferredWidth: 40
                }

                // 音量
                Button {
                    flat: true
                    icon.source: audioOutput.muted
                        ? "qrc:/icons/outlined/volume_off.svg"
                        : "qrc:/icons/outlined/volume_up.svg"
                    icon.width: 24
                    icon.height: 24
                    onClicked: audioOutput.muted = !audioOutput.muted
                }

                Slider {
                    id: volumeSlider
                    from: 0; to: 1.0; value: audioOutput.volume
                    implicitWidth: 80
                    onMoved: audioOutput.volume = value
                }
            }
        }
    }

    // 播放器
    MediaPlayer {
        id: mediaPlayer
        videoOutput: videoOutput
        audioOutput: AudioOutput { id: audioOutput }

        onPlaybackStateChanged: function(state) {
            // 自动播放下一个
        }

        onMediaStatusChanged: function(status) {
            if (status === MediaPlayer.EndOfMedia && _autoAdvance) {
                if (bridge.videoPlayer.currentIndex < _playlist.length - 1) {
                    bridge.videoPlayer.play_next()
                }
            }
        }
    }

    // 页面隐藏时暂停
    Component.onDestruction: {
        mediaPlayer.stop()
    }

    function _formatTime(ms) {
        var s = Math.floor(ms / 1000)
        var m = Math.floor(s / 60)
        s = s % 60
        return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s
    }

    function _segmentColor(index) {
        var colors = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#F44336", "#00BCD4", "#795548", "#607D8B"]
        return colors[index % colors.length]
    }
}
