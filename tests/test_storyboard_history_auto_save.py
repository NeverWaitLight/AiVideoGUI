import os
import tempfile
import time
import unittest

from models.enums import SceneLocation, SceneTime, ShotSize
from models.scene import Scene
from models.project import Project
from models.storyboard import Storyboard
from storage.orm.base import init_engine, create_all_tables, get_session, close_session
from storage.repositories.project_repository import ProjectRepository
from storage.repositories.screenplay_repository import ScreenplayRepository
from storage.repositories.storyboard_repository import StoryboardRepository, StoryboardHistoryRepository


class TestStoryboardHistoryAutoSave(unittest.TestCase):

    def setUp(self):
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        import storage.orm.base as orm_base
        orm_base.engine = None
        orm_base.SessionLocal = None

        database_url = f"sqlite:///{self.temp_db_path}"
        init_engine(database_url, echo=False)
        create_all_tables()

    def tearDown(self):
        from storage.orm.base import close_session, engine
        close_session()
        if engine:
            engine.dispose()

        try:
            os.unlink(self.temp_db_path)
        except PermissionError:
            pass

    def _create_project_and_scene(self):
        session = get_session()
        project_repo = ProjectRepository(session)
        screenplay_repo = ScreenplayRepository(session)

        now_ms = int(time.time() * 1000)
        project = Project(
            id=0,
            name="测试项目",
            resolution="720P",
            aspect_ratio="16:9",
            created_at=now_ms,
            updated_at=now_ms,
            cover_image=""
        )
        project = project_repo.create(project)
        session.commit()

        scene = Scene(
            id=0,
            project_id=project.id,
            scene_number=1,
            location_type=SceneLocation.INTERIOR,
            location="客厅",
            time_type=SceneTime.DAY,
            time_detail="下午",
            content="测试场次",
            created_at=now_ms,
            updated_at=now_ms,
        )
        scene = screenplay_repo.create(scene)
        session.commit()

        return project, scene

    def _make_storyboard(self, scene_id, scene_number=1, shot_number=1,
                         visual_content="画面内容"):
        now_ms = int(time.time() * 1000)
        return Storyboard(
            id=0,
            scene_id=scene_id,
            scene_number=scene_number,
            shot_number=shot_number,
            design_image="",
            shot_size=ShotSize.MEDIUM_SHOT,
            camera_movement="pan",
            visual_content=visual_content,
            dialogue="台词",
            sound_effect="",
            duration=5.0,
            notes="",
            created_at=now_ms,
            updated_at=now_ms,
        )

    def test_auto_save_history_on_insert(self):
        project, scene = self._create_project_and_scene()

        session = get_session()
        storyboard_repo = StoryboardRepository(session)
        history_repo = StoryboardHistoryRepository(session)

        sb = storyboard_repo.create(self._make_storyboard(scene.id))
        session.commit()

        history = history_repo.list_by_project(project.id)
        self.assertEqual(len(history), 1, "创建分镜后应自动保存 1 条历史")
        self.assertEqual(history[0].storyboard_id, sb.id)
        self.assertEqual(history[0].visual_content, "画面内容")
        self.assertEqual(history[0].project_id, project.id)

    def test_auto_save_history_on_update(self):
        project, scene = self._create_project_and_scene()

        session = get_session()
        storyboard_repo = StoryboardRepository(session)
        history_repo = StoryboardHistoryRepository(session)

        sb = storyboard_repo.create(self._make_storyboard(scene.id))
        session.commit()

        entity = session.get(storyboard_repo.entity_class, sb.id)
        entity.visual_content = "修改后的画面"
        entity.updated_at = int(time.time() * 1000)
        session.commit()

        history = history_repo.list_by_project(project.id)
        self.assertEqual(len(history), 2, "创建+更新后应有 2 条历史")
        self.assertEqual(history[0].visual_content, "修改后的画面")

    def test_no_history_on_updated_at_only(self):
        project, scene = self._create_project_and_scene()

        session = get_session()
        storyboard_repo = StoryboardRepository(session)
        history_repo = StoryboardHistoryRepository(session)

        sb = storyboard_repo.create(self._make_storyboard(scene.id))
        session.commit()

        entity = session.get(storyboard_repo.entity_class, sb.id)
        entity.updated_at = int(time.time() * 1000)
        session.commit()

        history = history_repo.list_by_project(project.id)
        self.assertEqual(len(history), 1, "仅 updated_at 变化不应新增历史")

    def test_batch_create_saves_history(self):
        project, scene = self._create_project_and_scene()

        session = get_session()
        storyboard_repo = StoryboardRepository(session)
        history_repo = StoryboardHistoryRepository(session)

        storyboards = [
            self._make_storyboard(scene.id, shot_number=1, visual_content="镜头1"),
            self._make_storyboard(scene.id, shot_number=2, visual_content="镜头2"),
            self._make_storyboard(scene.id, shot_number=3, visual_content="镜头3"),
        ]

        for sb in storyboards:
            storyboard_repo.create(sb)
        session.commit()

        history = history_repo.list_by_project(project.id)
        self.assertEqual(len(history), 3, "批量创建 3 条分镜应各保存 1 条历史")

    def test_history_contains_all_fields(self):
        project, scene = self._create_project_and_scene()

        session = get_session()
        storyboard_repo = StoryboardRepository(session)
        history_repo = StoryboardHistoryRepository(session)

        now_ms = int(time.time() * 1000)
        sb_dto = Storyboard(
            id=0,
            scene_id=scene.id, scene_number=1, shot_number=1,
            design_image="img.png", shot_size=ShotSize.CLOSE_UP,
            camera_movement="dolly", visual_content="特写画面",
            dialogue="重要台词", sound_effect="风声",
            duration=8.5, notes="注意光影", created_at=now_ms, updated_at=now_ms,
        )
        sb = storyboard_repo.create(sb_dto)
        session.commit()

        history = history_repo.list_by_project(project.id)
        self.assertEqual(len(history), 1)
        h = history[0]
        self.assertEqual(h.storyboard_id, sb.id)
        self.assertEqual(h.project_id, project.id)
        self.assertEqual(h.scene_id, scene.id)
        self.assertEqual(h.scene_number, 1)
        self.assertEqual(h.shot_number, 1)
        self.assertEqual(h.design_image, "img.png")
        self.assertEqual(h.shot_size, ShotSize.CLOSE_UP)
        self.assertEqual(h.camera_movement, "dolly")
        self.assertEqual(h.visual_content, "特写画面")
        self.assertEqual(h.dialogue, "重要台词")
        self.assertEqual(h.sound_effect, "风声")
        self.assertEqual(h.duration, 8.5)
        self.assertEqual(h.notes, "注意光影")

    def test_multiple_updates_accumulate(self):
        project, scene = self._create_project_and_scene()

        session = get_session()
        storyboard_repo = StoryboardRepository(session)
        history_repo = StoryboardHistoryRepository(session)

        sb = storyboard_repo.create(self._make_storyboard(scene.id))
        session.commit()

        entity = session.get(storyboard_repo.entity_class, sb.id)
        entity.visual_content = "版本2"
        entity.updated_at = int(time.time() * 1000)
        session.commit()

        entity = session.get(storyboard_repo.entity_class, sb.id)
        entity.visual_content = "版本3"
        entity.updated_at = int(time.time() * 1000)
        session.commit()

        history = history_repo.list_by_project(project.id)
        self.assertEqual(len(history), 3, "创建+2次更新应有 3 条历史")


if __name__ == "__main__":
    unittest.main()
