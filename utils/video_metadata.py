from loguru import logger
import os
from pathlib import Path

import ffmpeg

class VideoMetadataExtractor:
    @staticmethod
    def extract_metadata(video_path: str) -> dict:
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
                f"提取视频元数据: {video_path} ({duration:.1f}s, {width}x{height}, {file_size} bytes)"
            )

            return {
                "duration": duration,
                "width": width,
                "height": height,
                "file_size": file_size,
            }
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"ffmpeg probe 失败: {error_msg}")
            raise RuntimeError(f"无法提取视频元数据: {error_msg}") from e

    @staticmethod
    def generate_thumbnail(video_path: str, output_path: str, time_offset: float = 1.0) -> str:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            (
                ffmpeg.input(video_path, ss=time_offset)
                .filter("scale", 320, -1)
                .output(output_path, vframes=1, format="image2", vcodec="mjpeg")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )

            logger.info(f"生成视频缩略图: {video_path} -> {output_path}")
            return output_path
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"ffmpeg 生成缩略图失败: {error_msg}")
            raise RuntimeError(f"无法生成缩略图: {error_msg}") from e

    @staticmethod
    def extract_all(video_path: str, thumbnail_dir: str) -> dict:
        metadata = VideoMetadataExtractor.extract_metadata(video_path)

        video_name = Path(video_path).stem
        thumbnail_path = os.path.join(thumbnail_dir, f"{video_name}_thumb.jpg")

        try:
            VideoMetadataExtractor.generate_thumbnail(video_path, thumbnail_path)
            metadata["thumbnail_path"] = thumbnail_path
        except Exception as e:
            logger.warning(f"生成缩略图失败，跳过: {e}")
            metadata["thumbnail_path"] = ""

        return metadata
