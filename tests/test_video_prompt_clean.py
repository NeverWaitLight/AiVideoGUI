import unittest
from unittest.mock import Mock, patch

from models.storyboard import Storyboard, ShotSize
from models.scene import Scene, SceneLocation, SceneTime
from models.video_generation_request import VideoGenerationRequest, VideoScene
from prompts.video_prompt_builder import VideoPromptBuilder
from service.video_service import VideoService


def _make_storyboard(**kwargs) -> Storyboard:
    defaults = {
        "scene_number": 1,
        "shot_number": 1,
        "id": 1,
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


def _make_scene(**kwargs) -> Scene:
    defaults = {
        "id": 1,
        "project_id": 1,
        "scene_number": 1,
        "location_type": SceneLocation.INTERIOR,
        "location": "客厅",
        "time_type": SceneTime.DAY,
        "time_detail": "",
        "content": '小明走进客厅，看到妈妈在做饭。"妈妈，我回来了！"他高兴地说。背景传来电视新闻的声音。',
    }
    defaults.update(kwargs)
    return Scene(**defaults)


def _make_video_service(mock_chat_service: Mock) -> VideoService:
    return VideoService(
        session_manager=Mock(),
        config=Mock(),
        chat_service=mock_chat_service,
        prompt_builder=Mock(),
        storyboard_service=Mock(),
        screenplay_service=Mock(),
        workspace_root="/tmp/workspace",
    )


class TestVideoPromptClean(unittest.TestCase):
    def test_build_shot_prompt_includes_dialogue(self):
        """本地拼接保留场景对话和音效"""
        storyboard = _make_storyboard()
        scene = _make_scene()

        prompt = VideoPromptBuilder.build_shot_prompt(
            storyboard=storyboard,
            scene=scene,
        )

        self.assertIn("妈妈，我回来了", prompt)
        self.assertIn("背景传来电视新闻的声音", prompt)
        self.assertIn("【音效】开门声", prompt)

    @patch.object(VideoService, "start_shot_video", return_value="provider-task-1")
    def test_submit_shot_video_delegates_to_start_shot_video(self, mock_start):
        """VideoService.submit_shot_video 转调 start_shot_video"""
        storyboard = _make_storyboard()
        scene = _make_scene()

        video_service = _make_video_service(Mock())

        result = video_service.submit_shot_video(
            storyboard=storyboard,
            scene=scene,
            provider_name="dashscope",
            project_id=1,
            project_name="测试项目",
        )

        mock_start.assert_called_once()
        request = mock_start.call_args.args[0]
        self.assertIsInstance(request, VideoGenerationRequest)
        self.assertEqual(request.scene, VideoScene.SHOT_VIDEO)
        self.assertTrue(mock_start.call_args.kwargs["wait_submit"])
        self.assertEqual(result, "provider-task-1")

    def test_execute_submit_pipeline_uses_chat_for_clean_prompt(self):
        import json

        mock_chat_service = Mock()
        mock_chat_service.chat.return_value = ("cleaned prompt", 1)

        prompt_builder = Mock()
        prompt_builder.assemble_video_shot_prompt.return_value = "raw with dialogue"
        prompt_builder.build_video_prompt_clean_messages.return_value = [{"role": "user", "content": "x"}]

        storyboard_service = Mock()
        storyboard_service.get_storyboard.return_value = _make_storyboard()

        task_repo = Mock()
        task_repo.get_by_provider_task_id.return_value = {
            "id": 101,
            "provider_name": "dashscope",
            "request_params": json.dumps({
                "scene": VideoScene.SHOT_VIDEO.value,
                "storyboard_id": 1,
                "local_path": "",
                "provider_name": "dashscope",
                "clean_prompt": True,
            }),
        }
        session_manager = Mock()
        session_manager.get_repo.return_value = task_repo

        video_service = VideoService(
            session_manager=session_manager,
            config=Mock(),
            chat_service=mock_chat_service,
            prompt_builder=prompt_builder,
            storyboard_service=storyboard_service,
            screenplay_service=Mock(),
            workspace_root="/tmp/workspace",
        )

        with patch.object(video_service, "_call_provider", return_value=("provider-task-1", {"json": {}})) as mock_call:
            video_service.execute_submit_pipeline("pending-id")

        mock_chat_service.chat.assert_called_once()
        self.assertEqual(mock_call.call_args.kwargs["prompt"], "cleaned prompt")

    @patch.object(VideoService, "start_shot_video", return_value="provider-task-2")
    def test_submit_shot_video_clean_continuity_hints(self, mock_start):
        storyboard = _make_storyboard(
            shot_number=2,
            id=2,
            shot_size=ShotSize.CLOSE_UP,
            camera_movement="",
            content="妈妈转过身，微笑着看向小明",
            sound_effect="",
        )
        prev_shot = _make_storyboard(
            shot_number=1,
            content='小明站在门外，犹豫地举起手准备敲门。"要不要进去呢？"他自言自语',
            sound_effect="",
        )
        next_shot = _make_storyboard(
            shot_number=3,
            id=3,
            shot_size=ShotSize.FULL_SHOT,
            content='两人拥抱在一起。厨房里传来炒菜的滋滋声，妈妈说："你终于回来了"',
            sound_effect="",
        )

        video_service = _make_video_service(Mock())
        video_service.submit_shot_video(
            storyboard=storyboard,
            prev_shot=prev_shot,
            next_shot=next_shot,
            provider_name="dashscope",
        )

        request = mock_start.call_args.args[0]
        self.assertEqual(request.prev_shot_id, prev_shot.id)
        self.assertEqual(request.next_shot_id, next_shot.id)

    @patch.object(VideoService, "execute_submit_pipeline")
    def test_execute_submit_pipeline_clean_failure_fallback(self, _mock_execute):
        storyboard = _make_storyboard(content="测试内容", camera_movement="", sound_effect="")

        mock_chat_service = Mock()
        mock_chat_service.chat.side_effect = Exception("API 调用失败")

        prompt_builder = Mock()
        prompt_builder.assemble_video_shot_prompt.return_value = "测试内容"
        prompt_builder.build_video_prompt_clean_messages.return_value = [{"role": "user", "content": "x"}]

        storyboard_service = Mock()
        storyboard_service.get_storyboard.return_value = storyboard

        import json
        task_repo = Mock()
        task_repo.get_by_provider_task_id.return_value = {
            "id": 1,
            "provider_name": "dashscope",
            "request_params": json.dumps({
                "scene": VideoScene.SHOT_VIDEO.value,
                "storyboard_id": 1,
                "local_path": "",
                "provider_name": "dashscope",
                "clean_prompt": True,
            }),
        }
        session_manager = Mock()
        session_manager.get_repo.return_value = task_repo

        video_service = VideoService(
            session_manager=session_manager,
            config=Mock(),
            chat_service=mock_chat_service,
            prompt_builder=prompt_builder,
            storyboard_service=storyboard_service,
            screenplay_service=Mock(),
            workspace_root="/tmp/workspace",
        )

        with patch.object(video_service, "_call_provider", return_value=("task", {"json": {}})) as mock_call:
            video_service.execute_submit_pipeline("pending-id")
            submitted_prompt = mock_call.call_args.kwargs["prompt"]
            self.assertIn("测试内容", submitted_prompt)


if __name__ == "__main__":
    unittest.main()
