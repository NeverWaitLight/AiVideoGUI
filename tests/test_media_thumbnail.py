import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from models.enums import MediaType
from models.media_file import MediaFile
from service.media_service import MediaService
from utils.path_converter import to_qml_local_path


class TestMediaThumbnail(unittest.TestCase):
    def test_to_qml_local_path_normalizes_backslashes(self):
        self.assertEqual(
            to_qml_local_path(r"C:\foo\bar.jpg"),
            "C:/foo/bar.jpg",
        )

    def test_ensure_media_thumbnail_regenerates_missing_video_thumb(self):
        with tempfile.TemporaryDirectory() as tmp:
            video_path = os.path.join(tmp, "2-1-1.mp4")
            with open(video_path, "wb") as f:
                f.write(b"fake")

            media = MediaFile(
                id="mid-1",
                filename="2-1-1.mp4",
                media_type=MediaType.VIDEO,
                local_path=video_path,
                thumbnail_path=os.path.join(tmp, ".thumbnails", "2-1-1_thumb.jpg"),
            )

            session_manager = Mock()
            session_manager.get_repo.return_value = Mock()
            service = MediaService(session_manager=session_manager, workspace_root=tmp)

            with patch(
                "service.media_service.VideoMetadataExtractor.generate_thumbnail",
                return_value=os.path.join(tmp, ".thumbnails", "2-1-1_thumb.jpg"),
            ) as mock_gen:
                result = service._ensure_media_thumbnail(media)

            mock_gen.assert_called_once()
            self.assertTrue(result.thumbnail_path.endswith("2-1-1_thumb.jpg"))


if __name__ == "__main__":
    unittest.main()
