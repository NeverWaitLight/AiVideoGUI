"""测试 Screenplay 历史版本自动保存功能。"""

import os
import tempfile
import time
import unittest

from models.data_models import Scene, SceneLocation, SceneTime
from storage.database import DatabaseManager


class TestScreenplayHistoryAutoSave(unittest.TestCase):
    """测试 Screenplay 场次创建/更新时自动保存历史版本。"""

    def setUp(self):
        """创建临时数据库。"""
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        import storage.orm.base as orm_base
        orm_base.engine = None
        orm_base.SessionLocal = None

        self.db = DatabaseManager(self.temp_db_path)

    def tearDown(self):
        """删除临时数据库。"""
        from storage.orm.base import close_session, engine
        close_session()
        if engine:
            engine.dispose()

        try:
            os.unlink(self.temp_db_path)
        except PermissionError:
            pass

    def _create_project_and_scene(self, content="初始内容"):
        """辅助方法：创建项目和场次。"""
        project = self.db.create_project(
            name="测试项目",
            resolution="720P",
            aspect_ratio="16:9",
        )
        now_ms = int(time.time() * 1000)
        scene = self.db.create_scene(Scene(
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
        ))
        return project, scene

    def test_auto_save_history_on_insert(self):
        """测试创建场次时自动保存初始快照。"""
        project, scene = self._create_project_and_scene("初始内容")

        history = self.db.list_screenplay_history(project.id)
        self.assertEqual(len(history), 1, "创建场次后应自动保存 1 条历史")
        self.assertEqual(history[0].content, "初始内容")
        self.assertEqual(history[0].screenplay_id, scene.id)

    def test_auto_save_history_on_content_update(self):
        """测试更新场次 content 时自动保存历史。"""
        project, scene = self._create_project_and_scene("初始内容")

        self.db.update_scene(scene.id, content="修改后的内容")

        timestamps = self.db.list_screenplay_history_timestamps(project.id)
        self.assertEqual(len(timestamps), 2, "创建+更新后应有 2 条历史记录")

        history = self.db.list_screenplay_history_by_timestamp(project.id, timestamps[0])
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].content, "修改后的内容")
        self.assertEqual(history[0].screenplay_id, scene.id)
        self.assertEqual(history[0].scene_number, 1)
        self.assertEqual(history[0].location_type, SceneLocation.INTERIOR)
        self.assertEqual(history[0].location, "客厅")

    def test_auto_save_history_on_location_update(self):
        """测试更新场次地点时自动保存历史。"""
        project, scene = self._create_project_and_scene()

        self.db.update_scene(scene.id, location="书房")

        history = self.db.list_screenplay_history(project.id)
        self.assertEqual(len(history), 2, "创建+更新后应有 2 条历史记录")
        self.assertEqual(history[0].location, "书房")

    def test_no_history_on_updated_at_only(self):
        """测试仅更新 updated_at 时不保存历史。"""
        project, scene = self._create_project_and_scene()

        # 创建时已有 1 条历史（after_insert）
        self.db.update_scene(scene.id)

        history = self.db.list_screenplay_history(project.id)
        self.assertEqual(len(history), 1, "仅更新 updated_at 不应新增历史")

    def test_multiple_updates_accumulate(self):
        """测试多次更新累积历史记录。"""
        project, scene = self._create_project_and_scene("版本1")

        self.db.update_scene(scene.id, content="版本2")
        self.db.update_scene(scene.id, content="版本3")

        history = self.db.list_screenplay_history(project.id)
        self.assertEqual(len(history), 3, "创建+2次更新应有 3 条历史记录")

    def test_history_contains_all_fields(self):
        """测试历史记录包含与 screenplay 表一致的所有字段。"""
        project, scene = self._create_project_and_scene("原始内容")

        self.db.update_scene(scene.id, content="新内容", location="公园",
                             time_type=SceneTime.NIGHT.value, time_detail="晚上8点")

        history = self.db.list_screenplay_history(project.id)
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
