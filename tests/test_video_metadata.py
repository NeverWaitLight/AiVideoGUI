import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.video_metadata import VideoMetadataExtractor


class TestVideoMetadataExtractor(unittest.TestCase):
    def test_parse_duration_and_video_size_from_ffmpeg_stderr(self):
        stderr = (
            "Input #0, mov, from 'demo.mp4':\n"
            "  Duration: 00:00:05.12, start: 0.000000, bitrate: 1234 kb/s\n"
            "  Stream #0:0: Video: h264 (High), yuv420p, 1280x720, 24 fps\n"
        )
        self.assertAlmostEqual(VideoMetadataExtractor._parse_duration(stderr), 5.12)
        self.assertEqual(VideoMetadataExtractor._parse_video_size(stderr), (1280, 720))

    def test_extract_metadata_uses_ffmpeg_not_ffprobe(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = str(Path(tmp_dir) / "demo.mp4")
            Path(video_path).write_bytes(b"fake-video")
            stderr = (
                "Duration: 00:00:03.50, start: 0.000000, bitrate: 800 kb/s\n"
                "Stream #0:0: Video: h264, yuv420p, 640x360, 25 fps\n"
            )
            with patch.object(VideoMetadataExtractor, "_run_ffmpeg") as mock_run, patch.object(
                VideoMetadataExtractor,
                "_resolve_ffmpeg_exe",
                return_value="ffmpeg",
            ):
                mock_run.return_value.returncode = 1
                mock_run.return_value.stderr = stderr
                mock_run.return_value.stdout = ""
                metadata = VideoMetadataExtractor.extract_metadata(video_path)

            self.assertEqual(metadata["duration"], 3.5)
            self.assertEqual(metadata["width"], 640)
            self.assertEqual(metadata["height"], 360)
            self.assertEqual(metadata["file_size"], len(b"fake-video"))
            self.assertEqual(mock_run.call_args.args[0][0], "ffmpeg")
            self.assertNotIn("ffprobe", mock_run.call_args.args[0][0])

    def test_generate_thumbnail_none_offset_uses_first_keyframe(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = str(Path(tmp_dir) / "demo.mp4")
            output_path = str(Path(tmp_dir) / "thumb.jpg")
            Path(video_path).write_bytes(b"fake")

            with patch.object(VideoMetadataExtractor, "_extract_frame") as mock_extract:
                VideoMetadataExtractor.generate_thumbnail(
                    video_path,
                    output_path,
                    time_offset=None,
                    duration=5.0,
                )

            mock_extract.assert_called_once_with(
                video_path,
                output_path,
                first_keyframe=True,
            )


if __name__ == "__main__":
    unittest.main()
