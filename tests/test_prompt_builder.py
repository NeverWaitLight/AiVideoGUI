import unittest
from models.enums import SceneLocation, SceneTime, ShotSize
from models.scene import Scene
from models.storyboard import Storyboard
from prompts.video_prompt_builder import VideoPromptBuilder


class TestVideoPromptBuilder(unittest.TestCase):

    def test_build_shot_prompt_minimal(self):
        storyboard = Storyboard(
            id=1,
            scene_number=1,
            shot_number=1,
            scene_id=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            content="一个男人站在街道上",
            camera_movement="",
            dialogue="",
            sound_effect="",
            duration=5.0,
            notes="",
        )

        prompt = VideoPromptBuilder.build_shot_prompt(storyboard)

        self.assertIn("【镜头画面】", prompt)
        self.assertIn("一个男人站在街道上", prompt)
        self.assertIn("【镜头参数】", prompt)
        self.assertIn("景别：中景", prompt)
        self.assertIn("时长：5.0秒", prompt)
        self.assertNotIn("【台词】", prompt)
        self.assertNotIn("【音效】", prompt)
        self.assertNotIn("【场景上下文】", prompt)

    def test_build_shot_prompt_with_scene_context(self):
        scene = Scene(
            id=1,
            project_id=1,
            scene_number=1,
            location_type=SceneLocation.EXTERIOR,
            location="老城区街道",
            time_type=SceneTime.DAY,
            time_detail="",
            content="张三走在繁华的老城区街道上，街道两旁是各种小店铺，人来人往。",
        )

        storyboard = Storyboard(
            id=1,
            scene_number=1,
            shot_number=1,
            scene_id=1,
            shot_size=ShotSize.FULL_SHOT,
            content="张三从远处走来，背景是繁华的街道",
            camera_movement="跟拍",
            dialogue="",
            sound_effect="",
            duration=8.0,
            notes="",
        )

        prompt = VideoPromptBuilder.build_shot_prompt(storyboard, scene=scene)

        self.assertIn("【场景上下文】", prompt)
        self.assertIn("第 1 场", prompt)
        self.assertIn("外景", prompt)
        self.assertIn("老城区街道", prompt)
        self.assertIn("日", prompt)
        self.assertIn("张三走在繁华的老城区街道上", prompt)
        self.assertIn("【镜头画面】", prompt)
        self.assertIn("张三从远处走来", prompt)
        self.assertIn("运镜：跟拍", prompt)

    def test_build_shot_prompt_with_all_fields(self):
        scene = Scene(
            id=1,
            project_id=1,
            scene_number=2,
            location_type=SceneLocation.INTERIOR,
            location="审讯室",
            time_type=SceneTime.NIGHT,
            time_detail="深夜",
            content="审讯室内灯光昏暗，张三坐在桌子前，警察站在对面。",
        )

        storyboard = Storyboard(
            id=2,
            scene_number=2,
            shot_number=3,
            scene_id=1,
            shot_size=ShotSize.CLOSE_UP,
            content="张三紧张的表情，汗水从额头滴落",
            camera_movement="慢推",
            dialogue="张三：我什么都不知道！",
            sound_effect="紧张的背景音乐",
            duration=4.5,
            notes="注意光影对比",
        )

        prompt = VideoPromptBuilder.build_shot_prompt(storyboard, scene=scene)

        self.assertIn("【场景上下文】", prompt)
        self.assertIn("第 2 场", prompt)
        self.assertIn("内景", prompt)
        self.assertIn("审讯室", prompt)
        self.assertIn("夜", prompt)
        self.assertIn("【镜头画面】", prompt)
        self.assertIn("张三紧张的表情", prompt)
        self.assertIn("【镜头参数】", prompt)
        self.assertIn("景别：近景", prompt)
        self.assertIn("运镜：慢推", prompt)
        self.assertIn("时长：4.5秒", prompt)
        self.assertIn("【台词】", prompt)
        self.assertIn("张三：我什么都不知道！", prompt)
        self.assertIn("【音效】", prompt)
        self.assertIn("紧张的背景音乐", prompt)
        self.assertIn("【备注】", prompt)
        self.assertIn("注意光影对比", prompt)

    def test_build_shot_prompt_with_continuity(self):
        prev_shot = Storyboard(
            id=1,
            scene_number=1,
            shot_number=1,
            scene_id=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            content="张三从远处走来，背景是繁华的街道，人来人往",
            camera_movement="",
            dialogue="",
            sound_effect="",
            duration=5.0,
            notes="",
        )

        current_shot = Storyboard(
            id=2,
            scene_number=1,
            shot_number=2,
            scene_id=1,
            shot_size=ShotSize.CLOSE_UP,
            content="张三的脸部特写，表情严肃",
            camera_movement="",
            dialogue="",
            sound_effect="",
            duration=3.0,
            notes="",
        )

        next_shot = Storyboard(
            id=3,
            scene_number=1,
            shot_number=3,
            scene_id=1,
            shot_size=ShotSize.FULL_SHOT,
            content="张三走进一家咖啡店，推开玻璃门",
            camera_movement="",
            dialogue="",
            sound_effect="",
            duration=4.0,
            notes="",
        )

        prompt = VideoPromptBuilder.build_shot_prompt(
            current_shot, prev_shot=prev_shot, next_shot=next_shot
        )

        self.assertIn("【连贯性提示】", prompt)
        self.assertIn("前一镜：", prompt)
        self.assertIn("张三从远处走来", prompt)
        self.assertIn("后一镜：", prompt)
        self.assertIn("张三走进一家咖啡店", prompt)

    def test_build_shot_prompt_long_content_truncation(self):
        long_scene_content = "这是一段非常长的场景描述。" * 30

        scene = Scene(
            id=1,
            project_id=1,
            scene_number=1,
            location_type=SceneLocation.EXTERIOR,
            location="街道",
            time_type=SceneTime.DAY,
            time_detail="",
            content=long_scene_content,
        )

        long_content = "这是一段非常长的画面描述。" * 10

        prev_shot = Storyboard(
            id=1,
            scene_number=1,
            shot_number=1,
            scene_id=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            content=long_content,
            camera_movement="",
            dialogue="",
            sound_effect="",
            duration=5.0,
            notes="",
        )

        current_shot = Storyboard(
            id=2,
            scene_number=1,
            shot_number=2,
            scene_id=1,
            shot_size=ShotSize.CLOSE_UP,
            content="当前镜头画面",
            camera_movement="",
            dialogue="",
            sound_effect="",
            duration=3.0,
            notes="",
        )

        prompt = VideoPromptBuilder.build_shot_prompt(
            current_shot, scene=scene, prev_shot=prev_shot
        )

        self.assertIn("...", prompt)
        scene_section = prompt.split("【场景上下文】")[1].split("【")[0]
        self.assertLess(len(scene_section), 250)
        if "【连贯性提示】" in prompt:
            continuity_section = prompt.split("【连贯性提示】")[1].split("【")[0] if "【连贯性提示】" in prompt.split("【镜头画面】")[-1] else prompt.split("【连贯性提示】")[1]
            self.assertLess(len(continuity_section), 150)

    def test_build_shot_prompt_with_visual_style(self):
        scene = Scene(
            id=1,
            project_id=1,
            scene_number=1,
            location_type=SceneLocation.EXTERIOR,
            location="公园",
            time_type=SceneTime.DAY,
            time_detail="",
            content="阳光明媚的公园里，人们在散步。",
        )

        storyboard = Storyboard(
            id=1,
            scene_number=1,
            shot_number=1,
            scene_id=1,
            shot_size=ShotSize.FULL_SHOT,
            content="孩子们在草地上奔跑",
            camera_movement="",
            dialogue="",
            sound_effect="",
            duration=5.0,
            notes="",
        )

        prompt = VideoPromptBuilder.build_shot_prompt(
            storyboard, scene=scene, visual_style="写实主义"
        )

        self.assertIn("【场景上下文】", prompt)
        self.assertIn("【视觉风格】", prompt)
        self.assertIn("写实主义", prompt)
        self.assertIn("【镜头画面】", prompt)

        sections = prompt.split("【")
        scene_idx = next(i for i, s in enumerate(sections) if "场景上下文" in s)
        style_idx = next(i for i, s in enumerate(sections) if "视觉风格" in s)
        shot_idx = next(i for i, s in enumerate(sections) if "镜头画面" in s)

        self.assertLess(scene_idx, style_idx)
        self.assertLess(style_idx, shot_idx)

    def test_build_shot_prompt_without_visual_style(self):
        storyboard = Storyboard(
            id=1,
            scene_number=1,
            shot_number=1,
            scene_id=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            content="一个男人站在街道上",
            camera_movement="",
            dialogue="",
            sound_effect="",
            duration=5.0,
            notes="",
        )

        prompt = VideoPromptBuilder.build_shot_prompt(storyboard, visual_style=None)

        self.assertNotIn("【视觉风格】", prompt)
        self.assertIn("【镜头画面】", prompt)


if __name__ == "__main__":
    unittest.main()
