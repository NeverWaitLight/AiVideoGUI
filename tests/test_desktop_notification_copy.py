import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from service.desktop_notification_service import build_notify_texts


class TestBuildNotifyTexts(unittest.TestCase):
    def setUp(self) -> None:
        self.session_manager = MagicMock()

    def test_cover_success_title(self) -> None:
        task = {
            "id": 1,
            "type": "image",
            "caller_type": "cover",
            "caller_id": "10",
            "request_params": json.dumps({"scene": "project_cover"}),
            "error_message": "",
        }
        title, body = build_notify_texts(self.session_manager, task, True)
        self.assertEqual(title, "项目封面图生成完成")
        self.assertEqual(body, "点击查看")

    def test_cover_failure_title(self) -> None:
        task = {
            "id": 1,
            "type": "image",
            "caller_type": "cover",
            "caller_id": "10",
            "request_params": "{}",
            "error_message": "封面失败",
        }
        title, body = build_notify_texts(self.session_manager, task, False)
        self.assertEqual(title, "项目封面图生成失败")
        self.assertEqual(body, "封面失败")

    def test_character_with_name_from_params(self) -> None:
        task = {
            "id": 2,
            "type": "image",
            "caller_type": "character",
            "caller_id": "uuid-1",
            "request_params": json.dumps({"character_name": "小明"}),
            "error_message": "",
        }
        title, body = build_notify_texts(self.session_manager, task, True)
        self.assertEqual(title, "角色小明设计图生成完成")
        self.assertEqual(body, "点击查看")

    def test_character_name_fallback_from_repo(self) -> None:
        character_repo = MagicMock()
        character_repo.get_by_id.return_value = SimpleNamespace(name="阿花")
        self.session_manager.get_repo.return_value = character_repo
        task = {
            "id": 3,
            "type": "image",
            "caller_type": "character",
            "caller_id": "uuid-2",
            "request_params": json.dumps({}),
            "error_message": "",
        }
        title, _body = build_notify_texts(self.session_manager, task, True)
        self.assertEqual(title, "角色阿花设计图生成完成")

    @patch("storage.repositories.storyboard_repository.StoryboardRepository")
    def test_storyboard_design_image(self, _mock_repo_cls) -> None:
        storyboard_repo = MagicMock()
        storyboard_repo.get_by_id.return_value = SimpleNamespace(scene_number=1, shot_number=2)
        self.session_manager.get_repo.return_value = storyboard_repo
        task = {
            "id": 4,
            "type": "image",
            "caller_type": "storyboard",
            "caller_id": "99",
            "request_params": json.dumps({"scene": "storyboard_design"}),
            "error_message": "",
        }
        title, body = build_notify_texts(self.session_manager, task, True)
        self.assertEqual(title, "1场2镜设计图生成完成")
        self.assertEqual(body, "点击查看")

    @patch("storage.repositories.storyboard_take_repository.StoryboardTakeRepository")
    def test_video_with_scene_shot_take(self, _mock_repo_cls) -> None:
        take_repo = MagicMock()
        take_repo.get_by_generate_task_id.return_value = SimpleNamespace(number=3)
        self.session_manager.get_repo.return_value = take_repo
        task = {
            "id": 5,
            "type": "video",
            "caller_type": "storyboard",
            "caller_id": "88",
            "request_params": json.dumps({"scene_number": 2, "shot_number": 5}),
            "error_message": "",
        }
        title, body = build_notify_texts(self.session_manager, task, True)
        self.assertEqual(title, "2场5镜3次生成完成")
        self.assertEqual(body, "点击查看")

    def test_fallback_generic_image_title(self) -> None:
        storyboard_repo = MagicMock()
        storyboard_repo.get_by_id.return_value = None
        self.session_manager.get_repo.return_value = storyboard_repo
        task = {
            "id": 6,
            "type": "image",
            "caller_type": "storyboard",
            "caller_id": "404",
            "request_params": "{}",
            "error_message": "",
        }
        title, body = build_notify_texts(self.session_manager, task, True)
        self.assertEqual(title, "图片生成完成")
        self.assertEqual(body, "点击查看")

    def test_fallback_generic_video_when_take_missing(self) -> None:
        take_repo = MagicMock()
        take_repo.get_by_generate_task_id.return_value = None
        self.session_manager.get_repo.return_value = take_repo
        task = {
            "id": 7,
            "type": "video",
            "caller_type": "storyboard",
            "caller_id": "88",
            "request_params": json.dumps({"scene_number": 1, "shot_number": 1}),
            "error_message": "",
        }
        title, _body = build_notify_texts(self.session_manager, task, True)
        self.assertEqual(title, "视频生成完成")

    def test_error_body_truncated(self) -> None:
        task = {
            "id": 8,
            "type": "image",
            "caller_type": "cover",
            "caller_id": "1",
            "request_params": "{}",
            "error_message": "e" * 200,
        }
        _title, body = build_notify_texts(self.session_manager, task, False)
        self.assertEqual(len(body), 120)
        self.assertTrue(body.endswith("..."))


if __name__ == "__main__":
    unittest.main(verbosity=2)
