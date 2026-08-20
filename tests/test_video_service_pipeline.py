import json
import unittest
from unittest.mock import MagicMock, Mock, patch

from models.enums import GenerateTaskCallerType, GenerateTaskType
from models.storyboard import Storyboard, ShotSize
from models.video_generation_request import VideoScene
from models.provider_config import ProviderConfig
from service.video_service import VideoService


def _make_storyboard(**kwargs) -> Storyboard:
    defaults = {
        "scene_number": 1,
        "shot_number": 1,
        "id": 42,
        "scene_id": 1,
        "shot_size": ShotSize.MEDIUM_SHOT,
        "camera_movement": "推镜",
        "content": "小明推开门，阳光从窗户洒进来",
        "sound_effect": "开门声",
        "ambient_sound": "",
        "background_music": "",
        "duration": 5.0,
        "notes": "",
        "design_image": "",
        "seed": "",
    }
    defaults.update(kwargs)
    return Storyboard(**defaults)


class TestVideoServicePipeline(unittest.TestCase):
    def setUp(self):
        self.config = Mock()
        self.config.get_provider_config.return_value = ProviderConfig(
            provider_name="dashscope",
            api_key="test-key",
            default_model="wan2.7-t2v",
        )

        self.task_repo = Mock()
        self.task_repo.add.return_value = 101
        self.take_repo = Mock()
        self.take_repo.get_next_number.return_value = 1
        self.task_repo.get_by_provider_task_id.return_value = {
            "id": 101,
            "provider_name": "dashscope",
            "local_path": "projects/1/1-1-1.mp4",
            "request_params": json.dumps({
                "scene": VideoScene.SHOT_VIDEO.value,
                "storyboard_id": 42,
                "local_path": "projects/1/1-1-1.mp4",
                "provider_name": "dashscope",
                "project_id": 1,
                "project_name": "测试项目",
                "scene_id": 1,
                "scene_number": 1,
                "shot_number": 1,
                "reference_images": [],
                "reference_images_info": [],
                "visual_style": "",
                "params": {"prompt_extend": True},
                "prev_shot_last_frame": "",
                "clean_prompt": True,
            }),
            "completed": False,
        }

        self.session_manager = Mock()
        def get_repo(repo_class):
            name = getattr(repo_class, "__name__", str(repo_class))
            if "GenerateTask" in name:
                return self.task_repo
            return self.take_repo

        self.session_manager.get_repo.side_effect = get_repo

        self.chat_service = Mock()
        self.chat_service.chat.return_value = (" refined prompt ", 202)

        self.prompt_builder = Mock()
        self.prompt_builder.assemble_video_shot_prompt.return_value = "raw prompt"
        self.prompt_builder.build_video_prompt_clean_messages.return_value = [
            {"role": "user", "content": "clean"},
        ]

        self.storyboard_service = Mock()
        self.storyboard_service.get_storyboard.return_value = _make_storyboard()
        self.screenplay_service = Mock()
        self.screenplay_service.get_scene.return_value = None

        self.provider = Mock()
        self.provider._config = ProviderConfig(
            provider_name="dashscope",
            default_model="wan2.7-t2v",
        )
        self.provider.t2v.return_value = ("real-provider-task", {"json": {"input": {"prompt": "x"}}}, 303)

        self.video_service = VideoService(
            session_manager=self.session_manager,
            config=self.config,
            chat_service=self.chat_service,
            prompt_builder=self.prompt_builder,
            storyboard_service=self.storyboard_service,
            screenplay_service=self.screenplay_service,
            workspace_root="/tmp/workspace",
        )
        self.video_service.get_provider = Mock(return_value=self.provider)
        self.video_service._coordinator = Mock()
        self.video_service._coordinator.is_caller_active.return_value = False

    @patch("service.video_service.paths.workspace_root", return_value="/workspace")
    @patch("service.video_service.to_relative_path", return_value="projects/1/1-1-1.mp4")
    @patch("service.video_service.uuid.uuid4", return_value="pending-task-123")
    def test_start_shot_video_creates_pending_task_before_provider(self, *_mocks):
        from models.video_generation_request import VideoGenerationRequest

        self.video_service._coordinator.start = Mock()
        request = VideoGenerationRequest(
            scene=VideoScene.SHOT_VIDEO,
            storyboard_id=42,
            local_path="",
            provider_name="dashscope",
            project_id=1,
            project_name="测试项目",
            scene_number=1,
            shot_number=1,
        )
        provider_task_id = self.video_service.start_shot_video(request)

        self.assertEqual(provider_task_id, "pending-task-123")
        add_kwargs = self.task_repo.add.call_args.kwargs
        self.assertEqual(add_kwargs["type"], GenerateTaskType.VIDEO)
        self.assertEqual(add_kwargs["caller_type"], GenerateTaskCallerType.STORYBOARD)
        self.assertEqual(add_kwargs["caller_id"], "42")
        self.assertEqual(add_kwargs["provider_task_id"], "pending-task-123")
        self.video_service._coordinator.start.assert_called_once()

    def test_execute_submit_pipeline_chat_parent_ids_and_status_flow(self):
        final_id = self.video_service.execute_submit_pipeline("pending-task-123")

        self.assertEqual(final_id, "real-provider-task")
        self.task_repo.update_status.assert_any_call(101, "running")
        self.task_repo.update_status.assert_any_call(101, "pending")
        self.task_repo.update_provider_task_id.assert_not_called()

        chat_kwargs = self.chat_service.chat.call_args.kwargs
        self.assertEqual(chat_kwargs["parent_ids"], "101")

    def test_execute_submit_pipeline_failure_marks_task_failed(self):
        self.provider.t2v.side_effect = RuntimeError("provider failed")

        with self.assertRaises(RuntimeError):
            self.video_service.execute_submit_pipeline("pending-task-123")

        self.task_repo.update_status.assert_any_call(101, "failed", error_message="provider failed")
        self.task_repo.mark_completed.assert_called_with(101)

    @patch("service.video_service.paths.workspace_root", return_value="/workspace")
    @patch("service.video_service.to_relative_path", return_value="projects/1/1-1-1.mp4")
    def test_create_pending_task_creates_take(self, *_mocks):
        from models.video_generation_request import VideoGenerationRequest

        request = VideoGenerationRequest(
            scene=VideoScene.SHOT_VIDEO,
            storyboard_id=42,
            local_path="",
            provider_name="dashscope",
            project_id=1,
            scene_number=1,
            shot_number=1,
        )
        pending_id, task_id = self.video_service._create_pending_task(request)

        self.assertEqual(task_id, 101)
        self.take_repo.create.assert_called_once()
        create_kwargs = self.take_repo.create.call_args.kwargs
        self.assertEqual(create_kwargs["dto"].storyboard_id, 42)
        self.assertEqual(create_kwargs["dto"].generate_task_id, 101)


if __name__ == "__main__":
    unittest.main()
