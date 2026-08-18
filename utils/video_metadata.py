import os
import re
import shutil
import subprocess
from pathlib import Path

from imageio_ffmpeg import get_ffmpeg_exe
from loguru import logger


class VideoMetadataExtractor:
    _THUMBNAIL_SCALE = "scale=320:-1"

    @staticmethod
    def _resolve_ffmpeg_exe() -> str:
        ffmpeg_exe = get_ffmpeg_exe()
        if not os.path.exists(ffmpeg_exe):
            ffmpeg_exe = shutil.which("ffmpeg")
            if not ffmpeg_exe:
                raise RuntimeError("找不到 ffmpeg 可执行文件，请安装 ffmpeg 到系统 PATH")
        return ffmpeg_exe

    @staticmethod
    def _run_ffmpeg(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    @staticmethod
    def _parse_duration(text: str) -> float:
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
        if not match:
            return 0.0
        hours, minutes, seconds = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    @staticmethod
    def _parse_video_size(text: str) -> tuple[int, int]:
        match = re.search(r"Video:.*?\b(\d{2,5})x(\d{2,5})\b", text, re.DOTALL)
        if not match:
            return 0, 0
        return int(match.group(1)), int(match.group(2))

    @staticmethod
    def _probe_with_ffmpeg(video_path: str) -> str:
        """imageio-ffmpeg 只内置 ffmpeg 不带 ffprobe 用 ffmpeg -i 解析元数据。"""
        ffmpeg_exe = VideoMetadataExtractor._resolve_ffmpeg_exe()
        result = VideoMetadataExtractor._run_ffmpeg([ffmpeg_exe, "-i", video_path])
        # ffmpeg -i 在没有输出目标时通常返回非 0 但 stderr 仍含媒体信息
        probe_text = (result.stderr or "") + "\n" + (result.stdout or "")
        if "Duration:" not in probe_text and "Video:" not in probe_text:
            raise RuntimeError(f"ffmpeg 读取媒体信息失败: {result.stderr}")
        return probe_text

    @staticmethod
    def extract_metadata(video_path: str) -> dict:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        try:
            probe_text = VideoMetadataExtractor._probe_with_ffmpeg(video_path)
            duration = VideoMetadataExtractor._parse_duration(probe_text)
            width, height = VideoMetadataExtractor._parse_video_size(probe_text)
            file_size = os.path.getsize(video_path)

            if width <= 0 or height <= 0:
                raise RuntimeError("未找到视频流分辨率信息")

            logger.info(
                f"提取视频元数据: {video_path} ({duration:.1f}s, {width}x{height}, {file_size} bytes)"
            )

            return {
                "duration": duration,
                "width": width,
                "height": height,
                "file_size": file_size,
            }
        except Exception as e:
            logger.error(f"提取视频元数据失败: {e}")
            raise RuntimeError(f"无法提取视频元数据: {e}") from e

    @staticmethod
    def _extract_frame(
        video_path: str,
        output_path: str,
        *,
        time_offset: float | None = None,
        first_keyframe: bool = False,
        accurate_seek: bool = False,
        scale: bool = True,
        from_end: bool = False,
    ) -> None:
        ffmpeg_exe = VideoMetadataExtractor._resolve_ffmpeg_exe()
        cmd = [ffmpeg_exe]
        if from_end:
            cmd.extend(["-sseof", "-0.1"])
        if first_keyframe:
            cmd.extend(["-skip_frame", "nokey"])
        elif time_offset is not None and not accurate_seek and not from_end:
            cmd.extend(["-ss", str(time_offset)])
        cmd.extend(["-i", video_path])
        if time_offset is not None and not first_keyframe and accurate_seek and not from_end:
            cmd.extend(["-ss", str(time_offset)])
        if scale:
            cmd.extend(["-vf", VideoMetadataExtractor._THUMBNAIL_SCALE])
        cmd.extend([
            "-vframes", "1",
            "-f", "image2",
            "-c:v", "mjpeg",
            "-y",
            output_path,
        ])

        result = VideoMetadataExtractor._run_ffmpeg(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg 失败: {result.stderr}")

    @staticmethod
    def generate_thumbnail(
        video_path: str,
        output_path: str,
        time_offset: float | None = 1.0,
        duration: float | None = None,
    ) -> str:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            if time_offset is not None:
                VideoMetadataExtractor._extract_frame(
                    video_path,
                    output_path,
                    time_offset=time_offset,
                )
                logger.info(f"生成视频缩略图: {video_path} -> {output_path} (固定时间点 {time_offset}s)")
                return output_path

            VideoMetadataExtractor._extract_frame(
                video_path,
                output_path,
                first_keyframe=True,
            )
            logger.info(f"生成视频缩略图: {video_path} -> {output_path} (第一关键帧)")
            return output_path
        except Exception as e:
            logger.error(f"生成缩略图失败: {e}")
            raise RuntimeError(f"无法生成缩略图: {e}") from e

    @staticmethod
    def extract_first_last_frames(
        video_path: str,
        output_dir: str,
        duration: float = 0.0,
    ) -> dict[str, str]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        video_name = Path(video_path).stem
        first_frame_path = os.path.join(output_dir, f"{video_name}_first.jpg")
        last_frame_path = os.path.join(output_dir, f"{video_name}_last.jpg")
        result: dict[str, str] = {"first_frame_path": "", "last_frame_path": ""}

        try:
            VideoMetadataExtractor._extract_frame(
                video_path,
                first_frame_path,
                first_keyframe=True,
                scale=False,
            )
            result["first_frame_path"] = first_frame_path
            logger.info(f"提取视频首帧: {video_path} -> {first_frame_path}")
        except Exception as e:
            logger.warning(f"提取首帧失败，跳过: {e}")

        try:
            VideoMetadataExtractor._extract_frame(
                video_path,
                last_frame_path,
                from_end=True,
                scale=False,
            )
            result["last_frame_path"] = last_frame_path
            logger.info(f"提取视频末帧: {video_path} -> {last_frame_path}")
        except Exception as e:
            logger.warning(f"提取末帧失败，跳过: {e}")

        return result

    @staticmethod
    def extract_all(video_path: str, thumbnail_dir: str) -> dict:
        metadata = VideoMetadataExtractor.extract_metadata(video_path)

        video_name = Path(video_path).stem
        thumbnail_path = os.path.join(thumbnail_dir, f"{video_name}_thumb.jpg")

        try:
            VideoMetadataExtractor.generate_thumbnail(
                video_path,
                thumbnail_path,
                time_offset=None,
                duration=metadata.get("duration", 0.0),
            )
            metadata["thumbnail_path"] = thumbnail_path
        except Exception as e:
            logger.warning(f"生成缩略图失败，跳过: {e}")
            metadata["thumbnail_path"] = ""

        try:
            frame_paths = VideoMetadataExtractor.extract_first_last_frames(
                video_path,
                thumbnail_dir,
                duration=metadata.get("duration", 0.0),
            )
            metadata["first_frame_path"] = frame_paths.get("first_frame_path", "")
            metadata["last_frame_path"] = frame_paths.get("last_frame_path", "")
        except Exception as e:
            logger.warning(f"提取首尾帧失败，跳过: {e}")
            metadata["first_frame_path"] = ""
            metadata["last_frame_path"] = ""

        return metadata
