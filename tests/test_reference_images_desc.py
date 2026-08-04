import unittest
from models.storyboard import Storyboard
from models.enums import ShotSize
from prompts.video_prompt_builder import VideoPromptBuilder


class TestReferenceImagesDesc(unittest.TestCase):
    def test_no_reference_images(self):
        """测试不传递参考图片时的情况"""
        shot = Storyboard(
            id=1,
            scene_id=1,
            scene_number=1,
            shot_number=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="固定",
            visual_content="胖橘猫站在厨房里",
            dialogue="",
            sound_effect="",
            duration=5.0,
            notes="",
        )

        prompt = VideoPromptBuilder.build_shot_prompt(shot)

        self.assertNotIn("【参考图片说明】", prompt)
        self.assertIn("【镜头画面】", prompt)

    def test_design_image_only(self):
        """测试只有分镜设计图的情况"""
        shot = Storyboard(
            id=1,
            scene_id=1,
            scene_number=1,
            shot_number=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="固定",
            visual_content="胖橘猫站在厨房里",
            dialogue="",
            sound_effect="",
            duration=5.0,
            notes="",
        )

        reference_images = [
            {"type": "design", "description": ""}
        ]

        prompt = VideoPromptBuilder.build_shot_prompt(shot, reference_images=reference_images)

        self.assertIn("【参考图片说明】", prompt)
        self.assertIn("图1：本镜头的分镜设计图，请参考其构图、机位、光线、色调和整体氛围。", prompt)

    def test_character_image_only(self):
        """测试只有角色设计图的情况"""
        shot = Storyboard(
            id=1,
            scene_id=1,
            scene_number=1,
            shot_number=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="固定",
            visual_content="胖橘猫站在厨房里",
            dialogue="",
            sound_effect="",
            duration=5.0,
            notes="",
        )

        reference_images = [
            {"type": "character", "character_name": "胖橘猫", "description": ""}
        ]

        prompt = VideoPromptBuilder.build_shot_prompt(shot, reference_images=reference_images)

        self.assertIn("【参考图片说明】", prompt)
        self.assertIn("图1：胖橘猫的角色设计图，请严格参考其外观、服装、神态等视觉特征。", prompt)

    def test_multiple_reference_images(self):
        """测试多张参考图片的情况"""
        shot = Storyboard(
            id=1,
            scene_id=1,
            scene_number=1,
            shot_number=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="固定",
            visual_content="胖橘猫站在厨房里",
            dialogue="",
            sound_effect="",
            duration=5.0,
            notes="",
        )

        reference_images = [
            {"type": "design", "description": ""},
            {"type": "character", "character_name": "胖橘猫", "description": ""},
        ]

        prompt = VideoPromptBuilder.build_shot_prompt(shot, reference_images=reference_images)

        self.assertIn("【参考图片说明】", prompt)
        self.assertIn("图1：本镜头的分镜设计图", prompt)
        self.assertIn("图2：胖橘猫的角色设计图", prompt)

    def test_reference_images_order_in_prompt(self):
        """测试参考图片说明在 prompt 中的顺序（应该在场景上下文之后、镜头画面之前）"""
        from models.scene import Scene
        from models.enums import SceneLocation, SceneTime

        scene = Scene(
            id=1,
            project_id=1,
            scene_number=1,
            location_type=SceneLocation.INTERIOR,
            location="厨房",
            time_type=SceneTime.DAY,
            content="胖橘猫在厨房里学习如何喝水。",
        )

        shot = Storyboard(
            id=1,
            scene_id=1,
            scene_number=1,
            shot_number=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="固定",
            visual_content="胖橘猫站在厨房里",
            dialogue="",
            sound_effect="",
            duration=5.0,
            notes="",
        )

        reference_images = [
            {"type": "design", "description": ""}
        ]

        prompt = VideoPromptBuilder.build_shot_prompt(shot, scene=scene, reference_images=reference_images)

        context_index = prompt.find("【场景上下文】")
        ref_index = prompt.find("【参考图片说明】")
        visual_index = prompt.find("【镜头画面】")

        self.assertGreater(ref_index, context_index, "参考图片说明应该在场景上下文之后")
        self.assertLess(ref_index, visual_index, "参考图片说明应该在镜头画面之前")

    def test_empty_reference_images_list(self):
        """测试传递空列表时的情况"""
        shot = Storyboard(
            id=1,
            scene_id=1,
            scene_number=1,
            shot_number=1,
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="固定",
            visual_content="胖橘猫站在厨房里",
            dialogue="",
            sound_effect="",
            duration=5.0,
            notes="",
        )

        prompt = VideoPromptBuilder.build_shot_prompt(shot, reference_images=[])

        self.assertNotIn("【参考图片说明】", prompt)


if __name__ == "__main__":
    unittest.main()
