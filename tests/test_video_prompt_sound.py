"""测试视频 Prompt 构建器的声音字段整合"""

import unittest
from models.storyboard import Storyboard
from models.scene import Scene
from models.enums import ShotSize, SceneLocation, SceneTime
from prompts.video_prompt_builder import VideoPromptBuilder


class TestVideoPromptSound(unittest.TestCase):
    def test_build_prompt_with_all_sound_fields(self):
        """测试 Prompt 构建器能够整合所有声音字段"""
        shot = Storyboard(
            scene_number=1,
            shot_number=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="固定镜头",
            content="测试画面描述",
            sound_effect="他低声说：'我们不能再装作一切没变。'",
            ambient_sound="远处传来模糊的街道车流声，室内安静",
            background_music="低沉的大提琴旋律，压抑而沉重",
            duration=7.0,
            notes="暖色调"
        )

        scene = Scene(
            id=1,
            project_id=1,
            scene_number=1,
            location_type=SceneLocation.INTERIOR,
            location="餐厅",
            time_type=SceneTime.DAY,
            content="一对夫妇在餐厅对话"
        )

        prompt = VideoPromptBuilder.build_shot_prompt(shot, scene)

        # 验证所有声音字段都出现在 Prompt 中
        self.assertIn("【音效】", prompt)
        self.assertIn("他低声说：'我们不能再装作一切没变。'", prompt)

        self.assertIn("【环境音】", prompt)
        self.assertIn("远处传来模糊的街道车流声，室内安静", prompt)

        self.assertIn("【背景音乐】", prompt)
        self.assertIn("低沉的大提琴旋律，压抑而沉重", prompt)

    def test_build_prompt_with_empty_sound_fields(self):
        """测试 Prompt 构建器能够处理空的声音字段"""
        shot = Storyboard(
            scene_number=1,
            shot_number=1,
            shot_size=ShotSize.CLOSE_UP,
            camera_movement="固定镜头",
            content="测试画面描述",
            sound_effect="",
            ambient_sound="",
            background_music="",
            duration=5.0,
            notes=""
        )

        prompt = VideoPromptBuilder.build_shot_prompt(shot)

        # 验证空字段不会出现在 Prompt 中
        self.assertNotIn("【音效】", prompt)
        self.assertNotIn("【环境音】", prompt)
        self.assertNotIn("【背景音乐】", prompt)

    def test_build_prompt_with_partial_sound_fields(self):
        """测试 Prompt 构建器能够处理部分声音字段"""
        shot = Storyboard(
            scene_number=1,
            shot_number=1,
            shot_size=ShotSize.FULL_SHOT,
            camera_movement="固定镜头",
            content="测试画面描述",
            sound_effect="脚步声，清脆的敲击声",
            ambient_sound="",
            background_music="柔和的木吉他音乐",
            duration=6.0,
            notes=""
        )

        prompt = VideoPromptBuilder.build_shot_prompt(shot)

        # 验证非空字段出现，空字段不出现
        self.assertIn("【音效】", prompt)
        self.assertIn("脚步声，清脆的敲击声", prompt)

        self.assertNotIn("【环境音】", prompt)

        self.assertIn("【背景音乐】", prompt)
        self.assertIn("柔和的木吉他音乐", prompt)

    def test_sound_fields_order_in_prompt(self):
        """测试声音字段在 Prompt 中的顺序"""
        shot = Storyboard(
            scene_number=1,
            shot_number=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="固定镜头",
            content="测试画面描述",
            sound_effect="测试音效",
            ambient_sound="测试环境音",
            background_music="测试背景音乐",
            duration=5.0,
            notes="测试备注"
        )

        prompt = VideoPromptBuilder.build_shot_prompt(shot)

        # 验证字段顺序：音效 → 环境音 → 背景音乐
        sound_effect_pos = prompt.find("【音效】")
        ambient_sound_pos = prompt.find("【环境音】")
        background_music_pos = prompt.find("【背景音乐】")

        self.assertGreater(ambient_sound_pos, sound_effect_pos)
        self.assertGreater(background_music_pos, ambient_sound_pos)


if __name__ == "__main__":
    unittest.main()
