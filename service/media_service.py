"""素材库服务：管理媒体文件的导入、查询、删除和自动入库。"""

import logging
import os
import shutil
from pathlib import Path

from models.data_models import MediaFile, MediaType
from storage.database import DatabaseManager
from utils import paths
from utils.video_metadata import VideoMetadataExtractor

logger = logging.getLogger(__name__)

_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}
_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"}
_ALL_MEDIA_EXTENSIONS = _VIDEO_EXTENSIONS | _IMAGE_EXTENSIONS | _AUDIO_EXTENSIONS


def detect_media_type(filename: str) -> MediaType | None:
    """根据文件扩展名判断媒体类型。"""
    ext = Path(filename).suffix.lower()
    if ext in _VIDEO_EXTENSIONS:
        return MediaType.VIDEO
    if ext in _IMAGE_EXTENSIONS:
        return MediaType.IMAGE
    if ext in _AUDIO_EXTENSIONS:
        return MediaType.AUDIO
    return None


def supported_extensions() -> set[str]:
    """返回所有支持的媒体文件扩展名。"""
    return _ALL_MEDIA_EXTENSIONS


class MediaService:
    """素材库业务服务。"""

    def __init__(self, db: DatabaseManager, workspace_root: str) -> None:
        self._db = db
        self._root = workspace_root
        self._chat_dir = paths.chat_dir(workspace_root)
        os.makedirs(self._chat_dir, exist_ok=True)

    def register_task_result(
        self,
        message_id: int,
        local_path: str,
        conversation_id: int = 0,
    ) -> None:
        """视频任务完成后自动入库（防重复）。"""
        if self._db.get_media_file_by_message(message_id):
            logger.debug("素材已入库，跳过 message_id=%s", message_id)
            return

        filename = os.path.basename(local_path)
        media_type = detect_media_type(filename) or MediaType.VIDEO
        file_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0

        # 缩略图存放在文件所在目录的 .thumbnails 子目录
        file_dir = os.path.dirname(local_path)
        thumb_dir = paths.thumbnail_dir(file_dir)
        os.makedirs(thumb_dir, exist_ok=True)

        # 提取视频元数据
        thumbnail_path = ""
        duration = 0.0
        width = 0
        height = 0

        if media_type == MediaType.VIDEO and os.path.exists(local_path):
            try:
                metadata = VideoMetadataExtractor.extract_all(local_path, thumb_dir)
                thumbnail_path = metadata.get("thumbnail_path", "")
                duration = metadata.get("duration", 0.0)
                width = metadata.get("width", 0)
                height = metadata.get("height", 0)
                # 如果提取到的 file_size 更准确，使用 ffmpeg 的结果
                if metadata.get("file_size", 0) > 0:
                    file_size = metadata["file_size"]
                logger.info(
                    "视频元数据提取成功：%s (%.1fs, %dx%d)",
                    filename,
                    duration,
                    width,
                    height,
                )
            except Exception as e:
                logger.warning("视频元数据提取失败，将使用默认值：%s", e)

        media = MediaFile(
            id=0,
            filename=filename,
            media_type=media_type,
            local_path=local_path,
            file_size=file_size,
            source="task",
            conversation_id=conversation_id,
            message_id=message_id,
            created_at=0,
            thumbnail_path=thumbnail_path,
            duration=duration,
            width=width,
            height=height,
        )
        self._db.add_media_file(media)
        logger.info("素材自动入库：%s", filename)

    def import_files(self, file_paths: list[str], project_id: int = 0) -> list[MediaFile]:
        """将外部文件复制到目标目录并入库。project_id 非空时存入项目目录，否则存入 chat 目录。"""
        target_dir = paths.project_dir(self._root, project_id) if project_id else self._chat_dir
        os.makedirs(target_dir, exist_ok=True)
        imported: list[MediaFile] = []

        for src_path in file_paths:
            filename = os.path.basename(src_path)
            media_type = detect_media_type(filename)
            if media_type is None:
                logger.warning("不支持的文件类型，跳过：%s", filename)
                continue

            dest_path = self._resolve_dest_path(filename, target_dir)

            try:
                shutil.copy2(src_path, dest_path)
            except OSError as e:
                logger.error("复制文件失败 %s: %s", src_path, e)
                continue

            file_size = os.path.getsize(dest_path)

            # 缩略图存放在文件所在目录的 .thumbnails 子目录
            thumb_dir = paths.thumbnail_dir(target_dir)
            os.makedirs(thumb_dir, exist_ok=True)

            # 提取视频元数据
            thumbnail_path = ""
            duration = 0.0
            width = 0
            height = 0

            if media_type == MediaType.VIDEO:
                try:
                    metadata = VideoMetadataExtractor.extract_all(dest_path, thumb_dir)
                    thumbnail_path = metadata.get("thumbnail_path", "")
                    duration = metadata.get("duration", 0.0)
                    width = metadata.get("width", 0)
                    height = metadata.get("height", 0)
                    if metadata.get("file_size", 0) > 0:
                        file_size = metadata["file_size"]
                    logger.info(
                        "导入视频元数据提取成功：%s (%.1fs, %dx%d)",
                        filename,
                        duration,
                        width,
                        height,
                    )
                except Exception as e:
                    logger.warning("导入视频元数据提取失败，将使用默认值：%s", e)

            media = MediaFile(
                id=0,
                filename=os.path.basename(dest_path),
                media_type=media_type,
                local_path=dest_path,
                file_size=file_size,
                source="import",
                created_at=0,
                thumbnail_path=thumbnail_path,
                duration=duration,
                width=width,
                height=height,
            )
            self._db.add_media_file(media)
            imported.append(media)
            logger.info("导入素材：%s", media.filename)

        return imported

    def list_files(
        self,
        media_type: str | None = None,
        keyword: str | None = None,
        project_id: int | None = None,
    ) -> list[MediaFile]:
        """查询素材列表，可选按项目过滤。"""
        return self._db.list_media_files(
            media_type=media_type,
            keyword=keyword,
            project_id=project_id
        )

    def delete_file(self, media_id: int) -> bool:
        """删除单个素材（文件 + 缩略图 + 数据库记录）。"""
        media = self._db.delete_media_file(media_id)
        if not media:
            return False
        self._try_remove_file(media.local_path)
        # 同时删除缩略图
        if media.thumbnail_path:
            self._try_remove_file(media.thumbnail_path)
        logger.info("删除素材：%s", media.filename)
        return True

    def delete_files(self, media_ids: list[int]) -> int:
        """批量删除素材，返回成功删除数量。"""
        count = 0
        for mid in media_ids:
            if self.delete_file(mid):
                count += 1
        return count

    def _resolve_dest_path(self, filename: str, target_dir: str) -> str:
        """避免目标文件重名：同名时追加序号。"""
        dest = os.path.join(target_dir, filename)
        if not os.path.exists(dest):
            return dest
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        counter = 1
        while os.path.exists(dest):
            dest = os.path.join(target_dir, f"{stem}_{counter}{suffix}")
            counter += 1
        return dest

    @staticmethod
    def _try_remove_file(path: str) -> None:
        """尝试删除磁盘文件，失败时仅记录日志。"""
        if not path or not os.path.exists(path):
            return
        try:
            os.remove(path)
        except OSError as e:
            logger.warning("删除文件失败 %s: %s", path, e)
