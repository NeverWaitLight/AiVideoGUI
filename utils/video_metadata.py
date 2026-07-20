"""视频元数据提取工具。"""

import logging
import os
from pathlib import Path

import ffmpeg

logger = logging.getLogger(__name__)


class VideoMetadataExtractor:
    """使用 ffmpeg 提取视频元数据和生成缩略图。"""

    @staticmethod
    def extract_metadata(video_path: str) -> dict:
        """
        提取视频元数据。

        Args:
            video_path: 视频文件路径

        Returns:
            包含以下字段的字典：
            - duration: 时长（秒）
            - width: 分辨率宽度
            - height: 分辨率高度
            - file_size: 文件大小（字节）

        Raises:
            RuntimeError: ffmpeg 执行失败
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next(
                (s for s in probe["streams"] if s["codec_type"] == "video"), None
            )
            if not video_stream:
                raise RuntimeError("未找到视频流")

            duration = float(probe["format"].get("duration", 0))
            width = int(video_stream.get("width", 0))
            height = int(video_stream.get("height", 0))
            file_size = int(probe["format"].get("size", 0))

            logger.info(
                "提取视频元数据: %s (%.1fs, %dx%d, %d bytes)",
                video_path,
                duration,
                width,
                height,
                file_size,
            )

            return {
                "duration": duration,
                "width": width,
                "height": height,
                "file_size": file_size,
            }
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error("ffmpeg probe 失败: %s", error_msg)
            raise RuntimeError(f"无法提取视频元数据: {error_msg}") from e

    @staticmethod
    def generate_thumbnail(video_path: str, output_path: str, time_offset: float = 1.0) -> str:
        """
        生成视频缩略图。

        Args:
            video_path: 视频文件路径
            output_path: 缩略图输出路径（应为 .jpg 或 .png）
            time_offset: 截取时间点（秒），默认第 1 秒

        Returns:
            生成的缩略图路径

        Raises:
            RuntimeError: ffmpeg 执行失败
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        # 确保输出目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            # 提取指定时间点的帧作为缩略图
            (
                ffmpeg.input(video_path, ss=time_offset)
                .filter("scale", 320, -1)  # 宽度 320px，高度自适应
                .output(output_path, vframes=1, format="image2", vcodec="mjpeg")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )

            logger.info("生成视频缩略图: %s -> %s", video_path, output_path)
            return output_path
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error("ffmpeg 生成缩略图失败: %s", error_msg)
            raise RuntimeError(f"无法生成缩略图: {error_msg}") from e

    @staticmethod
    def extract_all(video_path: str, thumbnail_dir: str) -> dict:
        """
        提取视频元数据并生成缩略图（一站式方法）。

        Args:
            video_path: 视频文件路径
            thumbnail_dir: 缩略图保存目录

        Returns:
            包含元数据和缩略图路径的字典：
            - duration: 时长（秒）
            - width: 分辨率宽度
            - height: 分辨率高度
            - file_size: 文件大小（字节）
            - thumbnail_path: 缩略图路径

        Raises:
            RuntimeError: 提取失败
        """
        metadata = VideoMetadataExtractor.extract_metadata(video_path)

        # 生成缩略图文件名（基于视频文件名）
        video_name = Path(video_path).stem
        thumbnail_path = os.path.join(thumbnail_dir, f"{video_name}_thumb.jpg")

        try:
            VideoMetadataExtractor.generate_thumbnail(video_path, thumbnail_path)
            metadata["thumbnail_path"] = thumbnail_path
        except Exception as e:
            logger.warning("生成缩略图失败，跳过: %s", e)
            metadata["thumbnail_path"] = ""

        return metadata
