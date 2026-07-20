"""视频元数据提取功能测试。"""

import os
import tempfile
import unittest
from pathlib import Path

from utils.video_metadata import VideoMetadataExtractor


class TestVideoMetadataExtractor(unittest.TestCase):
    """测试 VideoMetadataExtractor 类。"""

    def test_extract_metadata_file_not_exist(self):
        """测试文件不存在时的异常处理。"""
        with self.assertRaises(FileNotFoundError):
            VideoMetadataExtractor.extract_metadata("nonexistent.mp4")

    def test_generate_thumbnail_file_not_exist(self):
        """测试生成缩略图时文件不存在的异常处理。"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "thumb.jpg")
            with self.assertRaises(FileNotFoundError):
                VideoMetadataExtractor.generate_thumbnail("nonexistent.mp4", output_path)

    # 注意：以下测试需要实际的视频文件才能运行
    # 如果要测试完整功能，需要准备测试视频文件

    def test_extract_all_with_real_video(self):
        """
        使用真实视频测试完整流程（需手动提供测试视频）。

        使用方法：
        1. 将测试视频放置在 tests/fixtures/sample.mp4
        2. 运行此测试
        """
        test_video = Path(__file__).parent / "fixtures" / "sample.mp4"
        if not test_video.exists():
            self.skipTest(f"测试视频不存在: {test_video}")

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = VideoMetadataExtractor.extract_all(str(test_video), tmp_dir)

            # 验证返回的字段
            self.assertIn("duration", result)
            self.assertIn("width", result)
            self.assertIn("height", result)
            self.assertIn("file_size", result)
            self.assertIn("thumbnail_path", result)

            # 验证数据类型
            self.assertIsInstance(result["duration"], float)
            self.assertIsInstance(result["width"], int)
            self.assertIsInstance(result["height"], int)
            self.assertIsInstance(result["file_size"], int)

            # 验证缩略图文件存在
            if result["thumbnail_path"]:
                self.assertTrue(os.path.exists(result["thumbnail_path"]))

            print(f"\n提取的元数据: {result}")


if __name__ == "__main__":
    unittest.main()
