import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from utils.video_metadata import VideoMetadataExtractor


class TestVideoMetadataExtractor(unittest.TestCase):
    def test_is_informative_frame_rejects_pure_black(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            image_path = str(Path(tmp_dir) / "black.jpg")
            Image.new("RGB", (320, 180), color=(0, 0, 0)).save(image_path, quality=95)
            self.assertFalse(VideoMetadataExtractor._is_informative_frame(image_path))

    def test_is_informative_frame_accepts_content_frame(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            image_path = str(Path(tmp_dir) / "content.jpg")
            image = Image.new("RGB", (320, 180))
            pixels = [
                ((x * 7 + y * 11) % 255, (x * 3 + y * 5) % 255, (x + y) % 255)
                for y in range(180)
                for x in range(320)
            ]
            image.putdata(pixels)
            image.save(image_path, quality=95)
            self.assertTrue(VideoMetadataExtractor._is_informative_frame(image_path))

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

    def test_build_thumbnail_candidates_prioritizes_keyframe_and_post_black(self):
        candidates = VideoMetadataExtractor._build_thumbnail_candidates(duration=10.0, black_end=1.2)
        self.assertEqual(candidates[0], ("first_keyframe", None))
        self.assertEqual(candidates[1], ("post_black", 1.25))

    def test_detect_leading_black_end_parses_ffmpeg_output(self):
        stderr = (
            "[blackdetect @ 000001] black_start:0 black_end:1.533333 black_duration:1.533333\n"
        )
        with patch.object(VideoMetadataExtractor, "_run_ffmpeg") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stderr = stderr
            self.assertEqual(VideoMetadataExtractor._detect_leading_black_end("demo.mp4"), 1.533333)

    def test_generate_thumbnail_smart_mode_uses_first_informative_candidate(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = str(Path(tmp_dir) / "demo.mp4")
            output_path = str(Path(tmp_dir) / "thumb.jpg")
            Path(video_path).write_bytes(b"fake")

            with patch.object(
                VideoMetadataExtractor,
                "_detect_leading_black_end",
                return_value=0.0,
            ), patch.object(
                VideoMetadataExtractor,
                "_extract_frame",
            ) as mock_extract, patch.object(
                VideoMetadataExtractor,
                "_is_informative_frame",
                side_effect=[False, True],
            ), patch("utils.video_metadata.shutil.move") as mock_move:
                VideoMetadataExtractor.generate_thumbnail(
                    video_path,
                    output_path,
                    time_offset=None,
                    duration=5.0,
                )

            self.assertEqual(mock_extract.call_count, 2)
            first_call = mock_extract.call_args_list[0].kwargs
            second_call = mock_extract.call_args_list[1].kwargs
            self.assertTrue(first_call["first_keyframe"])
            self.assertEqual(second_call["time_offset"], 0.1)
            mock_move.assert_called_once()


if __name__ == "__main__":
    unittest.main()
