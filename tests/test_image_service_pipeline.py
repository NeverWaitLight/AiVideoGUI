import json
import unittest
from unittest.mock import MagicMock, Mock, patch

from models.enums import GenerateTaskCallerType, GenerateTaskType
from models.image_generation_request import ImageScene
from models.provider_config import ProviderConfig
from service.image_service import ImageService


class TestImageServicePipeline(unittest.TestCase):
    def setUp(self):
        self.config_manager = Mock()
        self.config_manager.settings.default_image_provider = "dashscope"
        self.config_manager.resolve_config_for_type.return_value = ProviderConfig(
            provider_name="dashscope",
            api_key="test-key",
            default_model="wan2.6-t2i",
        )

        self.task_repo = Mock()
        self.task_repo.add.return_value = 101
        self.task_repo.get_by_provider_task_id.return_value = {
            "id": 101,
            "provider_name": "dashscope",
            "local_path": "projects/1/design-1-1.png",
            "request_params": json.dumps({
                "scene": ImageScene.STORYBOARD_DESIGN.value,
                "local_path": "projects/1/design-1-1.png",
                "caller_type": GenerateTaskCallerType.STORYBOARD.value,
                "caller_id": "42",
                "project_id": 1,
                "size": "1696*960",
                "config_name": "dashscope",
                "content": "主角站在窗前",
                "shot_size": "中景",
                "camera_movement": "固定",
                "notes": "",
                "character_info": "",
                "visual_style": "",
                "module": "storyboard",
                "context": "分镜设计图生成",
            }),
            "completed": False,
        }

        self.session_manager = Mock()
        self.session_manager.get_repo.return_value = self.task_repo

        self.chat_service = Mock()
        self.chat_service.chat.return_value = (" refined prompt ", 202)

        self.prompt_builder = Mock()
        self.prompt_builder.build_design_image_prompt_messages.return_value = [
            {"role": "user", "content": "test"},
        ]

        self.storyboard_service = Mock()
        self.character_service = Mock()
        self.project_service = Mock()

        self.image_service = ImageService(
            config_manager=self.config_manager,
            session_manager=self.session_manager,
            chat_service=self.chat_service,
            prompt_builder=self.prompt_builder,
            storyboard_service=self.storyboard_service,
            character_service=self.character_service,
            project_service=self.project_service,
            workspace_root="/tmp/workspace",
        )
        self.image_service._coordinator = Mock()
        self.image_service._coordinator.is_caller_active.return_value = False

    @patch("service.image_service.uuid.uuid4", return_value="image-task-123")
    def test_start_storyboard_creates_pending_image_task(self, _mock_uuid):
        self.image_service._coordinator.start = Mock()
        provider_task_id = self.image_service.start_storyboard_design_image(
            content="主角站在窗前",
            storyboard_id=42,
            project_id=1,
            scene_number=1,
            shot_number=1,
        )

        self.assertEqual(provider_task_id, "image-task-123")
        self.image_service._coordinator.start.assert_called_once()
        add_kwargs = self.task_repo.add.call_args.kwargs
        self.assertEqual(add_kwargs["type"], GenerateTaskType.IMAGE)
        self.assertEqual(add_kwargs["caller_type"], GenerateTaskCallerType.STORYBOARD)
        self.assertEqual(add_kwargs["caller_id"], "42")

        request_params = json.loads(add_kwargs["request_params"])
        self.assertEqual(request_params["scene"], ImageScene.STORYBOARD_DESIGN.value)
        self.assertNotIn("prompt", request_params)

    @patch("service.image_service._get_image_provider")
    def test_execute_pipeline_chat_parent_ids_and_status_flow(self, mock_get_provider):
        provider = Mock()
        provider.generate.return_value = ("https://example.com/a.png", {})
        provider.download.return_value = "/tmp/workspace/projects/1/design-1-1.png"
        mock_get_provider.return_value = provider

        relative_path = self.image_service.execute_pipeline("image-task-123")

        self.task_repo.update_status.assert_any_call(101, "running")
        self.task_repo.update_status.assert_any_call(101, "succeeded", remote_url="https://example.com/a.png")
        self.task_repo.mark_completed.assert_called_once_with(101)

        chat_kwargs = self.chat_service.chat.call_args.kwargs
        self.assertEqual(chat_kwargs["parent_ids"], "101")

        self.storyboard_service.update_storyboard.assert_called_once_with(
            storyboard_id=42,
            design_image="/tmp/workspace/projects/1/design-1-1.png",
        )
        self.assertEqual(relative_path, "projects/1/design-1-1.png")

    @patch("service.image_service._get_image_provider")
    def test_execute_pipeline_failure_marks_task_failed(self, mock_get_provider):
        self.chat_service.chat.side_effect = RuntimeError("chat failed")

        with self.assertRaises(RuntimeError):
            self.image_service.execute_pipeline("image-task-123")

        self.task_repo.update_status.assert_any_call(101, "failed", error_message="chat failed")
        self.task_repo.mark_completed.assert_called_with(101)


if __name__ == "__main__":
    unittest.main()
