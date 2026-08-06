import unittest
from unittest.mock import Mock, MagicMock
from models.storyboard import Storyboard, ShotSize
from models.scene import Scene, SceneLocation, SceneTime
from prompts.video_prompt_builder import VideoPromptBuilder


class TestVideoPromptClean(unittest.TestCase):
    def test_build_shot_prompt_without_clean(self):
        """测试不启用清理功能的基础场景"""
        storyboard = Storyboard(
            scene_number=1,
            shot_number=1,
            id=1,
            scene_id=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="推镜",
            content="小明推开门，阳光从窗户洒进来",
            sound_effect="开门声",
            ambient_sound="",
            background_music="",
            duration=5.0,
            notes="",
            design_image="",
            seed="",
        )

        scene = Scene(
            id=1,
            project_id=1,
            scene_number=1,
            location_type=SceneLocation.INTERIOR,
            location="客厅",
            time_type=SceneTime.DAY,
            time_detail="",
            content='小明走进客厅，看到妈妈在做饭。"妈妈，我回来了！"他高兴地说。背景传来电视新闻的声音。',
        )

        prompt = VideoPromptBuilder.build_shot_prompt(
            storyboard=storyboard,
            scene=scene,
            clean_dialogue_and_sound=False,
        )

        # 验证场景上下文包含对话和声音描述
        self.assertIn("妈妈，我回来了", prompt)
        self.assertIn("背景传来电视新闻的声音", prompt)
        self.assertIn("【音效】开门声", prompt)

    def test_build_shot_prompt_with_clean(self):
        """测试启用清理功能"""
        storyboard = Storyboard(
            scene_number=1,
            shot_number=1,
            id=1,
            scene_id=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="推镜",
            content="小明推开门，阳光从窗户洒进来",
            sound_effect="开门声",
            ambient_sound="",
            background_music="",
            duration=5.0,
            notes="",
            design_image="",
            seed="",
        )

        scene = Scene(
            id=1,
            project_id=1,
            scene_number=1,
            location_type=SceneLocation.INTERIOR,
            location="客厅",
            time_type=SceneTime.DAY,
            time_detail="",
            content='小明走进客厅，看到妈妈在做饭。"妈妈，我回来了！"他高兴地说。背景传来电视新闻的声音。',
        )

        mock_chat_service = Mock()
        mock_chat_service.chat.return_value = """【场景上下文】第 1 场 · 内景 · 客厅 · 日
小明走进客厅，看到妈妈在做饭。

【镜头画面】小明推开门，阳光从窗户洒进来

【镜头参数】景别：中景 | 运镜：推镜

【音效】开门声"""

        mock_template_manager = Mock()
        mock_template = Mock()
        mock_template.build_messages.return_value = [{"role": "user", "content": "test"}]
        mock_template_manager.get_template.return_value = mock_template

        prompt = VideoPromptBuilder.build_shot_prompt(
            storyboard=storyboard,
            scene=scene,
            clean_dialogue_and_sound=True,
            chat_service=mock_chat_service,
            template_manager=mock_template_manager,
        )

        # 验证 chat_service 被调用
        mock_chat_service.chat.assert_called_once()

        # 验证清理后的提示词不包含对话
        self.assertNotIn("妈妈，我回来了", prompt)
        self.assertNotIn("背景传来电视新闻的声音", prompt)

        # 验证保留了其他部分
        self.assertIn("小明走进客厅", prompt)
        self.assertIn("【音效】开门声", prompt)

    def test_clean_prompt_with_continuity_hints(self):
        """测试清理连贯性提示中的对话"""
        storyboard = Storyboard(
            scene_number=1,
            shot_number=2,
            id=2,
            scene_id=1,
            shot_size=ShotSize.CLOSE_UP,
            camera_movement="",
            content="妈妈转过身，微笑着看向小明",
            sound_effect="",
            ambient_sound="",
            background_music="",
            duration=5.0,
            notes="",
            design_image="",
            seed="",
        )

        prev_shot = Storyboard(
            scene_number=1,
            shot_number=1,
            id=1,
            scene_id=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="",
            content='小明站在门外，犹豫地举起手准备敲门。"要不要进去呢？"他自言自语',
            sound_effect="",
            ambient_sound="",
            background_music="",
            duration=5.0,
            notes="",
            design_image="",
            seed="",
        )

        next_shot = Storyboard(
            scene_number=1,
            shot_number=3,
            id=3,
            scene_id=1,
            shot_size=ShotSize.FULL_SHOT,
            camera_movement="",
            content='两人拥抱在一起。厨房里传来炒菜的滋滋声，妈妈说："你终于回来了"',
            sound_effect="",
            ambient_sound="",
            background_music="",
            duration=5.0,
            notes="",
            design_image="",
            seed="",
        )

        mock_chat_service = Mock()
        mock_chat_service.chat.return_value = """【镜头画面】妈妈转过身，微笑着看向小明

【镜头参数】景别：近景

【连贯性提示】前一镜：小明站在门外，犹豫地举起手准备敲门... | 后一镜：两人拥抱在一起..."""

        mock_template_manager = Mock()
        mock_template = Mock()
        mock_template.build_messages.return_value = [{"role": "user", "content": "test"}]
        mock_template_manager.get_template.return_value = mock_template

        prompt = VideoPromptBuilder.build_shot_prompt(
            storyboard=storyboard,
            prev_shot=prev_shot,
            next_shot=next_shot,
            clean_dialogue_and_sound=True,
            chat_service=mock_chat_service,
            template_manager=mock_template_manager,
        )

        # 验证连贯性提示中的对话被移除
        self.assertNotIn("要不要进去呢", prompt)
        self.assertNotIn("你终于回来了", prompt)
        self.assertNotIn("炒菜的滋滋声", prompt)

    def test_clean_prompt_exception_handling(self):
        """测试清理失败时返回原始提示词"""
        storyboard = Storyboard(
            scene_number=1,
            shot_number=1,
            id=1,
            scene_id=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="",
            content="测试内容",
            sound_effect="",
            ambient_sound="",
            background_music="",
            duration=5.0,
            notes="",
            design_image="",
            seed="",
        )

        mock_chat_service = Mock()
        mock_chat_service.chat.side_effect = Exception("API 调用失败")

        mock_template_manager = Mock()
        mock_template = Mock()
        mock_template.build_messages.return_value = [{"role": "user", "content": "test"}]
        mock_template_manager.get_template.return_value = mock_template

        # 应该不抛出异常，而是返回原始提示词
        prompt = VideoPromptBuilder.build_shot_prompt(
            storyboard=storyboard,
            clean_dialogue_and_sound=True,
            chat_service=mock_chat_service,
            template_manager=mock_template_manager,
        )

        # 验证返回了内容（没有因为异常而返回空字符串）
        self.assertIn("测试内容", prompt)


if __name__ == "__main__":
    unittest.main()
