import unittest
from unittest.mock import MagicMock

from models.enums import ShotSize, TakeStatus
from models.media_file import MediaFile
from models.enums import MediaType
from models.storyboard import Storyboard
from models.storyboard_take import StoryboardTake
from service.prev_shot_frame_service import PrevShotFrameService


def _make_storyboard(**kwargs) -> Storyboard:
    defaults = {
        "id": 1,
        "scene_id": 101,
        "scene_number": 1,
        "shot_number": 1,
        "shot_size": ShotSize.MEDIUM_SHOT,
        "content": "test",
    }
    defaults.update(kwargs)
    return Storyboard(**defaults)


class TestPrevShotFrameService(unittest.TestCase):

    def setUp(self):
        self.take_service = MagicMock()
        self.media_service = MagicMock()
        self.session_manager = MagicMock()
        self.service = PrevShotFrameService(
            session_manager=self.session_manager,
            take_service=self.take_service,
            media_service=self.media_service,
        )

    def test_should_use_prev_frame_same_scene(self):
        prev = _make_storyboard(id=1, scene_id=10, shot_number=1)
        current = _make_storyboard(id=2, scene_id=10, shot_number=2)
        self.assertTrue(self.service.should_use_prev_frame(prev, current, cross_scene=False))

    def test_should_not_use_prev_frame_cross_scene_default(self):
        prev = _make_storyboard(id=1, scene_id=10, shot_number=5)
        current = _make_storyboard(id=2, scene_id=20, shot_number=1)
        self.assertFalse(self.service.should_use_prev_frame(prev, current, cross_scene=False))

    def test_should_use_prev_frame_when_cross_scene_enabled(self):
        prev = _make_storyboard(id=1, scene_id=10)
        current = _make_storyboard(id=2, scene_id=20)
        self.assertTrue(self.service.should_use_prev_frame(prev, current, cross_scene=True))

    def test_find_prev_shot_media_prefers_selected_take(self):
        selected_take = StoryboardTake(
            id=1, storyboard_id=5, number=1, media_file_id="media-a",
            status=TakeStatus.SELECTED,
        )
        latest_take = StoryboardTake(
            id=2, storyboard_id=5, number=2, media_file_id="media-b",
            status=TakeStatus.CANDIDATE,
        )
        self.take_service.list_by_storyboard.return_value = [latest_take, selected_take]
        media = MediaFile(
            id="media-a", filename="a.mp4", media_type=MediaType.VIDEO, local_path="/a.mp4",
        )
        self.media_service.get_file_by_id.return_value = media

        result = self.service.find_prev_shot_media(5)
        self.assertEqual(result.id, "media-a")
        self.media_service.get_file_by_id.assert_called_with("media-a")

    def test_find_prev_shot_media_falls_back_to_latest_with_media(self):
        takes = [
            StoryboardTake(id=1, storyboard_id=5, number=1, media_file_id="media-a", status=TakeStatus.CANDIDATE),
            StoryboardTake(id=2, storyboard_id=5, number=3, media_file_id="media-c", status=TakeStatus.CANDIDATE),
            StoryboardTake(id=3, storyboard_id=5, number=2, media_file_id="media-b", status=TakeStatus.CANDIDATE),
        ]
        self.take_service.list_by_storyboard.return_value = takes
        media = MediaFile(
            id="media-c", filename="c.mp4", media_type=MediaType.VIDEO, local_path="/c.mp4",
        )
        self.media_service.get_file_by_id.return_value = media

        result = self.service.find_prev_shot_media(5)
        self.assertEqual(result.id, "media-c")

    def test_find_prev_pending_provider_task_id(self):
        take = StoryboardTake(
            id=1, storyboard_id=5, number=1, media_file_id="",
            generate_task_id=99, status=TakeStatus.CANDIDATE,
        )
        self.take_service.list_by_storyboard.return_value = [take]

        task_repo = MagicMock()
        task_repo.get_task_info.return_value = (False, "running")
        task_repo.get_by_id.return_value = {"provider_task_id": "provider-123"}
        self.session_manager.get_repo.return_value = task_repo

        result = self.service.find_prev_pending_provider_task_id(5)
        self.assertEqual(result, "provider-123")

    def test_resolve_last_frame_path(self):
        prev = _make_storyboard(id=1, scene_id=10)
        current = _make_storyboard(id=2, scene_id=10, shot_number=2)
        media = MediaFile(
            id="media-a", filename="a.mp4", media_type=MediaType.VIDEO, local_path="/a.mp4",
        )
        self.take_service.list_by_storyboard.return_value = [
            StoryboardTake(id=1, storyboard_id=1, number=1, media_file_id="media-a", status=TakeStatus.SELECTED),
        ]
        self.media_service.get_file_by_id.return_value = media
        self.media_service.ensure_last_frame.return_value = "/frames/a_last.jpg"

        result = self.service.resolve_last_frame_path(prev, current, cross_scene=False)
        self.assertEqual(result, "/frames/a_last.jpg")
        self.media_service.ensure_last_frame.assert_called_once_with("media-a")


if __name__ == "__main__":
    unittest.main()
