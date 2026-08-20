import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

from models.enums import GenerateTaskCallerType, GenerateTaskType
from models.image_generation_request import ImageGenerationRequest, ImageScene
from models.provider_config import ProviderConfig
from service.image_service import ImageService
from utils.image_replace import replace_stored_image, try_remove_workspace_file


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
        self.storyboard_service.get_storyboard.return_value = Mock(design_image="")
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

    @patch("service.image_service.uuid.uuid4", return_value="image-task-456")
    def test_start_storyboard_uses_aspect_ratio_for_size(self, _mock_uuid):
        self.image_service._coordinator.start = Mock()
        self.image_service.start_storyboard_design_image(
            content="主角站在窗前",
            storyboard_id=42,
            project_id=1,
            scene_number=1,
            shot_number=1,
            aspect_ratio="9:16",
        )

        request_params = json.loads(self.task_repo.add.call_args.kwargs["request_params"])
        self.assertEqual(request_params["aspect_ratio"], "9:16")
        self.assertEqual(request_params["size"], "960*1696")

    @patch("service.image_service.uuid.uuid4", return_value="image-task-char")
    def test_start_character_design_uses_fixed_4_3_aspect_ratio(self, _mock_uuid):
        self.project_service.get_project.return_value = Mock(aspect_ratio="9:16")
        self.image_service._coordinator.start = Mock()
        self.image_service.start_character_design_image(
            character_uuid="uuid-1",
            character_name="测试角色",
            description="角色描述",
            project_id=1,
        )

        request_params = json.loads(self.task_repo.add.call_args.kwargs["request_params"])
        self.assertEqual(request_params["aspect_ratio"], "4:3")
        self.assertEqual(request_params["size"], "1472*1104")
        self.project_service.get_project.assert_not_called()

    @patch("service.image_service._get_image_provider")
    def test_execute_pipeline_chat_parent_ids_and_status_flow(self, mock_get_provider):
        provider = Mock()
        provider.generate.return_value = ("https://example.com/a.png", {}, 303)
        provider.download.return_value = "/tmp/workspace/projects/1/design-1-1.png"
        mock_get_provider.return_value = provider

        relative_path = self.image_service.execute_pipeline("image-task-123")

        self.task_repo.update_status.assert_any_call(101, "running")
        self.task_repo.update_status.assert_any_call(101, "succeeded")
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

    def test_apply_business_update_storyboard_replaces_db_and_removes_old_file(self):
        with tempfile.TemporaryDirectory() as workspace:
            old_rel = "projects/1/custom-old.png"
            new_rel = "projects/1/design-1-1.png"
            old_abs = os.path.join(workspace, old_rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(old_abs), exist_ok=True)
            with open(old_abs, "w", encoding="utf-8") as f:
                f.write("old")

            self.image_service._workspace_root = workspace
            self.storyboard_service.get_storyboard.return_value = Mock(
                design_image=old_rel,
            )

            request = ImageGenerationRequest(
                scene=ImageScene.STORYBOARD_DESIGN,
                local_path=new_rel,
                caller_type=GenerateTaskCallerType.STORYBOARD,
                caller_id="42",
            )
            new_abs = os.path.join(workspace, new_rel.replace("/", os.sep))
            self.image_service._apply_business_update(request, new_abs, new_rel)

            self.storyboard_service.update_storyboard.assert_called_once_with(
                storyboard_id=42,
                design_image=new_abs,
            )
            self.assertFalse(os.path.exists(old_abs))

    def test_apply_business_update_character_updates_design_image(self):
        with tempfile.TemporaryDirectory() as workspace:
            old_rel = "projects/1/char-old.png"
            new_rel = "projects/1/char-uuid-1.png"
            old_abs = os.path.join(workspace, old_rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(old_abs), exist_ok=True)
            with open(old_abs, "w", encoding="utf-8") as f:
                f.write("old")

            self.image_service._workspace_root = workspace
            self.character_service.get_character.return_value = Mock(
                design_image=old_rel,
            )

            request = ImageGenerationRequest(
                scene=ImageScene.CHARACTER_DESIGN,
                local_path=new_rel,
                caller_type=GenerateTaskCallerType.CHARACTER,
                caller_id="uuid-1",
            )
            new_abs = os.path.join(workspace, new_rel.replace("/", os.sep))
            self.image_service._apply_business_update(request, new_abs, new_rel)

            self.character_service.update_character.assert_called_once_with(
                character_uuid="uuid-1",
                design_image=new_abs,
            )
            self.assertFalse(os.path.exists(old_abs))

    def test_apply_business_update_cover_updates_cover_image(self):
        with tempfile.TemporaryDirectory() as workspace:
            old_rel = "projects/1/old-cover.png"
            new_rel = "projects/1/cover-1.png"
            old_abs = os.path.join(workspace, old_rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(old_abs), exist_ok=True)
            with open(old_abs, "w", encoding="utf-8") as f:
                f.write("old")

            self.image_service._workspace_root = workspace
            self.project_service.get_project.return_value = Mock(
                id=1,
                cover_image=old_rel,
            )
            self.project_service.update_cover_image.return_value = True

            request = ImageGenerationRequest(
                scene=ImageScene.PROJECT_COVER,
                local_path=new_rel,
                caller_type=GenerateTaskCallerType.COVER,
                caller_id="1",
            )
            new_abs = os.path.join(workspace, new_rel.replace("/", os.sep))
            self.image_service._apply_business_update(request, new_abs, new_rel)

            self.project_service.update_cover_image.assert_called_once_with(
                project_id=1,
                cover_image=new_rel,
            )
            self.assertFalse(os.path.exists(old_abs))

    def test_apply_business_update_raises_when_storyboard_missing(self):
        self.storyboard_service.get_storyboard.return_value = None
        request = ImageGenerationRequest(
            scene=ImageScene.STORYBOARD_DESIGN,
            local_path="projects/1/design-1-1.png",
            caller_type=GenerateTaskCallerType.STORYBOARD,
            caller_id="42",
        )
        with self.assertRaises(RuntimeError):
            self.image_service._apply_business_update(
                request,
                "/tmp/workspace/projects/1/design-1-1.png",
                "projects/1/design-1-1.png",
            )

    @patch("service.image_service.uuid.uuid4", return_value="image-task-wait")
    def test_start_storyboard_wait_returns_relative_path(self, _mock_uuid):
        self.image_service.execute_pipeline = Mock(
            return_value="projects/1/design-1-1.png",
        )
        relative_path = self.image_service.start_storyboard_design_image(
            content="主角站在窗前",
            storyboard_id=42,
            project_id=1,
            scene_number=1,
            shot_number=1,
            wait=True,
        )
        self.assertEqual(relative_path, "projects/1/design-1-1.png")
        self.image_service.execute_pipeline.assert_called_once_with("image-task-wait")


