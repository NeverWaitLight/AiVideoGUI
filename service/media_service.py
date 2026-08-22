import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from imageio_ffmpeg import get_ffmpeg_exe
from loguru import logger

from models.enums import MediaType
from models.media_file import MediaFile
from storage.repositories.media_repository import MediaRepository
from storage.repositories.project_repository import ProjectRepository
from storage.repositories.storyboard_take_repository import StoryboardTakeRepository
from storage.session_manager import SessionManager
from utils import paths
from utils.path_converter import to_relative_path, to_qml_local_path
from utils.video_metadata import VideoMetadataExtractor

_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}
_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"}
_ALL_MEDIA_EXTENSIONS = _VIDEO_EXTENSIONS | _IMAGE_EXTENSIONS | _AUDIO_EXTENSIONS

def detect_media_type(filename: str) -> MediaType | None:
    ext = Path(filename).suffix.lower()
    if ext in _VIDEO_EXTENSIONS:
        return MediaType.VIDEO
    if ext in _IMAGE_EXTENSIONS:
        return MediaType.IMAGE
    if ext in _AUDIO_EXTENSIONS:
        return MediaType.AUDIO
    return None

def supported_extensions() -> set[str]:
    return _ALL_MEDIA_EXTENSIONS

class MediaService:

    def __init__(self, session_manager: SessionManager, workspace_root: str) -> None:
        self._sm = session_manager
        self._root = workspace_root

    def register_task_result(
        self,
        task_id: str,
        local_path: str,
        conversation_id: str = "",
        storyboard_id: int = 0,
        generate_task_id: int = 0,
    ) -> None:
        media_repo = self._sm.get_repo(repo_class=MediaRepository)

        if media_repo.get_by_message_id(task_id):
            logger.debug(f"素材已入库，跳过 task_id={task_id}")
            return

        filename = os.path.basename(local_path)
        media_type = detect_media_type(filename) or MediaType.VIDEO
        file_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0

        file_dir = os.path.dirname(local_path)
        thumb_dir = paths.thumbnail_dir(file_dir)
        os.makedirs(thumb_dir, exist_ok=True)

        thumbnail_path = ""
        first_frame_path = ""
        last_frame_path = ""
        duration = 0.0
        width = 0
        height = 0

        if media_type == MediaType.VIDEO and os.path.exists(local_path):
            try:
                metadata = VideoMetadataExtractor.extract_all(local_path, thumb_dir)
                thumbnail_path = metadata.get("thumbnail_path", "")
                first_frame_path = metadata.get("first_frame_path", "")
                last_frame_path = metadata.get("last_frame_path", "")
                duration = metadata.get("duration", 0.0)
                width = metadata.get("width", 0)
                height = metadata.get("height", 0)
                if metadata.get("file_size", 0) > 0:
                    file_size = metadata["file_size"]
                if not thumbnail_path:
                    video_name = Path(local_path).stem
                    thumbnail_path = os.path.join(thumb_dir, f"{video_name}_thumb.jpg")
                    VideoMetadataExtractor.generate_thumbnail(
                        local_path,
                        thumbnail_path,
                        time_offset=None,
                        duration=duration,
                    )
                logger.info(
                    "视频元数据提取成功：%s (%.1fs, %dx%d)",
                    filename,
                    duration,
                    width,
                    height,
                )
            except Exception as e:
                logger.warning(f"视频元数据提取失败，将使用默认值：{e}")

        relative_local_path = to_relative_path(local_path, self._root)
        relative_thumbnail_path = to_relative_path(thumbnail_path, self._root) if thumbnail_path else ""
        relative_first_frame_path = to_relative_path(first_frame_path, self._root) if first_frame_path else ""
        relative_last_frame_path = to_relative_path(last_frame_path, self._root) if last_frame_path else ""

        media = MediaFile(
            id=uuid.uuid4().hex,
            filename=filename,
            media_type=media_type,
            local_path=relative_local_path,
            file_size=file_size,
            source="task",
            conversation_id="",
            message_id=task_id,
            created_at=int(time.time() * 1000),
            thumbnail_path=relative_thumbnail_path,
            first_frame_path=relative_first_frame_path,
            last_frame_path=relative_last_frame_path,
            duration=duration,
            width=width,
            height=height,
            storyboard_id=storyboard_id,
            generate_task_id=generate_task_id or 0,
        )

        self._sm.begin_write()
        try:
            media_repo.create(dto=media)
            self._sm.commit_write()
            logger.info(f"素材自动入库：{filename}")
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"素材入库失败: {e}")
            raise

    def import_files(self, file_paths: list[str], project_id: int = "") -> list[MediaFile]:
        target_dir = paths.project_dir(self._root, project_id) if project_id else paths.workspace_dir(self._root)
        os.makedirs(target_dir, exist_ok=True)
        imported: list[MediaFile] = []

        for src_path in file_paths:
            filename = os.path.basename(src_path)
            media_type = detect_media_type(filename)
            if media_type is None:
                logger.warning(f"不支持的文件类型，跳过：{filename}")
                continue

            dest_path = self._resolve_dest_path(filename, target_dir)

            try:
                shutil.copy2(src_path, dest_path)
            except OSError as e:
                logger.error(f"复制文件失败 {src_path}: {e}")
                continue

            file_size = os.path.getsize(dest_path)

            thumb_dir = paths.thumbnail_dir(target_dir)
            os.makedirs(thumb_dir, exist_ok=True)

            thumbnail_path = ""
            first_frame_path = ""
            last_frame_path = ""
            duration = 0.0
            width = 0
            height = 0

            if media_type == MediaType.VIDEO:
                try:
                    metadata = VideoMetadataExtractor.extract_all(dest_path, thumb_dir)
                    thumbnail_path = metadata.get("thumbnail_path", "")
                    first_frame_path = metadata.get("first_frame_path", "")
                    last_frame_path = metadata.get("last_frame_path", "")
                    duration = metadata.get("duration", 0.0)
                    width = metadata.get("width", 0)
                    height = metadata.get("height", 0)
                    if metadata.get("file_size", 0) > 0:
                        file_size = metadata["file_size"]
                    if not thumbnail_path:
                        video_name = Path(dest_path).stem
                        thumbnail_path = os.path.join(thumb_dir, f"{video_name}_thumb.jpg")
                        VideoMetadataExtractor.generate_thumbnail(
                            dest_path,
                            thumbnail_path,
                            time_offset=None,
                            duration=duration,
                        )
                    logger.info(
                        "导入视频元数据提取成功：%s (%.1fs, %dx%d)",
                        filename,
                        duration,
                        width,
                        height,
                    )
                except Exception as e:
                    logger.warning(f"导入视频元数据提取失败，将使用默认值：{e}")

            relative_dest_path = to_relative_path(dest_path, self._root)
            relative_thumbnail_path = to_relative_path(thumbnail_path, self._root) if thumbnail_path else ""
            relative_first_frame_path = to_relative_path(first_frame_path, self._root) if first_frame_path else ""
            relative_last_frame_path = to_relative_path(last_frame_path, self._root) if last_frame_path else ""

            media = MediaFile(
                id=uuid.uuid4().hex,
                filename=os.path.basename(dest_path),
                media_type=media_type,
                local_path=relative_dest_path,
                file_size=file_size,
                source="import",
                created_at=int(time.time() * 1000),
                thumbnail_path=relative_thumbnail_path,
                first_frame_path=relative_first_frame_path,
                last_frame_path=relative_last_frame_path,
                duration=duration,
                width=width,
                height=height,
            )

            self._sm.begin_write()
            try:
                media_repo = self._sm.get_repo(repo_class=MediaRepository)
                media_repo.create(dto=media)
                self._sm.commit_write()
                imported.append(media)
                logger.info(f"导入素材：{media.filename}")
            except Exception as e:
                self._sm.rollback_write()
                logger.error(f"导入素材入库失败: {e}")
                self._try_remove_file(dest_path)
                if thumbnail_path:
                    self._try_remove_file(thumbnail_path)
                if first_frame_path:
                    self._try_remove_file(first_frame_path)
                if last_frame_path:
                    self._try_remove_file(last_frame_path)
                raise

        return imported

    def list_files(
        self,
        media_type: str | None = None,
        keyword: str | None = None,
        project_id: int | None = None,
    ) -> list[MediaFile]:
        media_repo = self._sm.get_repo(repo_class=MediaRepository)

        media_type_enum = None
        if media_type:
            media_type_enum = MediaType(media_type)

        files = media_repo.list_with_filters(
            media_type=media_type_enum,
            keyword=keyword,
            conversation_ids=None,
            project_id=project_id,
        )
        return [self._ensure_media_thumbnail(f) for f in files]

    def _ensure_media_thumbnail(self, media: MediaFile) -> MediaFile:
        """确保缩略图路径有效：图片用原图，视频缺失时补生成"""
        if media.media_type == MediaType.IMAGE:
            if media.local_path and os.path.exists(media.local_path):
                media.thumbnail_path = media.local_path
            else:
                media.thumbnail_path = ""
            return media

        if media.media_type != MediaType.VIDEO:
            return media

        if media.thumbnail_path and os.path.exists(media.thumbnail_path):
            return media

        if not media.local_path or not os.path.exists(media.local_path):
            media.thumbnail_path = ""
            return media

        thumb_dir = paths.thumbnail_dir(os.path.dirname(media.local_path))
        os.makedirs(thumb_dir, exist_ok=True)
        video_name = Path(media.local_path).stem
        thumbnail_abs = os.path.join(thumb_dir, f"{video_name}_thumb.jpg")

        try:
            VideoMetadataExtractor.generate_thumbnail(
                media.local_path,
                thumbnail_abs,
                time_offset=None,
                duration=media.duration,
            )
            relative_thumbnail = to_relative_path(thumbnail_abs, self._root)
            media_repo = self._sm.get_repo(repo_class=MediaRepository)
            self._sm.begin_write()
            try:
                media_repo.update_metadata(media.id, thumbnail_path=relative_thumbnail)
                self._sm.commit_write()
            except Exception:
                self._sm.rollback_write()
                raise
            media.thumbnail_path = to_qml_local_path(thumbnail_abs)
            logger.info(f"已补生成视频缩略图：{media.filename}")
        except Exception as e:
            logger.warning(f"补生成缩略图失败 {media.filename}: {e}")
            media.thumbnail_path = ""

        return media

    def delete_file(self, media_id: str) -> bool:
        media_repo = self._sm.get_repo(repo_class=MediaRepository)
        take_repo = self._sm.get_repo(repo_class=StoryboardTakeRepository)

        media = media_repo.get_by_id(media_id)
        if not media:
            return False

        self._sm.begin_write()
        try:
            take_repo.delete_by_media_file_id(media_id)
            media_repo.delete(media_id)
            self._sm.commit_write()
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"删除素材记录失败: {e}")
            raise

        self._try_remove_file(media.local_path)
        if media.thumbnail_path:
            self._try_remove_file(media.thumbnail_path)
        if media.first_frame_path:
            self._try_remove_file(media.first_frame_path)
        if media.last_frame_path:
            self._try_remove_file(media.last_frame_path)

        return True

    def delete_files(self, media_ids: list[str]) -> int:
        count = 0
        for mid in media_ids:
            if self.delete_file(mid):
                count += 1
        return count

    def cleanup_orphaned_files(self) -> int:
        """删除本地文件已不存在的素材库记录，并尝试清理残留缩略图/帧图。"""
        media_repo = self._sm.get_repo(repo_class=MediaRepository)
        take_repo = self._sm.get_repo(repo_class=StoryboardTakeRepository)

        orphans = [
            media
            for media in media_repo.list_all()
            if not media.local_path or not os.path.exists(media.local_path)
        ]
        if not orphans:
            return 0

        orphan_ids = [media.id for media in orphans]
        self._sm.begin_write()
        try:
            for media_id in orphan_ids:
                take_repo.delete_by_media_file_id(media_id)
            deleted = media_repo.delete_by_ids(orphan_ids)
            self._sm.commit_write()
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"清理孤儿素材记录失败: {e}")
            raise

        for media in orphans:
            if media.thumbnail_path:
                self._try_remove_file(media.thumbnail_path)
            if media.first_frame_path:
                self._try_remove_file(media.first_frame_path)
            if media.last_frame_path:
                self._try_remove_file(media.last_frame_path)

        logger.info(f"已清理孤儿素材记录：{deleted}")
        return deleted

    def list_by_storyboard(self, storyboard_id: int) -> list[MediaFile]:
        media_repo = self._sm.get_repo(repo_class=MediaRepository)
        files = media_repo.list_by_storyboard(storyboard_id)
        return [self._ensure_media_thumbnail(f) for f in files]

    def get_file_by_id(self, file_id: str) -> MediaFile | None:
        media_repo = self._sm.get_repo(repo_class=MediaRepository)
        media = media_repo.get_by_id(file_id)
        return self._ensure_media_thumbnail(media) if media else None

    def get_file_by_message_id(self, message_id: str) -> MediaFile | None:
        media_repo = self._sm.get_repo(repo_class=MediaRepository)
        media = media_repo.get_by_message_id(message_id)
        return self._ensure_media_thumbnail(media) if media else None

    def ensure_last_frame(self, media_id: str) -> str:
        media = self.get_file_by_id(media_id)
        if not media:
            return ""

        if media.last_frame_path and os.path.exists(media.last_frame_path):
            return media.last_frame_path

        if not media.local_path or not os.path.exists(media.local_path):
            return ""

        thumb_dir = paths.thumbnail_dir(os.path.dirname(media.local_path))
        os.makedirs(thumb_dir, exist_ok=True)

        try:
            frame_paths = VideoMetadataExtractor.extract_first_last_frames(
                media.local_path,
                thumb_dir,
                duration=media.duration,
            )
        except Exception as e:
            logger.warning(f"提取末帧失败 media_id={media_id}: {e}")
            return ""

        last_frame = frame_paths.get("last_frame_path", "")
        first_frame = frame_paths.get("first_frame_path", "")
        if not last_frame:
            return ""

        relative_last = to_relative_path(last_frame, self._root)
        relative_first = to_relative_path(first_frame, self._root) if first_frame else ""

        media_repo = self._sm.get_repo(repo_class=MediaRepository)
        self._sm.begin_write()
        try:
            media_repo.update_metadata(
                media_id,
                first_frame_path=relative_first,
                last_frame_path=relative_last,
            )
            self._sm.commit_write()
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"回写末帧路径失败 media_id={media_id}: {e}")
            raise

        return last_frame

    def set_featured(self, file_id: str, storyboard_id: int) -> None:
        media_repo = self._sm.get_repo(repo_class=MediaRepository)

        self._sm.begin_write()
        try:
            media_repo.set_featured(file_id=file_id, storyboard_id=storyboard_id)
            self._sm.commit_write()
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"设置封面失败: {e}")
            raise

    def export_project_video(self, project_id: int, output_path: str, progress_callback=None) -> str:
        media_repo = self._sm.get_repo(repo_class=MediaRepository)
        project_repo = self._sm.get_repo(repo_class=ProjectRepository)

        project = project_repo.get_by_id(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        videos = self._get_selected_take_videos(project_id)
        if not videos:
            videos = media_repo.list_featured_by_project(project_id)
        if not videos:
            raise ValueError("该项目没有可导出的视频")

        logger.info(f"开始导出项目视频，共 {len(videos)} 个分镜")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        temp_list_file = os.path.join(os.path.dirname(output_path), f".concat_list_{uuid.uuid4().hex}.txt")

        try:
            with open(temp_list_file, "w", encoding="utf-8") as f:
                for video in videos:
                    video_path = video.local_path.replace("\\", "/")
                    f.write(f"file '{video_path}'\n")

            logger.info(f"拼接列表文件已创建: {temp_list_file}")

            if progress_callback:
                progress_callback(10, f"开始拼接 {len(videos)} 个视频...")

            ffmpeg_exe = get_ffmpeg_exe()
            cmd = [
                ffmpeg_exe,
                "-f", "concat",
                "-safe", "0",
                "-i", temp_list_file,
                "-c", "copy",
                "-y",
                output_path
            ]

            logger.info(f"执行 ffmpeg 命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            if result.returncode != 0:
                logger.error(f"ffmpeg 拼接失败: {result.stderr}")
                raise RuntimeError(f"视频拼接失败: {result.stderr}")

            if progress_callback:
                progress_callback(90, "视频拼接完成，正在收尾...")

            logger.info(f"视频导出成功: {output_path}")

            if progress_callback:
                progress_callback(100, "导出完成")

            return output_path

        except Exception as e:
            logger.error(f"视频导出失败: {e}")
            raise
        finally:
            if os.path.exists(temp_list_file):
                try:
                    os.remove(temp_list_file)
                except OSError:
                    pass

    def _get_selected_take_videos(self, project_id: int) -> list[MediaFile]:
        """从 storyboard_takes 获取状态为选用的视频文件"""
        try:
            from storage.repositories.storyboard_take_repository import StoryboardTakeRepository
            take_repo = self._sm.get_repo(repo_class=StoryboardTakeRepository)
            selected_takes = take_repo.list_selected_by_project(project_id)
            if not selected_takes:
                return []

            media_repo = self._sm.get_repo(repo_class=MediaRepository)
            videos = []
            for take in selected_takes:
                if not take.media_file_id:
                    continue
                media = media_repo.get_by_id(take.media_file_id)
                if media:
                    videos.append(media)
            return videos
        except Exception as e:
            logger.warning(f"查询选用拍摄记录失败，回退到旧逻辑: {e}")
            return []

    def _resolve_dest_path(self, filename: str, target_dir: str) -> str:
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
        if not path or not os.path.exists(path):
            return
        try:
            os.remove(path)
        except OSError as e:
            logger.warning(f"删除文件失败 {path}: {e}")
