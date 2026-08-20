import os
import tempfile
import unittest

from models.character import Character
from models.enums import ShotSize
from models.storyboard import Storyboard


class TestDesignImageRevision(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.workspace_root = self._tmpdir.name

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_storyboard_update_design_image_increments_revision(self):
        from bridge.models.storyboard_model import StoryboardListModel

        model = StoryboardListModel(workspace_root=self.workspace_root)
        model.reset([
            Storyboard(
                id=1,
                scene_id=101,
                scene_number=1,
                shot_number=1,
                content="test",
            ),
        ])

        idx = model.index(0)
        self.assertEqual(model.data(idx, model.DesignImageRevisionRole), 0)

        image_path = os.path.join(self.workspace_root, "projects", "1", "design-1-1.png")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "w", encoding="utf-8") as f:
            f.write("v1")

        model.update_design_image(1, image_path)
        self.assertEqual(model.data(idx, model.DesignImageRevisionRole), 1)
        actual_path = os.path.normpath(model.data(idx, model.DesignImageRole)).replace("\\", "/")
        expected_path = os.path.normpath(image_path).replace("\\", "/")
        self.assertEqual(actual_path, expected_path)

        model.update_design_image(1, image_path)
        self.assertEqual(model.data(idx, model.DesignImageRevisionRole), 2)

    def test_storyboard_reset_clears_revision(self):
        from bridge.models.storyboard_model import StoryboardListModel

        model = StoryboardListModel(workspace_root=self.workspace_root)
        shot = Storyboard(id=1, scene_id=101, scene_number=1, shot_number=1, content="test")
        model.reset([shot])

        image_path = os.path.join(self.workspace_root, "projects", "1", "design-1-1.png")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "w", encoding="utf-8") as f:
            f.write("v1")
        model.update_design_image(1, image_path)

        model.reset([shot])
        idx = model.index(0)
        self.assertEqual(model.data(idx, model.DesignImageRevisionRole), 0)

    def test_character_update_design_image_increments_revision(self):
        from bridge.models.character_model import CharacterListModel

        model = CharacterListModel(workspace_root=self.workspace_root)
        model.reset([
            Character(
                id=1,
                uuid="uuid-1",
                project_id=1,
                name="角色A",
                ref_code="A01",
                description="描述",
            ),
        ])

        idx = model.index(0)
        self.assertEqual(model.data(idx, model.DesignImageRevisionRole), 0)

        image_path = os.path.join(self.workspace_root, "projects", "1", "char-uuid-1.png")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "w", encoding="utf-8") as f:
            f.write("v1")

        model.update_design_image("uuid-1", image_path)
        self.assertEqual(model.data(idx, model.DesignImageRevisionRole), 1)

        model.update_design_image("uuid-1", image_path)
        self.assertEqual(model.data(idx, model.DesignImageRevisionRole), 2)


if __name__ == "__main__":
    unittest.main()
