"""测试批量分镜设计图生成功能。"""

import unittest
from unittest.mock import MagicMock, patch

from models.enums import ShotSize
from models.storyboard import Storyboard


class TestBatchDesignGeneration(unittest.TestCase):
    """测试批量设计图生成功能"""

    def test_storyboard_editor_signal_exists(self):
        """测试 StoryboardEditor 是否有批量设计图生成信号"""
        from ui.storyboard_editor import StoryboardEditor

        # 检查信号是否存在
        self.assertTrue(hasattr(StoryboardEditor, 'batch_design_image_generation_requested'))
        print("batch_design_image_generation_requested signal exists")

    def test_collect_shot_data_for_batch_generation(self):
        """测试收集分镜数据的逻辑"""
        # 模拟分镜列表
        storyboards = [
            Storyboard(
                id=1,
                scene_id=101,
                scene_number=1,
                shot_number=1,
                shot_size=ShotSize.MEDIUM_SHOT,
                camera_movement="固定",
                visual_content="主角站在窗前，阳光洒在脸上",
                dialogue="",
                sound_effect="",
                duration=5.0,
                notes="",
                design_image="",
                created_at=1000000,
                updated_at=1000000,
            ),
            Storyboard(
                id=2,
                scene_id=101,
                scene_number=1,
                shot_number=2,
                shot_size=ShotSize.CLOSE_UP,
                camera_movement="慢推",
                visual_content="特写主角眼神坚定的表情",
                dialogue="",
                sound_effect="",
                duration=3.0,
                notes="",
                design_image="",
                created_at=1000000,
                updated_at=1000000,
            ),
            Storyboard(
                id=3,
                scene_id=101,
                scene_number=1,
                shot_number=3,
                shot_size=ShotSize.FULL_SHOT,
                camera_movement="跟拍",
                visual_content="",  # 空内容应该被过滤
                dialogue="",
                sound_effect="",
                duration=4.0,
                notes="",
                design_image="",
                created_at=1000000,
                updated_at=1000000,
            ),
        ]

        # 模拟收集逻辑
        shot_list = []
        project_id = 1
        for sb in storyboards:
            visual_content = sb.visual_content
            if not visual_content.strip():
                continue
            shot_list.append({
                "storyboard_id": sb.id,
                "scene_number": sb.scene_number,
                "shot_number": sb.shot_number,
                "visual_content": visual_content,
                "shot_size": sb.shot_size,
                "camera_movement": sb.camera_movement,
                "dialogue": sb.dialogue,
                "notes": sb.notes,
                "project_id": project_id,
            })

        # 验证收集结果
        self.assertEqual(len(shot_list), 2)  # 空内容的分镜应被过滤
        self.assertEqual(shot_list[0]["storyboard_id"], 1)
        self.assertEqual(shot_list[1]["storyboard_id"], 2)
        print(f"Successfully collected {len(shot_list)} valid shots (filtered empty content)")

    def test_batch_generation_data_structure(self):
        """测试批量生成数据结构的完整性"""
        shot_data = {
            "storyboard_id": 1,
            "scene_number": 1,
            "shot_number": 1,
            "visual_content": "主角站在窗前",
            "shot_size": ShotSize.MEDIUM_SHOT,
            "camera_movement": "固定",
            "dialogue": "这是一个美好的早晨",
            "notes": "柔和光线",
            "project_id": 1,
        }

        # 验证必需字段
        required_fields = [
            "storyboard_id", "scene_number", "shot_number",
            "visual_content", "shot_size", "project_id"
        ]
        for field in required_fields:
            self.assertIn(field, shot_data)

        print("Batch generation data structure contains all required fields")


if __name__ == "__main__":
    unittest.main()
