"""视频播放器页面：按场次-镜头顺序自动拼接播放分镜视频。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QStackedLayout,
)
from qfluentwidgets import ToolButton, FluentIcon, TitleLabel, PushButton

if TYPE_CHECKING:
    from models.data_models import MediaFile
    from storage.database import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class PlaylistItem:
    """播放列表项。"""
    scene_number: int      # 场次号
    shot_number: int       # 镜头号
    sequence: int          # 生成次数（序号）
    media_file: MediaFile  # 素材文件对象


class VideoPlayerPage(QWidget):
    """视频播放器页面。"""

    back_clicked = pyqtSignal()

    def __init__(self, db: DatabaseManager, parent: QWidget | None = None):
        super().__init__(parent)
        self._db = db
        self._playlist: list[PlaylistItem] = []
        self._current_index = 0
        self._is_slider_pressed = False

        # 初始化播放器组件
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        self._video_widget = QVideoWidget()
        self._player.setVideoOutput(self._video_widget)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """构建 UI 布局。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Header
        header = self._create_header()
        layout.addWidget(header)

        # 2. Video Container with Overlay
        video_container = self._create_video_container()
        layout.addWidget(video_container, stretch=1)

        # 3. Control Bar
        control_bar = self._create_control_bar()
        layout.addWidget(control_bar)

    def _create_header(self) -> QWidget:
        """创建顶部栏。"""
        header = QWidget()
        header.setStyleSheet("background: white; border-bottom: 1px solid #E0E0E0;")
        header.setFixedHeight(70)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(16)

        # 返回按钮
        self.back_btn = ToolButton(FluentIcon.RETURN)
        self.back_btn.setFixedSize(40, 40)
        self.back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(self.back_btn)

        # 标题
        title_label = TitleLabel("项目视频播放")
        layout.addWidget(title_label)

        layout.addStretch()

        # 播放列表信息标签
        self.playlist_info_label = QLabel("0 / 0")
        self.playlist_info_label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(self.playlist_info_label)

        return header

    def _create_video_container(self) -> QWidget:
        """创建视频容器（带叠加层）。"""
        container = QWidget()
        container.setStyleSheet("background: black;")

        # 使用 StackedLayout 实现叠加
        stack = QStackedLayout(container)
        stack.setStackingMode(QStackedLayout.StackingMode.StackAll)

        # 底层：视频控件
        stack.addWidget(self._video_widget)

        # 顶层：叠加层容器
        overlay_widget = QWidget()
        overlay_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        overlay_layout = QVBoxLayout(overlay_widget)
        overlay_layout.setContentsMargins(16, 16, 16, 16)

        # 左上角文本标签
        self.overlay_label = QLabel()
        self.overlay_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 153);  /* 60% 黑色 */
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.overlay_label.hide()  # 默认隐藏
        overlay_layout.addWidget(
            self.overlay_label,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        overlay_layout.addStretch()

        stack.addWidget(overlay_widget)

        return container

    def _create_control_bar(self) -> QWidget:
        """创建播放控制栏。"""
        control_bar = QWidget()
        control_bar.setFixedHeight(80)
        control_bar.setStyleSheet("background: #F5F5F5; border-top: 1px solid #E0E0E0;")

        layout = QHBoxLayout(control_bar)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)

        # 播放/暂停按钮
        self.play_pause_btn = ToolButton(FluentIcon.PLAY)
        self.play_pause_btn.setFixedSize(40, 40)
        layout.addWidget(self.play_pause_btn)

        # 上一个按钮
        self.prev_btn = ToolButton(FluentIcon.LEFT_ARROW)
        self.prev_btn.setFixedSize(40, 40)
        layout.addWidget(self.prev_btn)

        # 下一个按钮
        self.next_btn = ToolButton(FluentIcon.RIGHT_ARROW)
        self.next_btn.setFixedSize(40, 40)
        layout.addWidget(self.next_btn)

        # 当前时间
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setFixedWidth(45)
        self.current_time_label.setStyleSheet("font-size: 13px; color: #333;")
        layout.addWidget(self.current_time_label)

        # 进度条
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        layout.addWidget(self.progress_slider, stretch=1)

        # 总时长
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setFixedWidth(45)
        self.total_time_label.setStyleSheet("font-size: 13px; color: #333;")
        layout.addWidget(self.total_time_label)

        # 音量按钮
        self.volume_btn = ToolButton(FluentIcon.VOLUME)
        self.volume_btn.setFixedSize(40, 40)
        layout.addWidget(self.volume_btn)

        # 音量滑块
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(80)
        layout.addWidget(self.volume_slider)

        return control_bar

    def _connect_signals(self) -> None:
        """连接信号。"""
        # 播放器信号
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)

        # 控制按钮信号
        self.play_pause_btn.clicked.connect(self._toggle_play_pause)
        self.prev_btn.clicked.connect(self._play_previous)
        self.next_btn.clicked.connect(self._play_next)

        # 进度条信号
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)

        # 音量信号
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.volume_btn.clicked.connect(self._toggle_mute)

    # === 核心播放逻辑 ===

    def load_playlist(self, project_id: int) -> None:
        """加载项目播放列表并开始播放。"""
        self._playlist = self._generate_playlist(project_id)

        if not self._playlist:
            self.overlay_label.setText("没有可播放的分镜视频")
            self.overlay_label.show()
            self.playlist_info_label.setText("0 / 0")
            logger.warning(f"项目 {project_id} 没有分镜视频")
            return

        self._current_index = 0
        self._update_playlist_info()
        logger.info(f"加载播放列表完成，共 {len(self._playlist)} 个视频，开始播放第一个")
        self._play_current()

    def _generate_playlist(self, project_id: int) -> list[PlaylistItem]:
        """生成播放列表（选择每个场次-镜头的最新版本）。"""
        media_files = self._db.list_media_files(project_id=project_id, media_type="video")

        # 按场次-镜头分组
        shot_videos: dict[tuple[int, int], list[tuple[int, MediaFile]]] = {}
        pattern = re.compile(r"^(\d+)-(\d+)-(\d+)\.mp4$")

        for media in media_files:
            match = pattern.match(media.filename)
            if match:
                scene = int(match.group(1))
                shot = int(match.group(2))
                seq = int(match.group(3))
                key = (scene, shot)
                if key not in shot_videos:
                    shot_videos[key] = []
                shot_videos[key].append((seq, media))

        # 选择每组的最大序号（最新版本）
        playlist = []
        for (scene, shot), videos in sorted(shot_videos.items()):
            latest_seq, latest_media = max(videos, key=lambda x: x[0])
            playlist.append(PlaylistItem(
                scene_number=scene,
                shot_number=shot,
                sequence=latest_seq,
                media_file=latest_media
            ))

        logger.info(f"生成播放列表：共 {len(playlist)} 个视频")
        return playlist

    def _play_current(self) -> None:
        """播放当前索引的视频。"""
        if not (0 <= self._current_index < len(self._playlist)):
            logger.warning("播放索引超出范围")
            return

        item = self._playlist[self._current_index]
        self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(item.media_file.local_path))
        self._update_overlay(item)
        self._update_playlist_info()

        logger.info(f"播放视频：场{item.scene_number}镜{item.shot_number}-第{item.sequence}次生成 ({item.media_file.filename})")

        # 显式启动播放，确保视频立即开始
        self._player.play()
        logger.debug("已调用 player.play() 启动播放")

    def _update_overlay(self, item: PlaylistItem) -> None:
        """更新叠加层文本。"""
        text = f"场{item.scene_number}镜{item.shot_number}-第{item.sequence}次生成"
        self.overlay_label.setText(text)
        self.overlay_label.show()

    def _update_playlist_info(self) -> None:
        """更新播放列表信息。"""
        if self._playlist:
            self.playlist_info_label.setText(f"{self._current_index + 1} / {len(self._playlist)}")
        else:
            self.playlist_info_label.setText("0 / 0")

    # === 信号处理 ===

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        """媒体状态改变（关键：自动切换下一个）。"""
        # 记录所有状态变化，便于诊断
        status_name = {
            QMediaPlayer.MediaStatus.NoMedia: "NoMedia",
            QMediaPlayer.MediaStatus.LoadingMedia: "LoadingMedia",
            QMediaPlayer.MediaStatus.LoadedMedia: "LoadedMedia",
            QMediaPlayer.MediaStatus.StalledMedia: "StalledMedia",
            QMediaPlayer.MediaStatus.BufferingMedia: "BufferingMedia",
            QMediaPlayer.MediaStatus.BufferedMedia: "BufferedMedia",
            QMediaPlayer.MediaStatus.EndOfMedia: "EndOfMedia",
            QMediaPlayer.MediaStatus.InvalidMedia: "InvalidMedia",
        }.get(status, f"Unknown({status})")
        logger.debug(f"媒体状态变化: {status_name}")

        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            # 加载完成，确保播放（虽然 _play_current 已经调用了 play）
            if self._player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                logger.debug("LoadedMedia 状态下播放器未运行，调用 play()")
                self._player.play()
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            # 播放结束，切换下一个
            logger.info(f"视频播放结束 [索引 {self._current_index + 1}/{len(self._playlist)}]，自动切换下一个")
            self._play_next()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            logger.error(f"无效的媒体文件，无法播放当前视频 [索引 {self._current_index + 1}]")

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """播放状态改变（更新播放/暂停按钮图标）。"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_btn.setIcon(FluentIcon.PAUSE)
        else:
            self.play_pause_btn.setIcon(FluentIcon.PLAY)

    def _on_position_changed(self, position: int) -> None:
        """播放位置改变（更新进度条和时间）。"""
        if not self._is_slider_pressed:
            duration = self._player.duration()
            if duration > 0:
                self.progress_slider.setValue(int(position * 1000 / duration))

        self.current_time_label.setText(self._format_time(position))

    def _on_duration_changed(self, duration: int) -> None:
        """视频时长改变。"""
        self.total_time_label.setText(self._format_time(duration))

    def _on_volume_changed(self, value: int) -> None:
        """音量改变。"""
        self._audio_output.setVolume(value / 100.0)

    # === 控制按钮处理 ===

    def _toggle_play_pause(self) -> None:
        """切换播放/暂停。"""
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _play_next(self) -> None:
        """播放下一个视频。"""
        if self._current_index < len(self._playlist) - 1:
            self._current_index += 1
            logger.info(f"切换到下一个视频 [索引 {self._current_index + 1}/{len(self._playlist)}]")
            self._play_current()
        else:
            # 播放完毕，停止（停留在最后一帧）
            logger.info("播放列表已全部播放完毕，停留在最后一帧")

    def _play_previous(self) -> None:
        """播放上一个视频。"""
        if self._current_index > 0:
            self._current_index -= 1
            logger.info(f"切换到上一个视频 [索引 {self._current_index + 1}/{len(self._playlist)}]")
            self._play_current()

    def _toggle_mute(self) -> None:
        """切换静音。"""
        is_muted = self._audio_output.isMuted()
        self._audio_output.setMuted(not is_muted)
        self.volume_btn.setIcon(FluentIcon.MUTE if not is_muted else FluentIcon.VOLUME)

    # === 进度条拖动处理 ===

    def _on_slider_pressed(self) -> None:
        """进度条按下（暂停自动更新）。"""
        self._is_slider_pressed = True

    def _on_slider_released(self) -> None:
        """进度条释放（跳转到目标位置）。"""
        self._is_slider_pressed = False
        duration = self._player.duration()
        if duration > 0:
            position = int(self.progress_slider.value() * duration / 1000)
            self._player.setPosition(position)

    # === 工具方法 ===

    @staticmethod
    def _format_time(ms: int) -> str:
        """格式化时间（毫秒 → MM:SS）。"""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    # === 生命周期 ===

    def hideEvent(self, event) -> None:
        """页面隐藏时暂停播放。"""
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        super().hideEvent(event)
