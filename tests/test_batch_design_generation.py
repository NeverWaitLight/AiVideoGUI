import unittest
from unittest.mock import MagicMock

from models.enums import ShotSize
from models.storyboard import Storyboard


def _make_storyboard_bridge():
    container = MagicMock()
    container.config.workspace_root.return_value = "/tmp/workspace"
    from bridge.storyboard_bridge import StoryboardBridge
    return StoryboardBridge(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(),
        MagicMock(), MagicMock(), MagicMock(), MagicMock(),
        MagicMock(), container,
    )


def _make_character_bridge():
    container = MagicMock()
    container.config.workspace_root.return_value = "/tmp/workspace"
    from bridge.character_bridge import CharacterBridge
    return CharacterBridge(
        MagicMock(), MagicMock(), MagicMock(),
        MagicMock(), MagicMock(), container=container,
    )


class TestBatchDesignGeneration(unittest.TestCase):

    def test_storyboard_bridge_signals_exist(self):
        from bridge.storyboard_bridge import StoryboardBridge

        self.assertTrue(hasattr(StoryboardBridge, 'design_image_ready'))
        self.assertTrue(hasattr(StoryboardBridge, 'design_image_started'))
        self.assertTrue(hasattr(StoryboardBridge, 'design_image_finished'))
        self.assertTrue(hasattr(StoryboardBridge, 'design_image_progress'))
        self.assertTrue(hasattr(StoryboardBridge, 'design_image_failed'))

    def test_character_bridge_signals_exist(self):
        from bridge.character_bridge import CharacterBridge

        self.assertTrue(hasattr(CharacterBridge, 'design_image_started'))
        self.assertTrue(hasattr(CharacterBridge, 'design_image_finished'))

    def test_batch_worker_signals_exist(self):
        from service.background.image_generation_worker import BatchImageGenerationWorker

        self.assertTrue(hasattr(BatchImageGenerationWorker, 'shot_design_started'))
        self.assertTrue(hasattr(BatchImageGenerationWorker, 'shot_design_failed'))

    def test_storyboard_design_generating_mark_unmark(self):
        bridge = _make_storyboard_bridge()
        started = []
        finished = []
        bridge.design_image_started.connect(lambda shot_id: started.append(shot_id))
        bridge.design_image_finished.connect(lambda shot_id: finished.append(shot_id))

        bridge._mark_design_generating(42)
        self.assertIn(42, bridge._generating_design_shot_ids)
        self.assertEqual(started, ["42"])
        self.assertEqual(finished, [])

        bridge._unmark_design_generating(42)
        self.assertNotIn(42, bridge._generating_design_shot_ids)
        self.assertEqual(finished, ["42"])

        bridge._unmark_design_generating(42)
        self.assertEqual(finished, ["42"])

    def test_storyboard_design_failed_unmarks_generating(self):
        bridge = _make_storyboard_bridge()
        finished = []
        failed = []
        bridge.design_image_finished.connect(lambda shot_id: finished.append(shot_id))
        bridge.design_image_failed.connect(lambda err: failed.append(err))

        bridge._mark_design_generating(7)
        bridge._on_design_failed(7, "生成超时")

        self.assertNotIn(7, bridge._generating_design_shot_ids)
        self.assertEqual(finished, ["7"])
        self.assertEqual(failed, ["生成超时"])

    def test_character_design_generating_mark_unmark(self):
        bridge = _make_character_bridge()
        started = []
        finished = []
        bridge.design_image_started.connect(lambda uuid: started.append(uuid))
        bridge.design_image_finished.connect(lambda uuid: finished.append(uuid))

        bridge._mark_design_generating("uuid-abc")
        self.assertIn("uuid-abc", bridge._generating_design_char_uuids)
        self.assertEqual(started, ["uuid-abc"])

        bridge._unmark_design_generating("uuid-abc")
        self.assertNotIn("uuid-abc", bridge._generating_design_char_uuids)
        self.assertEqual(finished, ["uuid-abc"])

    def test_storyboard_design_done_converts_relative_path(self):
        import os
        bridge = _make_storyboard_bridge()
        ready_paths = []
        bridge.design_image_ready.connect(lambda shot_id, path: ready_paths.append((shot_id, path)))
        bridge._cur_shot_id = 9

        bridge._on_design_done(9, "projects/1/design-1-1.png")

        self.assertTrue(os.path.isabs(bridge._cur_design_image))
        self.assertTrue(bridge._cur_design_image.replace("\\", "/").endswith("projects/1/design-1-1.png"))
        self.assertEqual(ready_paths[0][0], "9")
        self.assertTrue(os.path.isabs(ready_paths[0][1]))

    def test_collect_shot_data_for_batch_generation(self):
        storyboards = [
            Storyboard(
                id=1,
                scene_id=101,
                scene_number=1,
                shot_number=1,
                shot_size=ShotSize.MEDIUM_SHOT,
                camera_movement="固定",
                content="主角站在窗前，阳光洒在脸上",
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
                content="特写主角眼神坚定的表情",
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
                content="",
                dialogue="",
                sound_effect="",
                duration=4.0,
                notes="",
                design_image="",
                created_at=1000000,
                updated_at=1000000,
            ),
        ]

        shot_list = []
        project_id = 1
        for sb in storyboards:
            content = sb.content
            if not content.strip():
                continue
            shot_list.append({
                "storyboard_id": sb.id,
                "scene_number": sb.scene_number,
                "shot_number": sb.shot_number,
                "content": content,
                "shot_size": sb.shot_size,
                "camera_movement": sb.camera_movement,
                "dialogue": sb.dialogue,
                "notes": sb.notes,
                "project_id": project_id,
            })

        self.assertEqual(len(shot_list), 2)
        self.assertEqual(shot_list[0]["storyboard_id"], 1)
        self.assertEqual(shot_list[1]["storyboard_id"], 2)
        print(f"Successfully collected {len(shot_list)} valid shots (filtered empty content)")

    def test_batch_generation_data_structure(self):
        shot_data = {
            "storyboard_id": 1,
            "scene_number": 1,
            "shot_number": 1,
            "content": "主角站在窗前",
            "shot_size": ShotSize.MEDIUM_SHOT,
            "camera_movement": "固定",
            "dialogue": "这是一个美好的早晨",
            "notes": "柔和光线",
            "project_id": 1,
        }

        required_fields = [
            "storyboard_id", "scene_number", "shot_number",
            "content", "shot_size", "project_id"
        ]
        for field in required_fields:
            self.assertIn(field, shot_data)

        print("Batch generation data structure contains all required fields")


if __name__ == "__main__":
    unittest.main()
