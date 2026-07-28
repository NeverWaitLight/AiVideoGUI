"""视频播放器桥接：播放列表管理。"""

from __future__ import annotations

import json
import re
from loguru import logger

from PySide6.QtCore import QObject, Property, Signal, Slot

from models.enums import MediaType
from storage.repositories.conversation_repository import ConversationRepository
from storage.repositories.media_repository import MediaRepository


class VideoPlayerBridge(QObject):
    """视频播放器桥接。"""

    playlist_changed = Signal()
    current_index_changed = Signal()

    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self._session_manager = session_manager
        self._playlist: list[dict] = []
        self._current_index: int = -1

    @Property(int, notify=current_index_changed)
    def currentIndex(self) -> int:
        return self._current_index

    @Property(int, notify=playlist_changed)
    def playlistCount(self) -> int:
        return len(self._playlist)

    @Slot(int)
    def load_playlist(self, project_id: int) -> None:
        """从项目分镜视频生成播放列表。"""
        conv_repo = self._session_manager.get_repo(ConversationRepository)
        media_repo = self._session_manager.get_repo(MediaRepository)

        conversations = conv_repo.list_by_project(project_id, is_hidden=False)
        conv_ids = {c.id for c in conversations}

        media_files = media_repo.list_with_filters(
            media_type=MediaType.VIDEO, conversation_ids=conv_ids,
        )

        # 按场次-镜头分组，选择最新版本
        shot_videos: dict[tuple[int, int], list[tuple[int, object]]] = {}
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

        # 每组选最大序号（最新版本）
        playlist = []
        for (scene, shot), videos in sorted(shot_videos.items()):
            latest_seq, latest_media = max(videos, key=lambda x: x[0])
            playlist.append({
                "sceneNumber": scene,
                "shotNumber": shot,
                "sequence": latest_seq,
                "fileName": latest_media.filename,
                "filePath": latest_media.local_path,
                "thumbnailPath": latest_media.thumbnail_path or "",
                "duration": latest_media.duration or 0,
                "label": f"场{scene}镜{shot}-第{latest_seq}次",
            })

        self._playlist = playlist
        self._current_index = 0 if playlist else -1
        self.playlist_changed.emit()
        self.current_index_changed.emit()
        logger.info(f"播放列表加载完成：{len(playlist)} 个视频")

    @Slot(result=str)
    def get_playlist_json(self) -> str:
        """返回播放列表 JSON。"""
        return json.dumps(self._playlist)

    @Slot(result=str)
    def get_current_video(self) -> str:
        """获取当前视频信息 JSON。"""
        if 0 <= self._current_index < len(self._playlist):
            return json.dumps(self._playlist[self._current_index])
        return "{}"

    @Slot(int)
    def set_current_index(self, index: int) -> None:
        """设置当前播放索引。"""
        if 0 <= index < len(self._playlist):
            self._current_index = index
            self.current_index_changed.emit()

    @Slot()
    def play_next(self) -> None:
        """切换到下一个视频。"""
        if self._current_index < len(self._playlist) - 1:
            self._current_index += 1
            self.current_index_changed.emit()

    @Slot()
    def play_previous(self) -> None:
        """切换到上一个视频。"""
        if self._current_index > 0:
            self._current_index -= 1
            self.current_index_changed.emit()

    @Slot(str, result=str)
    def get_thumbnail(self, message_id: str) -> str:
        media_repo = self._session_manager.get_repo(MediaRepository)
        media_file = media_repo.get_by_message_id(message_id)
        return media_file.thumbnail_path if media_file else ""

    @Slot(str, result=float)
    def get_duration(self, message_id: str) -> float:
        media_repo = self._session_manager.get_repo(MediaRepository)
        media_file = media_repo.get_by_message_id(message_id)
        return media_file.duration if media_file else 0.0
