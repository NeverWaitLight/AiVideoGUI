import unittest

from bridge.storyboard_bridge import StoryboardBridge
from models.character import Character
from models.enums import ShotSize
from models.storyboard import Storyboard


def _make_storyboard(**kwargs) -> Storyboard:
    defaults = {
        "id": 1,
        "scene_id": 101,
        "scene_number": 1,
        "shot_number": 1,
        "shot_size": ShotSize.MEDIUM_SHOT,
        "camera_movement": "固定",
        "content": "李明站在窗前",
        "sound_effect": "",
        "ambient_sound": "",
        "background_music": "",
        "duration": 5.0,
        "notes": "",
        "design_image": "projects/1/storyboard-design.png",
        "created_at": 1000000,
        "updated_at": 1000000,
    }
    defaults.update(kwargs)
    return Storyboard(**defaults)


def _make_character(**kwargs) -> Character:
    defaults = {
        "id": 1,
        "uuid": "char-uuid-1",
        "project_id": 1,
        "name": "李明",
        "ref_code": "CHAR_A",
        "design_image": "projects/1/char-design.png",
        "description": "",
        "created_at": 1000000,
        "updated_at": 1000000,
    }
    defaults.update(kwargs)
    return Character(**defaults)


class TestBuildShotReferenceImages(unittest.TestCase):
    WORKSPACE = "/tmp/workspace"

    def test_both_enabled_includes_storyboard_and_character(self):
        shot = _make_storyboard()
        characters = [_make_character()]

        paths, info = StoryboardBridge._build_shot_reference_images(
            shot, characters, self.WORKSPACE,
            use_storyboard_design=True,
            use_character_design=True,
        )

        self.assertEqual(len(paths), 2)
        self.assertEqual(len(info), 2)
        self.assertEqual(info[0]["type"], "design")
        self.assertEqual(info[1]["type"], "character")
        self.assertEqual(info[1]["character_name"], "李明")
        self.assertIn("storyboard-design.png", paths[0])
        self.assertIn("char-design.png", paths[1])

    def test_storyboard_only(self):
        shot = _make_storyboard()
        characters = [_make_character()]

        paths, info = StoryboardBridge._build_shot_reference_images(
            shot, characters, self.WORKSPACE,
            use_storyboard_design=True,
            use_character_design=False,
        )

        self.assertEqual(len(paths), 1)
        self.assertEqual(info[0]["type"], "design")

    def test_character_only(self):
        shot = _make_storyboard()
        characters = [_make_character()]

        paths, info = StoryboardBridge._build_shot_reference_images(
            shot, characters, self.WORKSPACE,
            use_storyboard_design=False,
            use_character_design=True,
        )

        self.assertEqual(len(paths), 1)
        self.assertEqual(info[0]["type"], "character")
        self.assertEqual(info[0]["character_name"], "李明")

    def test_both_disabled_returns_empty(self):
        shot = _make_storyboard()
        characters = [_make_character()]

        paths, info = StoryboardBridge._build_shot_reference_images(
            shot, characters, self.WORKSPACE,
            use_storyboard_design=False,
            use_character_design=False,
        )

        self.assertEqual(paths, [])
        self.assertEqual(info, [])

    def test_character_not_in_content_not_included(self):
        shot = _make_storyboard(content="一个空镜头")
        characters = [_make_character()]

        paths, info = StoryboardBridge._build_shot_reference_images(
            shot, characters, self.WORKSPACE,
            use_storyboard_design=False,
            use_character_design=True,
        )

        self.assertEqual(paths, [])
        self.assertEqual(info, [])

    def test_batch_generate_videos_slot_accepts_reference_flags(self):
        import inspect
        from bridge.storyboard_bridge import StoryboardBridge

        sig = inspect.signature(StoryboardBridge.batch_generate_videos)
        self.assertIn("use_storyboard_design", sig.parameters)
        self.assertIn("use_character_design", sig.parameters)
        self.assertTrue(sig.parameters["use_storyboard_design"].default)
        self.assertTrue(sig.parameters["use_character_design"].default)

    def test_collect_video_generate_preview_includes_thumbnails_data(self):
        shot = _make_storyboard()
        characters = [_make_character()]
        preview = StoryboardBridge._collect_video_generate_preview(
            [shot], characters, self.WORKSPACE,
        )

        self.assertEqual(len(preview["storyboardDesigns"]), 1)
        self.assertEqual(preview["storyboardDesigns"][0]["label"], "1场1镜")
        self.assertIn("storyboard-design.png", preview["storyboardDesigns"][0]["imagePath"])
        self.assertEqual(len(preview["characterDesigns"]), 1)
        self.assertEqual(preview["characterDesigns"][0]["characterName"], "李明")
        self.assertIn("char-design.png", preview["characterDesigns"][0]["imagePath"])

    def test_collect_video_generate_preview_deduplicates_characters(self):
        shot1 = _make_storyboard(id=1, shot_number=1)
        shot2 = _make_storyboard(id=2, shot_number=2, content="李明看向窗外")
        characters = [_make_character()]

        preview = StoryboardBridge._collect_video_generate_preview(
            [shot1, shot2], characters, self.WORKSPACE,
        )

        self.assertEqual(len(preview["storyboardDesigns"]), 2)
        self.assertEqual(len(preview["characterDesigns"]), 1)


if __name__ == "__main__":
    unittest.main()
