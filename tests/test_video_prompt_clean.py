import unittest
from unittest.mock import Mock, patch

from models.storyboard import Storyboard, ShotSize
from models.scene import Scene, SceneLocation, SceneTime
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

    @patch.object(VideoService, "submit_task", return_value="provider-task-1")
    def test_submit_shot_video_with_clean(self, mock_submit_task):
        """VideoService 内部调用 ChatService 清理提示词"""
        storyboard = _make_storyboard()
        scene = _make_scene()

        mock_chat_service = Mock()
        mock_chat_service.clean_video_prompt.return_value = ("""【场景上下文】第 1 场 · 内景 · 客厅 · 日
小明走进客厅，看到妈妈在做饭。

【镜头画面】小明推开门，阳光从窗户洒进来

【镜头参数】景别：中景 | 运镜：推镜

【音效】开门声""", 1)

        video_service = VideoService(
            session_manager=Mock(),
            config=Mock(),
            chat_service=mock_chat_service,
        )

        result = video_service.submit_shot_video(
            storyboard=storyboard,
            scene=scene,
            provider_name="dashscope",
            project_id=1,
            project_name="测试项目",
        )

        mock_chat_service.clean_video_prompt.assert_called_once()
        mock_submit_task.assert_called_once()
        submitted_prompt = mock_submit_task.call_args.kwargs["prompt"]
        self.assertNotIn("妈妈，我回来了", submitted_prompt)
        self.assertNotIn("背景传来电视新闻的声音", submitted_prompt)
        self.assertIn("小明走进客厅", submitted_prompt)
        self.assertIn("【音效】开门声", submitted_prompt)
        self.assertEqual(result, "provider-task-1")

    @patch.object(VideoService, "submit_task", return_value="provider-task-2")
    def test_submit_shot_video_clean_continuity_hints(self, mock_submit_task):
        """清理连贯性提示中的对话"""
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

        mock_chat_service = Mock()
        mock_chat_service.clean_video_prompt.return_value = ("""【镜头画面】妈妈转过身，微笑着看向小明

【镜头参数】景别：近景

【连贯性提示】前一镜：小明站在门外，犹豫地举起手准备敲门... | 后一镜：两人拥抱在一起...""", 1)

        video_service = VideoService(
            session_manager=Mock(),
            config=Mock(),
            chat_service=mock_chat_service,
        )

        video_service.submit_shot_video(
            storyboard=storyboard,
            prev_shot=prev_shot,
            next_shot=next_shot,
            provider_name="dashscope",
        )

        submitted_prompt = mock_submit_task.call_args.kwargs["prompt"]
        self.assertNotIn("要不要进去呢", submitted_prompt)
        self.assertNotIn("你终于回来了", submitted_prompt)
        self.assertNotIn("炒菜的滋滋声", submitted_prompt)

    @patch.object(VideoService, "submit_task", return_value="provider-task-3")
    def test_submit_shot_video_clean_failure_fallback(self, mock_submit_task):
        """清理失败时使用原始提示词"""
        storyboard = _make_storyboard(content="测试内容", camera_movement="", sound_effect="")

        mock_chat_service = Mock()
        mock_chat_service.clean_video_prompt.side_effect = Exception("API 调用失败")

        video_service = VideoService(
            session_manager=Mock(),
            config=Mock(),
            chat_service=mock_chat_service,
        )

        video_service.submit_shot_video(
            storyboard=storyboard,
            provider_name="dashscope",
        )

        submitted_prompt = mock_submit_task.call_args.kwargs["prompt"]
        self.assertIn("测试内容", submitted_prompt)


if __name__ == "__main__":
    unittest.main()
