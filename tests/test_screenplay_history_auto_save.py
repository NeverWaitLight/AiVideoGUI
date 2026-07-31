import os
import tempfile
import time
import unittest

from models.enums import SceneLocation, SceneTime
from models.project import Project
from models.scene import Scene
from storage.orm.base import init_engine, create_all_tables, get_session, close_session
from storage.repositories.project_repository import ProjectRepository
from storage.repositories.screenplay_repository import ScreenplayRepository, ScreenplayHistoryRepository


class TestScreenplayHistoryAutoSave(unittest.TestCase):

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
        from storage.orm.base import engine
        close_session()
        if engine:
            engine.dispose()

        try:
            os.unlink(self.temp_db_path)
        except PermissionError:
            pass

    def _create_project_and_scene(self, content="初始内容"):
        session = get_session()
        project_repo = ProjectRepository(session)
        scene_repo = ScreenplayRepository(session)

        now_ms = int(time.time() * 1000)
        project = Project(
            id=0,
            name="测试项目",
            resolution="720P",
            aspect_ratio="16:9",
            created_at=now_ms,
            updated_at=now_ms,
            cover_image="",
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
            content=content,
            created_at=now_ms,
            updated_at=now_ms,
        )
        scene = scene_repo.create(scene)
        session.commit()

        return project, scene

    def test_auto_save_history_on_insert(self):
        project, scene = self._create_project_and_scene("初始内容")

        session = get_session()
        history_repo = ScreenplayHistoryRepository(session)
        history = history_repo.list_by_project(project.id)

        self.assertEqual(len(history), 1, "创建场次后应自动保存 1 条历史")
        self.assertEqual(history[0].content, "初始内容")
        self.assertEqual(history[0].screenplay_id, scene.id)

    def test_auto_save_history_on_content_update(self):
        project, scene = self._create_project_and_scene("初始内容")

        session = get_session()
        scene_repo = ScreenplayRepository(session)
        history_repo = ScreenplayHistoryRepository(session)

        entity = session.get(scene_repo.entity_class, scene.id)
        entity.content = "修改后的内容"
        entity.updated_at = int(time.time() * 1000)
        session.commit()

        timestamps = history_repo.distinct_timestamps_by_project(project.id)
        self.assertEqual(len(timestamps), 2, "创建+更新后应有 2 条历史记录")

        history = history_repo.list_by_project_and_timestamp(project.id, timestamps[0])
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].content, "修改后的内容")
        self.assertEqual(history[0].screenplay_id, scene.id)
        self.assertEqual(history[0].scene_number, 1)
        self.assertEqual(history[0].location_type, SceneLocation.INTERIOR)
        self.assertEqual(history[0].location, "客厅")

    def test_auto_save_history_on_location_update(self):
        project, scene = self._create_project_and_scene()

        session = get_session()
        scene_repo = ScreenplayRepository(session)
        history_repo = ScreenplayHistoryRepository(session)

        entity = session.get(scene_repo.entity_class, scene.id)
        entity.location = "书房"
        entity.updated_at = int(time.time() * 1000)
        session.commit()

        history = history_repo.list_by_project(project.id)
        self.assertEqual(len(history), 2, "创建+更新后应有 2 条历史记录")
        self.assertEqual(history[0].location, "书房")

    def test_no_history_on_updated_at_only(self):
        project, scene = self._create_project_and_scene()

        session = get_session()
        scene_repo = ScreenplayRepository(session)
        history_repo = ScreenplayHistoryRepository(session)

        entity = session.get(scene_repo.entity_class, scene.id)
        entity.updated_at = int(time.time() * 1000)
        session.commit()

        history = history_repo.list_by_project(project.id)
        self.assertEqual(len(history), 1, "仅更新 updated_at 不应新增历史")

    def test_multiple_updates_accumulate(self):
        project, scene = self._create_project_and_scene("版本1")

        session = get_session()
        scene_repo = ScreenplayRepository(session)
        history_repo = ScreenplayHistoryRepository(session)

        entity = session.get(scene_repo.entity_class, scene.id)
        entity.content = "版本2"
        entity.updated_at = int(time.time() * 1000)
        session.commit()

        entity = session.get(scene_repo.entity_class, scene.id)
        entity.content = "版本3"
        entity.updated_at = int(time.time() * 1000)
        session.commit()

        history = history_repo.list_by_project(project.id)
        self.assertEqual(len(history), 3, "创建+2次更新应有 3 条历史记录")

    def test_history_contains_all_fields(self):
        project, scene = self._create_project_and_scene("原始内容")

        session = get_session()
        scene_repo = ScreenplayRepository(session)
        history_repo = ScreenplayHistoryRepository(session)

        entity = session.get(scene_repo.entity_class, scene.id)
        entity.content = "新内容"
        entity.location = "公园"
        entity.time_type = SceneTime.NIGHT.value
        entity.time_detail = "晚上8点"
        entity.updated_at = int(time.time() * 1000)
        session.commit()

        history = history_repo.list_by_project(project.id)
        self.assertEqual(len(history), 2, "创建+更新后应有 2 条历史记录")
        h = history[0]
        self.assertEqual(h.screenplay_id, scene.id)
        self.assertEqual(h.project_id, project.id)
        self.assertEqual(h.scene_number, 1)
        self.assertEqual(h.location_type, SceneLocation.INTERIOR)
        self.assertEqual(h.location, "公园")
        self.assertEqual(h.time_type, SceneTime.NIGHT)
        self.assertEqual(h.time_detail, "晚上8点")
        self.assertEqual(h.content, "新内容")


if __name__ == "__main__":
    unittest.main()
