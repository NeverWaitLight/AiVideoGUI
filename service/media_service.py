from loguru import logger
import os
import shutil
import time
import uuid
import subprocess
from pathlib import Path
from imageio_ffmpeg import get_ffmpeg_exe

from models.enums import MediaType
from models.media_file import MediaFile
from storage.session_manager import SessionManager
from storage.repositories.media_repository import MediaRepository
from storage.repositories.project_repository import ProjectRepository
from utils import paths
from utils.video_metadata import VideoMetadataExtractor
from utils.path_converter import to_relative_path

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
                logger.warning(f"视频元数据提取失败，将使用默认值：{e}")

        relative_local_path = to_relative_path(local_path, self._root)
        relative_thumbnail_path = to_relative_path(thumbnail_path, self._root) if thumbnail_path else ""

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
            duration=duration,
            width=width,
            height=height,
            storyboard_id=storyboard_id,
        )

        self._sm.begin_write()
        try:
            media_repo.create(media=media)
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
                    logger.warning(f"导入视频元数据提取失败，将使用默认值：{e}")

            relative_dest_path = to_relative_path(dest_path, self._root)
            relative_thumbnail_path = to_relative_path(thumbnail_path, self._root) if thumbnail_path else ""

            media = MediaFile(
                id=uuid.uuid4().hex,
                filename=os.path.basename(dest_path),
                media_type=media_type,
                local_path=relative_dest_path,
                file_size=file_size,
                source="import",
                created_at=int(time.time() * 1000),
                thumbnail_path=relative_thumbnail_path,
                duration=duration,
                width=width,
                height=height,
            )

            self._sm.begin_write()
            try:
                media_repo = self._sm.get_repo(repo_class=MediaRepository)
                media_repo.create(media=media)
                self._sm.commit_write()
                imported.append(media)
                logger.info(f"导入素材：{media.filename}")
            except Exception as e:
                self._sm.rollback_write()
                logger.error(f"导入素材入库失败: {e}")
                self._try_remove_file(dest_path)
                if thumbnail_path:
                    self._try_remove_file(thumbnail_path)
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

        return media_repo.list_with_filters(
            media_type=media_type_enum,
            keyword=keyword,
            conversation_ids=None,
        )

    def delete_file(self, media_id: str) -> bool:
        media_repo = self._sm.get_repo(repo_class=MediaRepository)

        media = media_repo.get_by_id(media_id)
        if not media:
            return False

        self._sm.begin_write()
        try:
            media_repo.delete(media_id=media_id)
            self._sm.commit_write()
        except Exception as e:
            self._sm.rollback_write()
            logger.error(f"删除素材记录失败: {e}")
            raise

        self._try_remove_file(media.local_path)
        if media.thumbnail_path:
            self._try_remove_file(media.thumbnail_path)

        logger.info(f"删除素材：{media.filename}")
        return True

    def delete_files(self, media_ids: list[str]) -> int:
        count = 0
        for mid in media_ids:
            if self.delete_file(mid):
                count += 1
        return count

    def list_by_storyboard(self, storyboard_id: int) -> list[MediaFile]:
        media_repo = self._sm.get_repo(repo_class=MediaRepository)
        return media_repo.list_by_storyboard(storyboard_id)

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
