"""视频播放器页面：按场次-镜头顺序自动拼接播放分镜视频。"""

from __future__ import annotations

from loguru import logger
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSize, Qt, QUrl, pyqtSignal
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
from qfluentwidgets import FluentIcon, TitleLabel, PushButton, ToolButton

from models.enums import MediaType
from ui.page_header import PageHeader
from ui.timeline_widget import TimelineWidget, VideoSegment, generate_segment_colors

if TYPE_CHECKING:
    from models.media_file import MediaFile
    from storage.session_manager import SessionManager

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

    def __init__(self, session_manager: SessionManager, parent: QWidget | None = None):
        super().__init__(parent)
        self._session_manager = session_manager
        self._playlist: list[PlaylistItem] = []
        self._current_index = 0

        # 双播放器无缝切换方案
        self._player1 = QMediaPlayer()
        self._player2 = QMediaPlayer()
        self._audio_output1 = QAudioOutput()
        self._audio_output2 = QAudioOutput()
        self._player1.setAudioOutput(self._audio_output1)
        self._player2.setAudioOutput(self._audio_output2)

        self._video_widget = QVideoWidget()

        # 当前活跃的播放器（0=player1, 1=player2）
        self._active_player_index = 0
        self._player1.setVideoOutput(self._video_widget)

        # 预加载和切换优化
        self._preload_threshold = 600   # 提前0.6秒预加载下一个视频（毫秒）
        self._switch_threshold = 100    # 提前0.1秒切换播放器（毫秒）
        self._next_prepared = False     # 标记下一个视频是否已准备好
        self._next_started = False      # 标记下一个视频是否已开始播放

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
        header = PageHeader("项目视频播放")
        header.back_clicked.connect(self.back_clicked.emit)

        self.playlist_info_label = QLabel("0 / 0")
        self.playlist_info_label.setStyleSheet("font-size: 14px; color: #666;")
        header.add_action(self.playlist_info_label)

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
        control_bar.setFixedHeight(120)  # 增加高度以适应更高的时间轴
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

        # 时间轴（替换旧的进度条）
        self.timeline = TimelineWidget()
        layout.addWidget(self.timeline, stretch=1)

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
        # 播放器1信号
        self._player1.mediaStatusChanged.connect(self._on_media_status_changed)
        self._player1.positionChanged.connect(self._on_position_changed)
        self._player1.durationChanged.connect(self._on_duration_changed)
        self._player1.playbackStateChanged.connect(self._on_playback_state_changed)

        # 播放器2信号
        self._player2.mediaStatusChanged.connect(self._on_media_status_changed)

        # 控制按钮信号
        self.play_pause_btn.clicked.connect(self._toggle_play_pause)
        self.prev_btn.clicked.connect(self._play_previous)
        self.next_btn.clicked.connect(self._play_next)

        # 时间轴信号
        self.timeline.seekRequested.connect(self._on_timeline_seek)

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

        # 构建时间轴数据
        self._build_timeline_segments()

        self._current_index = 0
        self._update_playlist_info()
        logger.info(f"加载播放列表完成，共 {len(self._playlist)} 个视频，开始播放第一个")
        self._play_current()

    def _generate_playlist(self, project_id: int) -> list[PlaylistItem]:
        """生成播放列表（选择每个场次-镜头的最新版本）。"""
        from storage.repositories.conversation_repository import ConversationRepository
        from storage.repositories.media_repository import MediaRepository

        # 获取 Repository 实例
        conv_repo = self._session_manager.get_repo(ConversationRepository)
        media_repo = self._session_manager.get_repo(MediaRepository)

        # 查询项目的所有对话
        conversations = conv_repo.list_by_project(project_id, is_hidden=False)
        conv_ids = {c.id for c in conversations}

        # 查询视频文件
        media_files = media_repo.list_with_filters(
            media_type=MediaType.VIDEO,
            conversation_ids=conv_ids
        )

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

    def _build_timeline_segments(self) -> None:
        """构建时间轴片段数据。"""
        segments = []
        colors = generate_segment_colors(len(self._playlist))
        cumulative_time = 0

        for i, item in enumerate(self._playlist):
            duration = item.media_file.duration or 0
            segments.append(VideoSegment(
                scene_number=item.scene_number,
                shot_number=item.shot_number,
                sequence=item.sequence,
                start_time=cumulative_time,
                duration=duration,
                color=colors[i],
                thumbnail_path=item.media_file.thumbnail_path
            ))
            cumulative_time += duration

        self.timeline.set_segments(segments)
        logger.debug(f"时间轴片段构建完成：{len(segments)} 个片段，总时长 {cumulative_time}ms")

    def _play_current(self) -> None:
        """播放当前索引的视频。"""
        if not (0 <= self._current_index < len(self._playlist)):
            logger.warning("播放索引超出范围")
            return

        item = self._playlist[self._current_index]

        # 获取当前活跃的播放器
        active_player = self._get_active_player()

        # 直接设置新源（不调用 stop，减少状态转换）
        active_player.setSource(QUrl.fromLocalFile(item.media_file.local_path))
        self._update_overlay(item)
        self._update_playlist_info()

        # 重置预加载标记
        self._next_prepared = False
        self._next_started = False

        logger.info(f"播放视频：场{item.scene_number}镜{item.shot_number}-第{item.sequence}次生成 ({item.media_file.filename})")

        # 显式启动播放，确保视频立即开始
        active_player.play()
        logger.debug("已调用 player.play() 启动播放")

    def _get_active_player(self) -> QMediaPlayer:
        """获取当前活跃的播放器。"""
        return self._player1 if self._active_player_index == 0 else self._player2

    def _get_inactive_player(self) -> QMediaPlayer:
        """获取当前非活跃的播放器（用于预加载）。"""
        return self._player2 if self._active_player_index == 0 else self._player1

    def _get_inactive_audio(self) -> QAudioOutput:
        """获取当前非活跃的音频输出。"""
        return self._audio_output2 if self._active_player_index == 0 else self._audio_output1

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
            active_player = self._get_active_player()
            if active_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                logger.debug("LoadedMedia 状态下播放器未运行，调用 play()")
                active_player.play()
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            # 播放结束，切换下一个（如果已准备好则立即切换）
            logger.info(f"视频播放结束 [索引 {self._current_index + 1}/{len(self._playlist)}]，自动切换下一个")

            # 检查是否还有下一个视频
            if self._current_index < len(self._playlist) - 1:
                self._current_index += 1

                # 如果下一个视频已经开始播放，直接切换播放器
                if self._next_started:
                    self._instant_switch_to_next()
                else:
                    # 否则正常播放
                    self._play_current()
            else:
                logger.info("播放列表已全部播放完毕")
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
        # 计算全局位置并更新时间轴
        global_position = self._calculate_global_position(position)
        self.timeline.set_position(global_position)

        # 更新时间标签
        self.current_time_label.setText(self._format_time(position))

        # 预加载和切换优化
        active_player = self._get_active_player()
        duration = active_player.duration()
        if duration > 0:
            remaining = duration - position

            # 步骤1：提前0.6秒预加载下一个视频到备用播放器
            if not self._next_prepared and remaining <= self._preload_threshold and remaining > 0:
                self._prepare_next_video()
                self._next_prepared = True

            # 步骤2：提前0.1秒启动下一个视频播放（静音）
            if self._next_prepared and not self._next_started and remaining <= self._switch_threshold and remaining > 0:
                self._start_next_video_silently()
                self._next_started = True

    def _on_duration_changed(self, duration: int) -> None:
        """视频时长改变。"""
        self.total_time_label.setText(self._format_time(duration))

    def _on_volume_changed(self, value: int) -> None:
        """音量改变。"""
        # 同步两个播放器的音量
        self._audio_output1.setVolume(value / 100.0)
        self._audio_output2.setVolume(value / 100.0)

    # === 控制按钮处理 ===

    def _toggle_play_pause(self) -> None:
        """切换播放/暂停。"""
        active_player = self._get_active_player()
        if active_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            active_player.pause()
        else:
            active_player.play()

    def _play_next(self) -> None:
        """播放下一个视频（手动切换）。"""
        if self._current_index < len(self._playlist) - 1:
            self._current_index += 1
            logger.info(f"手动切换到下一个视频 [索引 {self._current_index + 1}/{len(self._playlist)}]")
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
        # 同步两个播放器的静音状态
        is_muted = self._audio_output1.isMuted()
        self._audio_output1.setMuted(not is_muted)
        self._audio_output2.setMuted(not is_muted)
        self.volume_btn.setIcon(FluentIcon.MUTE if not is_muted else FluentIcon.VOLUME)

    # === 时间轴拖动处理 ===

    def _on_timeline_seek(self, global_position: int) -> None:
        """时间轴拖动定位。"""
        # 查找目标视频片段
        target_index, local_position = self._find_segment_at_position(global_position)

        if target_index is None:
            logger.warning(f"无法找到全局位置 {global_position}ms 对应的片段")
            return

        # 切换到目标视频（如果需要）
        if target_index != self._current_index:
            self._current_index = target_index
            logger.info(f"时间轴定位：切换到视频 {target_index + 1}")
            self._play_current()

        # 定位到片段内的具体时间点
        active_player = self._get_active_player()
        active_player.setPosition(local_position)
        logger.debug(f"时间轴定位：全局位置 {global_position}ms → 视频 {target_index + 1} 本地位置 {local_position}ms")

    def _calculate_global_position(self, local_position: int) -> int:
        """本地位置 → 全局位置。"""
        if not self._playlist or self._current_index < 0:
            return 0

        base_time = sum(
            item.media_file.duration or 0
            for item in self._playlist[:self._current_index]
        )
        return base_time + local_position

    def _find_segment_at_position(self, global_position: int) -> tuple[int | None, int]:
        """全局位置 → (视频索引, 本地位置)。"""
        cumulative = 0
        for i, item in enumerate(self._playlist):
            duration = item.media_file.duration or 0
            if cumulative + duration >= global_position:
                return i, global_position - cumulative
            cumulative += duration

        # 如果超出范围，返回最后一个视频的末尾
        if self._playlist:
            last_duration = self._playlist[-1].media_file.duration or 0
            return len(self._playlist) - 1, last_duration

        return None, 0

    def _prepare_next_video(self) -> None:
        """在备用播放器中预加载下一个视频（关键方法）。"""
        next_index = self._current_index + 1
        if next_index >= len(self._playlist):
            return  # 已经是最后一个视频

        next_item = self._playlist[next_index]
        inactive_player = self._get_inactive_player()

        # 在备用播放器中加载下一个视频，但不播放
        inactive_player.setSource(QUrl.fromLocalFile(next_item.media_file.local_path))

        logger.debug(f"预加载下一个视频到备用播放器：{next_item.media_file.filename}")

    def _start_next_video_silently(self) -> None:
        """提前启动下一个视频播放（静音状态）。"""
        inactive_player = self._get_inactive_player()
        inactive_audio = self._get_inactive_audio()

        # 静音备用播放器
        inactive_audio.setMuted(True)

        # 开始播放（此时已经加载好，可以立即开始解码）
        inactive_player.play()

        logger.debug("提前启动下一个视频播放（静音）")

    def _instant_switch_to_next(self) -> None:
        """瞬间切换到下一个视频（下一个视频已在播放中）。"""
        next_item = self._playlist[self._current_index]

        # 停止当前播放器
        old_player = self._get_active_player()
        old_audio = self._audio_output1 if self._active_player_index == 0 else self._audio_output2
        old_player.stop()

        # 切换活跃播放器
        self._active_player_index = 1 - self._active_player_index
        new_player = self._get_active_player()
        new_audio = self._get_inactive_audio()

        # 将视频输出切换到新播放器
        new_player.setVideoOutput(self._video_widget)

        # 恢复新播放器的音量（取消静音）
        user_muted = old_audio.isMuted()
        new_audio.setMuted(user_muted)

        # 更新 UI
        self._update_overlay(next_item)
        self._update_playlist_info()

        # 重置预加载标记
        self._next_prepared = False
        self._next_started = False

        logger.info(f"瞬间切换到视频：场{next_item.scene_number}镜{next_item.shot_number}-第{next_item.sequence}次生成")

    def _seamless_switch_to_next(self) -> None:
        """无缝切换到下一个视频（关键方法）。"""
        next_item = self._playlist[self._current_index]

        # 停止当前播放器
        old_player = self._get_active_player()
        old_player.stop()

        # 切换活跃播放器
        self._active_player_index = 1 - self._active_player_index
        new_player = self._get_active_player()

        # 将视频输出切换到新播放器
        new_player.setVideoOutput(self._video_widget)

        # 更新 UI
        self._update_overlay(next_item)
        self._update_playlist_info()

        # 重置预加载标记
        self._next_prepared = False

        # 开始播放新视频（已经加载好，立即播放）
        new_player.play()

        logger.info(f"无缝切换到视频：场{next_item.scene_number}镜{next_item.shot_number}-第{next_item.sequence}次生成")

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
        # 暂停所有播放器
        if self._player1.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player1.pause()
        if self._player2.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player2.pause()
        super().hideEvent(event)