class TestImageReplace(unittest.TestCase):
    def test_replace_stored_image_removes_old_when_paths_differ(self):
        with tempfile.TemporaryDirectory() as workspace:
            old_rel = "projects/1/old.png"
            new_rel = "projects/1/new.png"
            old_abs = os.path.join(workspace, old_rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(old_abs), exist_ok=True)
            with open(old_abs, "w", encoding="utf-8") as f:
                f.write("old")

            replace_stored_image(workspace, old_rel, new_rel)
            self.assertFalse(os.path.exists(old_abs))

    def test_replace_stored_image_skips_when_paths_same(self):
        with tempfile.TemporaryDirectory() as workspace:
            rel = "projects/1/same.png"
            abs_path = os.path.join(workspace, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write("content")

            replace_stored_image(workspace, rel, rel)
            self.assertTrue(os.path.exists(abs_path))

    def test_try_remove_workspace_file_skips_outside_workspace(self):
        with tempfile.TemporaryDirectory() as workspace:
            outside = os.path.join(tempfile.gettempdir(), "outside-image-replace-test.png")
            with open(outside, "w", encoding="utf-8") as f:
                f.write("outside")
            try:
                try_remove_workspace_file(workspace, outside)
                self.assertTrue(os.path.exists(outside))
            finally:
                if os.path.exists(outside):
                    os.remove(outside)


if __name__ == "__main__":
    unittest.main()
